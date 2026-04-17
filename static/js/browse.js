const API_BASE = '';

let tagTree = {};
let allTags = [];
let questions = [];
let selectedTags = new Set();
let selectedQuestions = new Set();
let expandedTags = new Set();
let currentQuestion = null;
let debounceTimer = null;

let questionItems = [];
let answerItems = [];
let currentTab = 'question';
let itemCounter = 0;
let tags = [];
let currentView = 'edit';
let subQuestions = [];
let currentEditingQuestion = null;
let activeSubQuestionId = null;
let activeMainPaste = null;

let currentPage = 1;
let totalPages = 1;
let totalQuestions = 0;
let pageSize = 50;
let currentSearch = '';

function getCurrentItems(target) {
    if (target === 'question') return questionItems;
    if (target === 'answer') return answerItems;
    return currentTab === 'question' ? questionItems : answerItems;
}

function setCurrentItems(items, target) {
    if (target === 'question') {
        questionItems = items;
    } else if (target === 'answer') {
        answerItems = items;
    } else {
        if (currentTab === 'question') {
            questionItems = items;
        } else {
            answerItems = items;
        }
    }
}

function getCurrentContentList(target) {
    if (target === 'question') return document.getElementById('question-content-list');
    if (target === 'answer') return document.getElementById('answer-content-list');
    return currentTab === 'question'
        ? document.getElementById('question-content-list')
        : document.getElementById('answer-content-list');
}

function activateMainPaste(type) {
    activeMainPaste = type;
    activeSubQuestionId = null;
    updateMainPasteButtons();
    updateSubQuestionPasteButtons();
}

function updateMainPasteButtons() {
    const questionBtn = document.getElementById('question-paste-btn');
    const answerBtn = document.getElementById('answer-paste-btn');
    if (questionBtn) {
        questionBtn.classList.toggle('active', activeMainPaste === 'question');
    }
    if (answerBtn) {
        answerBtn.classList.toggle('active', activeMainPaste === 'answer');
    }
}

function updateSubQuestionPasteButtons() {
    subQuestions.forEach(sq => {
        const btn = document.getElementById(`sq-paste-btn-${sq.id}`);
        if (btn) {
            btn.classList.toggle('active', activeSubQuestionId === sq.id);
        }
    });
}

function setupEditTabs() {
    document.querySelectorAll('#edit-view .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#edit-view .tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('#edit-view .tab-content').forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const tabName = tab.dataset.tab;
            if (tabName) {
                document.getElementById(`${tabName}-tab`).classList.add('active');
                currentTab = tabName;
                renderContentList();
            }
        });
    });
}

function handleHtmlPaste(html, plainText, target) {
    if (!plainText.trim()) return;

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    let fragments = [];

    function processNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            if (node.textContent) {
                fragments.push({ text: node.textContent, underline: false });
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            const style = node.getAttribute('style') || '';
            const tagName = node.tagName.toLowerCase();

            let isUnderline = false;

            if (style.includes('text-decoration') && style.includes('underline')) {
                isUnderline = true;
            }
            if (tagName === 'u') {
                isUnderline = true;
            }

            if (tagName === 'br') {
                fragments.push({ text: '\n', underline: false });
                return;
            }

            if (tagName === 'p') {
                if (fragments.length > 0 && !fragments[fragments.length - 1].text.endsWith('\n')) {
                    fragments.push({ text: '\n', underline: false });
                }
            }

            const startIndex = fragments.length;

            for (const child of node.childNodes) {
                processNode(child);
            }

            if (isUnderline) {
                for (let i = startIndex; i < fragments.length; i++) {
                    fragments[i].underline = true;
                }
            }

            if (tagName === 'p' && fragments.length > 0 && !fragments[fragments.length - 1].text.endsWith('\n')) {
                fragments.push({ text: '\n', underline: false });
            }
        }
    }

    processNode(doc.body);

    let merged = [];
    for (const frag of fragments) {
        if (merged.length > 0 && merged[merged.length - 1].underline === frag.underline) {
            merged[merged.length - 1].text += frag.text;
        } else {
            merged.push({ text: frag.text, underline: frag.underline });
        }
    }

    if (merged.length > 0) {
        merged[0].text = merged[0].text.replace(/^\n+/, '');
        merged[merged.length - 1].text = merged[merged.length - 1].text.replace(/\n+$/, '');
    }

    const items = getCurrentItems(target);
    const newItem = {
        id: ++itemCounter,
        type: 'richtext',
        content: plainText,
        fragments: merged
    };
    items.push(newItem);
    setCurrentItems(items, target);

    const contentList = getCurrentContentList(target);
    renderContentList(contentList, items, target);
    renderPreview();
}

function handleTextPaste(text, target) {
    if (!text.trim()) return;

    text = text.replace(/^\n+|\n+$/g, '');

    const items = getCurrentItems(target);
    const newItem = {
        id: ++itemCounter,
        type: 'text',
        content: text
    };
    items.push(newItem);
    setCurrentItems(items, target);

    const contentList = getCurrentContentList(target);
    renderContentList(contentList, items, target);
    renderPreview();
}

async function handleImagePaste(file, target) {
    if (!file) return;

    try {
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64 = e.target.result;

            const result = await API.uploadImage(base64);

            if (result.success) {
                const items = getCurrentItems(target);
                const newItem = {
                    id: ++itemCounter,
                    type: 'image',
                    image_id: result.image_id,
                    config_id: null,
                    src: result.path,
                    display: 'center',
                    width: 300,
                    height: 'auto',
                    base64: base64
                };
                items.push(newItem);
                setCurrentItems(items, target);

                const contentList = getCurrentContentList(target);
                renderContentList(contentList, items, target);
                renderPreview();
            } else {
                alert('图片上传失败: ' + result.error);
            }
        };
        reader.readAsDataURL(file);
    } catch (error) {
        alert('图片上传失败: ' + error.message);
    }
}

function renderContentList(contentListOrTarget, itemsOrUndefined, targetOrUndefined) {
    let contentList, items, target;
    if (typeof contentListOrTarget === 'string' || contentListOrTarget === undefined) {
        target = contentListOrTarget || currentTab;
        contentList = getCurrentContentList(target);
        items = getCurrentItems(target);
    } else {
        contentList = contentListOrTarget;
        items = itemsOrUndefined;
        target = targetOrUndefined;
    }

    const addTextBtn = contentList.querySelector('.add-text-btn');
    contentList.innerHTML = '';

    items.forEach((item, index) => {
        if (item.type === 'text' || item.type === 'richtext') {
            const div = document.createElement('div');
            div.className = 'text-item';
            const content = item.type === 'richtext' ? Utils.renderRichtext(item.fragments) : Utils.escapeHtml(item.content);
            div.innerHTML = `
                <div class="text-item-content" ondblclick="doEditText(this, ${index}, '${target}')">${content}</div>
                <button class="delete-btn" onclick="deleteItem(${index}, '${target}')">删除</button>
            `;
            contentList.appendChild(div);
        } else if (item.type === 'image') {
            const div = document.createElement('div');
            div.className = 'image-card';
            const imgSrc = item.base64 || (item.src && !item.src.startsWith('http') ? '/' + item.src : item.src);
            const hasCharBox = item.charBox ? true : false;
            div.innerHTML = `
                <img src="${imgSrc}" class="image-preview" alt="图片">
                <div class="image-controls">
                    <label>显示方式:</label>
                    <select onchange="updateImageDisplay(${index}, this.value, '${target}')">
                        <option value="center" ${item.display === 'center' ? 'selected' : ''}>居中显示</option>
                        <option value="float-left" ${item.display === 'float-left' ? 'selected' : ''}>文字环绕(左)</option>
                        <option value="float-right" ${item.display === 'float-right' ? 'selected' : ''}>文字环绕(右)</option>
                    </select>
                    <label>宽度:</label>
                    <input type="number" value="${item.width || 300}" onchange="updateImageSize(${index}, 'width', this.value, '${target}')">
                    <label>高度:</label>
                    <input type="number" value="${item.height === 'auto' ? '' : item.height}" onchange="updateImageSize(${index}, 'height', this.value, '${target}')" placeholder="自动">
                    <button class="char-box-btn-annotate ${hasCharBox ? 'has-box' : ''}" onclick="openCharBoxModal('${currentQuestion?.id}', ${index}, '${target}')">${hasCharBox ? '已标注' : '标注字框'}</button>
                    <button class="delete-btn" onclick="deleteItem(${index}, '${target}')">删除</button>
                </div>
            `;
            contentList.appendChild(div);
        }
    });

    if (addTextBtn) {
        contentList.appendChild(addTextBtn);
    }
}

function addTextItem(target = currentTab) {
    const items = getCurrentItems(target);
    const newItem = {
        id: ++itemCounter,
        type: 'text',
        content: ''
    };
    items.push(newItem);
    const newIndex = items.length - 1;
    setCurrentItems(items, target);
    renderContentList(target);
    renderPreview();

    const contentList = getCurrentContentList(target);
    const textElements = contentList.querySelectorAll('.text-item');
    const lastTextElement = textElements[textElements.length - 1];
    if (lastTextElement) {
        const textContent = lastTextElement.querySelector('.text-item-content');
        if (textContent) {
            setTimeout(() => {
                doEditText(textContent, newIndex, target);
            }, 10);
        }
    }
}

function doEditText(element, index, target = currentTab) {
    const items = getCurrentItems(target);
    const item = items[index];
    if (!item) return;

    const currentContent = item.content || '';
    element.contentEditable = 'true';
    element.classList.add('editing');

    element.addEventListener('blur', function onBlur() {
        const newContent = element.textContent;
        items[index].content = newContent;
        setCurrentItems(items, target);
        element.contentEditable = 'false';
        element.classList.remove('editing');
        element.removeEventListener('blur', onBlur);
        element.removeEventListener('keydown', onKeydown);
        renderPreview();
    });

    element.addEventListener('keydown', function onKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            element.blur();
        }
        if (e.key === 'Escape') {
            e.preventDefault();
            element.textContent = currentContent;
            element.blur();
        }
    });

    element.focus();
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(element);
    selection.removeAllRanges();
    selection.addRange(range);
}

function deleteItem(index, target = currentTab) {
    const items = getCurrentItems(target);
    items.splice(index, 1);
    setCurrentItems(items, target);
    renderContentList(target);
    renderPreview();
}

function updateImageDisplay(index, display, target = currentTab) {
    const items = getCurrentItems(target);
    items[index].display = display;
    setCurrentItems(items, target);
    renderPreview();
}

function updateImageSize(index, dimension, value, target = currentTab) {
    const items = getCurrentItems(target);
    if (dimension === 'height' && !value) {
        items[index][dimension] = 'auto';
    } else {
        items[index][dimension] = parseInt(value) || 300;
    }
    setCurrentItems(items, target);
    renderPreview();
}

function renderTags() {
    const container = document.getElementById('tag-container');
    const input = document.getElementById('tag-input');

    container.innerHTML = '';

    tags.forEach((tag, index) => {
        const tagEl = document.createElement('span');
        tagEl.className = 'tag-item';
        tagEl.innerHTML = `${tag}<span class="tag-remove" onclick="removeTag(${index})">×</span>`;
        container.appendChild(tagEl);
    });

    container.appendChild(input);
}

function addTag(tag) {
    tag = tag.trim();
    if (tag && !tags.includes(tag)) {
        tags.push(tag);
        renderTags();
    }
}

function removeTag(index) {
    tags.splice(index, 1);
    renderTags();
}

function addSubQuestion() {
    const id = Date.now();
    subQuestions.push({
        id: id,
        title: `第${subQuestions.length + 1}小问`,
        question_text: { items: [] },
        tags: []
    });
    renderSubQuestions();
}

function removeSubQuestion(id) {
    subQuestions = subQuestions.filter(sq => sq.id !== id);
    renderSubQuestions();
}

function updateSubQuestionTitle(id, title) {
    const sq = subQuestions.find(s => s.id === id);
    if (sq) {
        sq.title = title;
    }
}

function addSubQuestionTag(id, tag) {
    tag = tag.trim();
    const sq = subQuestions.find(s => s.id === id);
    if (sq && tag && !sq.tags.includes(tag)) {
        sq.tags.push(tag);
        renderSubQuestions();
    }
}

function removeSubQuestionTag(id, tagIndex) {
    const sq = subQuestions.find(s => s.id === id);
    if (sq) {
        sq.tags.splice(tagIndex, 1);
        renderSubQuestions();
    }
}

function renderSubQuestions() {
    const container = document.getElementById('subQuestionsList');

    if (!subQuestions || subQuestions.length === 0) {
        container.innerHTML = '<div style="color: #999; font-size: 12px; text-align: center; padding: 10px;">暂无小问，点击上方按钮添加</div>';
        return;
    }

    container.innerHTML = '';

    subQuestions.forEach(sq => {
        const card = document.createElement('div');
        card.className = 'sub-question-card';

        card.innerHTML = `
            <div class="sub-question-card-header">
                <div class="sub-question-card-title">
                    <input type="text" value="${Utils.escapeHtml(sq.title)}" onchange="updateSubQuestionTitle(${sq.id}, this.value)">
                </div>
                <button class="sub-question-remove-btn" onclick="removeSubQuestion(${sq.id})">删除</button>
            </div>
            <div class="sub-question-card-content">
                <button class="sub-question-paste-btn ${activeSubQuestionId === sq.id ? 'active' : ''}" id="sq-paste-btn-${sq.id}" onclick="activateSubQuestionPaste(${sq.id})">
                    📋 点击此处粘贴内容
                </button>
                <div class="sub-question-content-list" id="sq-content-list-${sq.id}">
                    ${renderSubQuestionContentItems(sq)}
                </div>
                <div class="sub-question-tags" id="sq-tags-${sq.id}">
                    ${(sq.tags || []).map((tag, idx) => `
                        <span class="tag-item">${Utils.escapeHtml(tag)}<span class="tag-remove" onclick="removeSubQuestionTag(${sq.id}, ${idx})">×</span></span>
                    `).join('')}
                    <input type="text" placeholder="输入标签后回车" onkeydown="handleSubQuestionTagInput(${sq.id}, event)">
                    <div class="sub-question-quick-tags">
                        <button class="quick-tag-btn" onclick="addSubQuestionTag(${sq.id}, '思维')">思维</button>
                        <button class="quick-tag-btn" onclick="addSubQuestionTag(${sq.id}, '积累')">积累</button>
                        <button class="quick-tag-btn" onclick="addSubQuestionTag(${sq.id}, '重要')">重要</button>
                        <button class="quick-tag-btn" onclick="addSubQuestionTag(${sq.id}, '必考')">必考</button>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderSubQuestionContentItems(sq) {
    const items = sq.question_text?.items || [];
    if (items.length === 0) return '';

    return items.map((item, idx) => {
        if (item.type === 'text' || item.type === 'richtext') {
            const content = item.type === 'richtext' ? renderRichtext(item.fragments) : escapeHtml(item.content);
            return `<div class="text-item">
                <div class="text-item-content">${content}</div>
                <button class="delete-btn" onclick="removeSubQuestionContent(${sq.id}, ${idx})">删除</button>
            </div>`;
        } else if (item.type === 'image') {
            const imgSrc = item.base64 || (item.src && !item.src.startsWith('http') ? '/' + item.src : item.src);
            return `<div class="image-card">
                <img src="${imgSrc}" class="image-preview" alt="图片">
                <div class="image-controls">
                    <label>显示方式:</label>
                    <select onchange="updateSubQuestionImageDisplay(${sq.id}, ${idx}, this.value)">
                        <option value="center" ${item.display === 'center' ? 'selected' : ''}>居中显示</option>
                        <option value="float-left" ${item.display === 'float-left' ? 'selected' : ''}>文字环绕(左)</option>
                        <option value="float-right" ${item.display === 'float-right' ? 'selected' : ''}>文字环绕(右)</option>
                    </select>
                    <label>宽度:</label>
                    <input type="number" value="${item.width || 300}" onchange="updateSubQuestionImageSize(${sq.id}, ${idx}, 'width', this.value)">
                    <label>高度:</label>
                    <input type="number" value="${item.height === 'auto' ? '' : item.height}" onchange="updateSubQuestionImageSize(${sq.id}, ${idx}, 'height', this.value)" placeholder="自动">
                    <button class="delete-btn" onclick="removeSubQuestionContent(${sq.id}, ${idx})">删除</button>
                </div>
            </div>`;
        }
        return '';
    }).join('');
}

function updateSubQuestionImageDisplay(sqId, itemIndex, display) {
    const sq = subQuestions.find(s => s.id === sqId);
    if (sq && sq.question_text && sq.question_text.items && sq.question_text.items[itemIndex]) {
        sq.question_text.items[itemIndex].display = display;
        renderSubQuestions();
    }
}

function updateSubQuestionImageSize(sqId, itemIndex, dimension, value) {
    const sq = subQuestions.find(s => s.id === sqId);
    if (sq && sq.question_text && sq.question_text.items && sq.question_text.items[itemIndex]) {
        if (dimension === 'height' && !value) {
            sq.question_text.items[itemIndex][dimension] = 'auto';
        } else {
            sq.question_text.items[itemIndex][dimension] = parseInt(value) || 300;
        }
        renderSubQuestions();
    }
}

function activateSubQuestionPaste(id) {
    activeSubQuestionId = id;
    activeMainPaste = null;
    updateMainPasteButtons();
    renderSubQuestions();
}

function handleSubQuestionHtmlPaste(html, plainText, sqId) {
    if (!plainText.trim()) return;

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    let fragments = [];

    function processNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            if (node.textContent) {
                fragments.push({ text: node.textContent, underline: false });
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            const style = node.getAttribute('style') || '';
            const tagName = node.tagName.toLowerCase();

            let isUnderline = false;

            if (style.includes('text-decoration') && style.includes('underline')) {
                isUnderline = true;
            }
            if (tagName === 'u') {
                isUnderline = true;
            }

            if (tagName === 'br') {
                fragments.push({ text: '\n', underline: false });
                return;
            }

            if (tagName === 'p') {
                if (fragments.length > 0 && !fragments[fragments.length - 1].text.endsWith('\n')) {
                    fragments.push({ text: '\n', underline: false });
                }
            }

            const startIndex = fragments.length;

            for (const child of node.childNodes) {
                processNode(child);
            }

            if (isUnderline) {
                for (let i = startIndex; i < fragments.length; i++) {
                    fragments[i].underline = true;
                }
            }

            if (tagName === 'p' && fragments.length > 0 && !fragments[fragments.length - 1].text.endsWith('\n')) {
                fragments.push({ text: '\n', underline: false });
            }
        }
    }

    processNode(doc.body);

    const merged = [];
    for (const frag of fragments) {
        if (merged.length > 0 && merged[merged.length - 1].underline === frag.underline) {
            merged[merged.length - 1].text += frag.text;
        } else {
            merged.push({ text: frag.text, underline: frag.underline });
        }
    }

    const sq = subQuestions.find(s => s.id === sqId);
    if (sq) {
        if (!sq.question_text) sq.question_text = { items: [] };
        sq.question_text.items.push({
            id: Date.now(),
            type: 'richtext',
            content: plainText,
            fragments: merged
        });
        renderSubQuestions();
    }
}

function handleSubQuestionTextPaste(text, sqId) {
    if (!text.trim()) return;

    const sq = subQuestions.find(s => s.id === sqId);
    if (sq) {
        if (!sq.question_text) sq.question_text = { items: [] };
        sq.question_text.items.push({
            id: Date.now(),
            type: 'text',
            content: text
        });
        renderSubQuestions();
    }
}

async function handleSubQuestionImagePaste(file, sqId) {
    if (!file) return;

    try {
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64 = e.target.result;

            const response = await fetch(`${API_BASE}/api/upload-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: base64 })
            });

            const result = await response.json();

            if (result.success) {
                const sq = subQuestions.find(s => s.id === sqId);
                if (sq) {
                    if (!sq.question_text) sq.question_text = { items: [] };
                    sq.question_text.items.push({
                        id: Date.now(),
                        type: 'image',
                        image_id: result.image_id,
                        config_id: null,
                        src: result.path,
                        display: 'center',
                        width: 300,
                        height: 'auto',
                        base64: base64
                    });
                    renderSubQuestions();
                }
            }
        };
        reader.readAsDataURL(file);
    } catch (error) {
        console.error('图片上传失败:', error);
    }
}

function removeSubQuestionContent(sqId, contentIndex) {
    const sq = subQuestions.find(s => s.id === sqId);
    if (sq && sq.question_text && sq.question_text.items) {
        sq.question_text.items.splice(contentIndex, 1);
        renderSubQuestions();
    }
}

function handleSubQuestionTagInput(id, event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const input = event.target;
        addSubQuestionTag(id, input.value);
        input.value = '';
    }
}

function renderItemsPreview(items) {
    if (!items || items.length === 0) {
        return '<div style="color: #999; font-style: italic;">暂无内容</div>';
    }

    let html = '';

    items.forEach(item => {
        if (item.type === 'text') {
            const processed = Utils.processTextWithLatex(item.content);
            html += `<span class="preview-text">${processed}</span>`;
        } else if (item.type === 'richtext') {
            html += `<span class="preview-text">${Utils.renderRichtext(item.fragments)}</span>`;
        } else if (item.type === 'image') {
            let imgClass = 'preview-image-center';
            if (item.display === 'float-left') {
                imgClass = 'preview-image-float-left';
            } else if (item.display === 'float-right') {
                imgClass = 'preview-image-float-right';
            }
            const heightStyle = item.height === 'auto' ? 'auto' : `${item.height}px`;
            const imgSrc = item.base64 || (item.src && !item.src.startsWith('http') ? '/' + item.src : item.src);
            html += `<img src="${imgSrc}" class="${imgClass}" style="width: ${item.width}px; height: ${heightStyle};" alt="图片">`;
        }
    });

    return html;
}

function renderPreview() {
    if (currentView === 'preview') {
        const container = document.getElementById('questionPreview');
        container.innerHTML = `
            <div class="preview-content">
                <div class="preview-section">
                    <div class="preview-section-title">【原题】</div>
                    <div class="preview-content-inner">${renderItemsPreview(questionItems)}</div>
                </div>
                <div class="divider"></div>
                <div class="preview-section">
                    <div class="preview-section-title">【答案】</div>
                    <div class="preview-content-inner">${renderItemsPreview(answerItems)}</div>
                </div>
            </div>
        `;
    }
}

function switchView(view) {
    currentView = view;
    document.getElementById('edit-tab-btn').classList.toggle('active', view === 'edit');
    document.getElementById('preview-tab-btn').classList.toggle('active', view === 'preview');
    document.getElementById('edit-view').classList.toggle('active', view === 'edit');
    document.getElementById('preview-view').classList.toggle('active', view === 'preview');

    if (view === 'preview') {
        renderPreview();
    }
}

async function loadTags() {
    try {
        const response = await fetch(`${API_BASE}/api/tags`);
        const result = await response.json();
        if (result.success) {
            tagTree = result.tag_tree;
            allTags = result.all_tags;
            renderTagTree();
        }
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

function renderTagTree() {
    const container = document.getElementById('tagTree');
    container.innerHTML = renderTreeNode(tagTree, '');
}

function renderTreeNode(tree, prefix) {
    let html = '';
    for (const [tag, value] of Object.entries(tree)) {
        const fullTag = prefix ? `${prefix}::${tag}` : tag;
        const hasChildren = value && value.children && Object.keys(value.children).length > 0;
        const isExpanded = expandedTags.has(fullTag);
        const isSelected = selectedTags.has(fullTag);

        html += `<div class="tag-tree-item">`;
        html += `<div class="tag-tree-content ${isSelected ? 'selected' : ''}" data-tag="${fullTag}">`;

        if (hasChildren) {
            html += `<span class="tag-tree-toggle" onclick="toggleTagExpand('${fullTag}')">${isExpanded ? '▼' : '▶'}</span>`;
        } else {
            html += `<span class="tag-tree-toggle hidden"></span>`;
        }

        html += `<input type="checkbox" class="tag-tree-checkbox" ${isSelected ? 'checked' : ''} onclick="toggleTagSelection('${fullTag}')">`;
        html += `<span class="tag-tree-label">${Utils.escapeHtml(tag)}</span>`;
        html += `</div>`;

        if (hasChildren) {
            html += `<div class="tag-tree-children ${isExpanded ? 'expanded' : ''}">`;
            html += renderTreeNode(value.children, fullTag);
            html += `</div>`;
        }

        html += `</div>`;
    }
    return html;
}

function toggleTagExpand(tag) {
    if (expandedTags.has(tag)) {
        expandedTags.delete(tag);
    } else {
        expandedTags.add(tag);
    }
    renderTagTree();
}

function toggleTagSelection(tag) {
    if (selectedTags.has(tag)) {
        selectedTags.delete(tag);
    } else {
        selectedTags.add(tag);
    }
    renderTagTree();
    updateSearchFromTags();
    applyFilters();
}

function updateSearchFromTags() {
    const searchInput = document.getElementById('searchInput');

    let newValue = '';
    if (selectedTags.size > 0) {
        newValue = Array.from(selectedTags).map(t => `tag:${t}`).join(' ');
    }

    searchInput.value = newValue;
}

function clearTagSelection() {
    selectedTags.clear();
    renderTagTree();
    updateSearchFromTags();
    applyFilters();
}

async function loadQuestions() {
    await applyFilters();
}

async function applyFilters() {
    try {
        currentSearch = document.getElementById('searchInput').value;
        currentPage = 1;

        let url = `${API_BASE}/api/questions?page=${currentPage}&page_size=${pageSize}`;
        if (currentSearch.trim()) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }

        const response = await fetch(url);
        const result = await response.json();
        questions = result.questions || [];
        totalQuestions = result.total || 0;
        totalPages = result.total_pages || 1;

        renderQuestionList();
        renderPagination();
    } catch (error) {
        console.error('加载错题失败:', error);
    }
}

function renderPagination() {
    const container = document.getElementById('paginationContainer');
    if (!container) return;

    let html = `<span class="pagination-info">共 ${totalQuestions} 题，第 ${currentPage}/${totalPages} 页</span>`;

    if (totalPages > 1) {
        html += '<div class="pagination-controls">';
        html += `<button class="pagination-btn" onclick="goToPage(1)" ${currentPage === 1 ? 'disabled' : ''}>首页</button>`;
        html += `<button class="pagination-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>`;

        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
        }

        html += `<button class="pagination-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>`;
        html += `<button class="pagination-btn" onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>末页</button>`;
        html += '</div>';
    }

    container.innerHTML = html;
}

async function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;

    try {
        let url = `${API_BASE}/api/questions?page=${currentPage}&page_size=${pageSize}`;
        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }

        const response = await fetch(url);
        const result = await response.json();
        questions = result.questions || [];
        totalQuestions = result.total || 0;
        totalPages = result.total_pages || 1;

        renderQuestionList();
        renderPagination();
    } catch (error) {
        console.error('加载错题失败:', error);
    }
}

function debounceApplyFilters() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(applyFilters, 300);
}

function renderQuestionList() {
    const container = document.getElementById('questionList');

    if (questions.length === 0) {
        container.innerHTML = '<div class="preview-placeholder">没有找到错题</div>';
        return;
    }

    container.innerHTML = questions.map(q => {
        let preview = '';
        for (const item of q.question?.items || []) {
            if (item.type === 'text' || item.type === 'richtext') {
                preview = item.content;
                break;
            }
        }
        if (!preview && q.answer?.items?.length > 0) {
            for (const item of q.answer.items) {
                if (item.type === 'text' || item.type === 'richtext') {
                    preview = item.content;
                    break;
                }
            }
        }

        const isSelected = selectedQuestions.has(q.id);
        const hasAiContent = q.question_analysis || q.thinking_processes || q.neural_reaction || q.immersion_thinking || q.math_thinking_chain;

        return `
            <div class="question-item ${isSelected ? 'selected' : ''}"
                 data-id="${q.id}"
                 onclick="selectQuestion(event, '${q.id}')"
                 oncontextmenu="showContextMenu(event, '${q.id}')">
                <div class="question-item-header">
                    <input type="checkbox" class="question-checkbox" ${isSelected ? 'checked' : ''} onclick="toggleQuestionSelection(event, '${q.id}')">
                    <span class="question-item-id">#${q.id}</span>
                    ${hasAiContent ? '<span class="ai-badge" title="包含AI分析内容">AI</span>' : ''}
                    <span class="question-item-date">${q.created_at || ''}</span>
                </div>
                <div class="question-item-preview">${Utils.escapeHtml(preview || '(暂无文本内容)')}</div>
                <div class="question-item-tags">
                    ${(q.tags || []).map(t => `<span class="question-tag">${Utils.escapeHtml(t)}</span>`).join('')}
                </div>
            </div>
        `;
    }).join('');

    updateSelectionInfo();
}

function toggleQuestionSelection(event, id) {
    event.stopPropagation();
    if (selectedQuestions.has(id)) {
        selectedQuestions.delete(id);
    } else {
        selectedQuestions.add(id);
    }
    renderQuestionList();
}

function selectAllWithAiContent() {
    hideContextMenu();
    questions.forEach(q => {
        if (q.question_analysis || q.thinking_processes || q.neural_reaction || q.immersion_thinking || q.math_thinking_chain) {
            selectedQuestions.add(q.id);
        }
    });
    renderQuestionList();
}

function selectQuestion(event, id) {
    if (event.ctrlKey || event.metaKey) {
        if (selectedQuestions.has(id)) {
            selectedQuestions.delete(id);
        } else {
            selectedQuestions.add(id);
        }
    } else {
        selectedQuestions.clear();
        selectedQuestions.add(id);
    }

    renderQuestionList();
    loadQuestionForEdit(id);
}

function loadQuestionForEdit(id, preserveTab = false) {
    const question = questions.find(q => q.id === id);
    if (!question) return;

    const previousTab = currentTab;
    currentQuestion = question;
    currentEditingQuestion = question;

    questionItems = JSON.parse(JSON.stringify(question.question?.items || []));
    answerItems = JSON.parse(JSON.stringify(question.answer?.items || []));
    tags = JSON.parse(JSON.stringify(question.tags || []));
    subQuestions = JSON.parse(JSON.stringify(question.sub_questions || []));
    itemCounter = questionItems.length + answerItems.length;

    questionItems.forEach(item => {
        if (item.type === 'image' && item.src && !item.base64) {
            item.base64 = item.src.startsWith('http') ? item.src : '/' + item.src;
        }
    });
    answerItems.forEach(item => {
        if (item.type === 'image' && item.src && !item.base64) {
            item.base64 = item.src.startsWith('http') ? item.src : '/' + item.src;
        }
    });

    if (!preserveTab) {
        currentTab = 'question';
        document.querySelectorAll('#edit-view .tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('#edit-view .tab-content').forEach(c => c.classList.remove('active'));
        document.querySelector('#edit-view [data-tab="question"]').classList.add('active');
        document.getElementById('question-tab').classList.add('active');
    } else {
        currentTab = previousTab;
    }

    renderContentList();
    renderTags();
    renderSubQuestions();

    if (currentView === 'preview') {
        renderPreview();
    }
}

function toggleSelectAll() {
    if (selectedQuestions.size === questions.length) {
        selectedQuestions.clear();
    } else {
        selectedQuestions.clear();
        questions.forEach(q => selectedQuestions.add(q.id));
    }
    renderQuestionList();
}

function updateSelectionInfo() {
    const info = document.getElementById('selectionInfo');
    const count = document.getElementById('selectedCount');

    if (selectedQuestions.size > 0) {
        info.style.display = 'block';
        count.textContent = selectedQuestions.size;
    } else {
        info.style.display = 'none';
    }
}

function showContextMenu(event, id) {
    event.preventDefault();

    if (!selectedQuestions.has(id)) {
        selectedQuestions.clear();
        selectedQuestions.add(id);
        renderQuestionList();
    }

    const menu = document.getElementById('contextMenu');
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';
    menu.classList.add('show');
}

function hideContextMenu() {
    document.getElementById('contextMenu').classList.remove('show');
}

async function batchAddTag() {
    hideContextMenu();
    if (selectedQuestions.size === 0) {
        alert('请先选择要操作的错题');
        return;
    }

    document.getElementById('modalOverlay').classList.add('show');
    document.getElementById('tagInput').value = '';
    document.getElementById('tagInput').focus();
}

async function confirmAddTag() {
    const tag = document.getElementById('tagInput').value.trim();
    if (!tag) {
        alert('请输入标签名称');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/questions/batch-add-tag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                record_ids: Array.from(selectedQuestions),
                tag: tag
            })
        });

        const result = await response.json();
        if (result.success) {
            alert('标签添加成功');
            closeModal();
            loadTags();
            loadQuestions();
        } else {
            alert('操作失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

function batchPrint() {
    hideContextMenu();
    if (selectedQuestions.size === 0) {
        alert('请先选择要打印的错题');
        return;
    }

    const ids = Array.from(selectedQuestions).join(',');
    window.open(`/print.html?ids=${ids}`, '_blank');
}

async function batchDelete() {
    hideContextMenu();
    if (selectedQuestions.size === 0) {
        alert('请先选择要操作的错题');
        return;
    }

    if (!confirm(`确定要删除选中的 ${selectedQuestions.size} 道错题吗？此操作不可恢复！`)) {
        return;
    }

    try {
        let successCount = 0;
        for (const id of Array.from(selectedQuestions)) {
            const response = await fetch(`${API_BASE}/api/questions/${id}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                successCount++;
            }
        }

        alert(`成功删除 ${successCount} 道错题`);
        selectedQuestions.clear();
        loadTags();
        loadQuestions();
        resetEditArea();
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

async function batchRemoveAiContent() {
    hideContextMenu();
    if (selectedQuestions.size === 0) {
        alert('请先选择要操作的错题');
        return;
    }

    if (!confirm(`确定要删除选中的 ${selectedQuestions.size} 道错题的AI分析内容吗？`)) {
        return;
    }

    try {
        let successCount = 0;
        for (const id of Array.from(selectedQuestions)) {
            const question = questions.find(q => q.id === id);
            if (!question) continue;

            const hasAiContent = question.question_analysis || question.thinking_processes || question.neural_reaction || question.immersion_thinking || question.math_thinking_chain;
            if (!hasAiContent) continue;

            const cleanItems = (items) => {
                return items.map(item => {
                    if (item.type === 'image') {
                        const result = {
                            type: 'image',
                            src: item.src,
                            display: item.display,
                            width: item.width,
                            height: item.height
                        };
                        if (item.image_id) {
                            result.image_id = item.image_id;
                        }
                        if (item.config_id) {
                            result.config_id = item.config_id;
                        }
                        if (item.charBox) {
                            result.charBox = item.charBox;
                        }
                        if (item.splitLines && item.splitLines.length > 0) {
                            result.splitLines = item.splitLines;
                        }
                        return result;
                    } else if (item.type === 'richtext') {
                        return {
                            type: 'richtext',
                            content: item.content,
                            fragments: item.fragments
                        };
                    }
                    return { ...item };
                });
            };

            const cleanSubQuestions = () => {
                return (question.sub_questions || []).map(sq => ({
                    id: sq.id,
                    title: sq.title,
                    question_text: {
                        items: cleanItems(sq.question_text?.items || [])
                    },
                    tags: [...(sq.tags || [])]
                }));
            };

            const data = {
                id: id,
                question: {
                    items: cleanItems(question.question?.items || [])
                },
                answer: {
                    items: cleanItems(question.answer?.items || [])
                },
                tags: question.tags || [],
                sub_questions: cleanSubQuestions()
            };

            const response = await fetch(`${API_BASE}/api/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                successCount++;
                const idx = questions.findIndex(q => q.id === id);
                if (idx !== -1) {
                    questions[idx] = { ...questions[idx], ...data, question_analysis: undefined, thinking_processes: undefined, neural_reaction: undefined, immersion_thinking: undefined, math_thinking_chain: undefined };
                }
            }
        }

        alert(`成功删除 ${successCount} 道错题的AI分析内容`);
        renderQuestionList();
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

async function deleteCurrentQuestion() {
    if (!currentQuestion) {
        alert('请先选择要删除的错题');
        return;
    }

    if (!confirm('确定要删除这道错题吗？此操作不可恢复！')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/questions/${currentQuestion.id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('删除成功');
            selectedQuestions.delete(currentQuestion.id);
            loadTags();
            loadQuestions();
            resetEditArea();
        } else {
            alert('删除失败');
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

async function saveCurrentQuestion() {
    if (!currentQuestion) {
        alert('请先选择要保存的错题');
        return;
    }

    const cleanItems = (items) => {
        return items.map(item => {
            if (item.type === 'image') {
                const result = {
                    type: 'image',
                    src: item.src,
                    display: item.display,
                    width: item.width,
                    height: item.height
                };
                if (item.image_id) {
                    result.image_id = item.image_id;
                }
                if (item.config_id) {
                    result.config_id = item.config_id;
                }
                if (item.charBox) {
                    result.charBox = item.charBox;
                }
                if (item.splitLines && item.splitLines.length > 0) {
                    result.splitLines = item.splitLines;
                }
                return result;
            } else if (item.type === 'richtext') {
                return {
                    type: 'richtext',
                    content: item.content,
                    fragments: item.fragments
                };
            }
            return { ...item };
        });
    };

    const cleanSubQuestions = () => {
        return subQuestions.map(sq => ({
            id: sq.id,
            title: sq.title,
            question_text: {
                items: cleanItems(sq.question_text?.items || [])
            },
            tags: [...(sq.tags || [])]
        }));
    };

    const data = {
        id: currentQuestion.id,
        question: {
            items: cleanItems(questionItems)
        },
        answer: {
            items: cleanItems(answerItems)
        },
        tags: tags,
        sub_questions: cleanSubQuestions()
    };

    try {
        const response = await fetch(`${API_BASE}/api/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('保存成功！');
            loadQuestions();
            loadTags();
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

function resetEditArea() {
    currentQuestion = null;
    questionItems = [];
    answerItems = [];
    tags = [];
    itemCounter = 0;

    renderContentList();
    renderTags();

    document.getElementById('questionPreview').innerHTML = '<div class="preview-placeholder">点击左侧错题查看详情</div>';
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('show');
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.context-menu')) {
        hideContextMenu();
    }
    if (!e.target.closest('.modal') && !e.target.closest('.context-menu-item')) {
        closeModal();
    }
});

document.getElementById('tag-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        const input = e.target;
        addTag(input.value);
        input.value = '';
    }
});

document.getElementById('tagInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        confirmAddTag();
    }
});

setupEditTabs();

document.addEventListener('paste', (e) => {
    if (activeSubQuestionId !== null) {
        e.preventDefault();
        const sqId = activeSubQuestionId;

        const items = e.clipboardData.items;

        for (let item of items) {
            if (item.type.startsWith('image/')) {
                const file = item.getAsFile();
                handleSubQuestionImagePaste(file, sqId);
                return;
            }
        }

        const html = e.clipboardData.getData('text/html');
        const text = e.clipboardData.getData('text');
        if (html) {
            handleSubQuestionHtmlPaste(html, text, sqId);
        } else if (text) {
            handleSubQuestionTextPaste(text, sqId);
        }
        return;
    }

    if (activeMainPaste !== null) {
        e.preventDefault();

        const items = e.clipboardData.items;

        for (let item of items) {
            if (item.type.startsWith('image/')) {
                const file = item.getAsFile();
                handleImagePaste(file, activeMainPaste);
                return;
            }
        }

        const html = e.clipboardData.getData('text/html');
        const text = e.clipboardData.getData('text');
        if (html) {
            handleHtmlPaste(html, text, activeMainPaste);
        } else if (text) {
            handleTextPaste(text, activeMainPaste);
        }
        return;
    }

    const activeElement = document.activeElement;
    if (activeElement.classList.contains('paste-zone')) {
        return;
    }

    const items = e.clipboardData.items;

    for (let item of items) {
        if (item.type.startsWith('image/')) {
            e.preventDefault();
            const file = item.getAsFile();
            handleImagePaste(file, 'question');
            return;
        }
    }

    const html = e.clipboardData.getData('text/html');
    const text = e.clipboardData.getData('text');
    if (html) {
        e.preventDefault();
        handleHtmlPaste(html, text, 'question');
    } else if (text) {
        e.preventDefault();
        handleTextPaste(text, 'question');
    }
});

loadTags();
loadQuestions();

let charBoxModalData = {
    questionId: null,
    itemIndex: null,
    itemType: null,
    isDrawing: false,
    startX: 0,
    startY: 0,
    currentBox: null,
    imageWidth: 0,
    imageHeight: 0,
    mode: 'charbox',
    splitLines: []
};

function openCharBoxModal(questionId, itemIndex, itemType) {
    const question = questions.find(q => q.id === questionId);
    if (!question) return;

    let items;
    if (itemType === 'question') {
        items = question.question?.items || [];
    } else if (itemType === 'answer') {
        items = question.answer?.items || [];
    } else {
        return;
    }

    const item = items[itemIndex];
    if (!item || item.type !== 'image') return;

    charBoxModalData.questionId = questionId;
    charBoxModalData.itemIndex = itemIndex;
    charBoxModalData.itemType = itemType;
    charBoxModalData.currentBox = item.charBox ? { ...item.charBox } : null;
    charBoxModalData.splitLines = item.splitLines ? [...item.splitLines] : [];
    charBoxModalData.mode = 'charbox';

    const modal = document.getElementById('charBoxModal');
    const img = document.getElementById('charBoxImage');
    const imgSrc = item.src && !item.src.startsWith('http') ? '/' + item.src : item.src;

    img.onload = function() {
        charBoxModalData.imageWidth = img.naturalWidth;
        charBoxModalData.imageHeight = img.naturalHeight;

        switchCharBoxMode('charbox');
        document.querySelectorAll('.char-box-mode-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.mode === 'charbox');
        });

        if (charBoxModalData.currentBox) {
            drawCharBox(charBoxModalData.currentBox);
            document.getElementById('charBoxFontSize').value = charBoxModalData.currentBox.fontSize || 'medium';
        }
    };
    img.src = imgSrc;

    modal.style.display = 'flex';
}

function switchCharBoxMode(mode) {
    charBoxModalData.mode = mode;
    document.querySelectorAll('.char-box-mode-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === mode);
    });

    const container = document.getElementById('charBoxImageContainer');
    container.classList.toggle('split-mode', mode === 'splitline');

    const hint = document.getElementById('charBoxHint');

    if (mode === 'splitline') {
        clearCharBoxOverlay();
        renderSplitLines();
        hint.textContent = '右键点击图片添加分割线，左键点击分割线删除';
    } else {
        clearSplitLines();
        hint.textContent = '在图片上拖动鼠标绘制一个正方形，代表一个汉字的大小';
        if (charBoxModalData.currentBox) {
            drawCharBox(charBoxModalData.currentBox);
        }
    }
}

function renderSplitLines() {
    const overlay = document.getElementById('charBoxOverlay');
    const img = document.getElementById('charBoxImage');
    const displayHeight = img.clientHeight;

    charBoxModalData.splitLines.forEach((line, index) => {
        const lineEl = document.createElement('div');
        lineEl.className = 'char-box-split-line';
        lineEl.style.top = (line * displayHeight) + 'px';
        lineEl.dataset.index = index;
        lineEl.onclick = function(e) {
            e.stopPropagation();
            deleteSplitLine(index);
        };
        overlay.appendChild(lineEl);
    });
}

function clearSplitLines() {
    const overlay = document.getElementById('charBoxOverlay');
    overlay.querySelectorAll('.char-box-split-line').forEach(el => el.remove());
}

function addSplitLine(yRatio) {
    const newLine = Math.round(yRatio * 1000) / 1000;
    if (!charBoxModalData.splitLines.includes(newLine)) {
        charBoxModalData.splitLines.push(newLine);
        charBoxModalData.splitLines.sort((a, b) => a - b);
        clearSplitLines();
        renderSplitLines();
    }
}

function deleteSplitLine(index) {
    charBoxModalData.splitLines.splice(index, 1);
    clearSplitLines();
    renderSplitLines();
}

function closeCharBoxModal() {
    const modal = document.getElementById('charBoxModal');
    modal.style.display = 'none';
    clearCharBoxOverlay();
    clearSplitLines();
    charBoxModalData = {
        questionId: null,
        itemIndex: null,
        itemType: null,
        isDrawing: false,
        startX: 0,
        startY: 0,
        currentBox: null,
        imageWidth: 0,
        imageHeight: 0,
        mode: 'charbox',
        splitLines: []
    };
}

function clearCharBoxOverlay() {
    const overlay = document.getElementById('charBoxOverlay');
    overlay.innerHTML = '';
}

function drawCharBox(box) {
    const overlay = document.getElementById('charBoxOverlay');
    const img = document.getElementById('charBoxImage');

    overlay.innerHTML = '';

    const rect = document.createElement('div');
    rect.className = 'char-box-rect';

    const displayWidth = img.clientWidth;
    const displayHeight = img.clientHeight;

    rect.style.left = (box.x * displayWidth) + 'px';
    rect.style.top = (box.y * displayHeight) + 'px';
    rect.style.width = (box.width * displayWidth) + 'px';
    rect.style.height = (box.height * displayHeight) + 'px';

    overlay.appendChild(rect);
}

async function confirmCharBox() {
    if (!charBoxModalData.currentBox && charBoxModalData.mode === 'charbox') {
        alert('请先绘制字框');
        return;
    }

    const charBoxData = charBoxModalData.currentBox ? {
        ...charBoxModalData.currentBox,
        fontSize: document.getElementById('charBoxFontSize').value
    } : null;

    const question = questions.find(q => q.id === charBoxModalData.questionId);
    if (question) {
        let items;
        if (charBoxModalData.itemType === 'question') {
            items = question.question?.items || [];
        } else if (charBoxModalData.itemType === 'answer') {
            items = question.answer?.items || [];
        }
        const item = items[charBoxModalData.itemIndex];
        if (item) {
            if (charBoxData) {
                item.charBox = charBoxData;
            }
            if (charBoxModalData.splitLines.length > 0) {
                item.splitLines = [...charBoxModalData.splitLines];
            } else {
                delete item.splitLines;
            }
        }
    }

    if (currentQuestion && currentQuestion.id === charBoxModalData.questionId) {
        if (charBoxModalData.itemType === 'question') {
            if (charBoxData) {
                questionItems[charBoxModalData.itemIndex].charBox = charBoxData;
            }
            if (charBoxModalData.splitLines.length > 0) {
                questionItems[charBoxModalData.itemIndex].splitLines = [...charBoxModalData.splitLines];
            } else {
                delete questionItems[charBoxModalData.itemIndex].splitLines;
            }
        } else if (charBoxModalData.itemType === 'answer') {
            if (charBoxData) {
                answerItems[charBoxModalData.itemIndex].charBox = charBoxData;
            }
            if (charBoxModalData.splitLines.length > 0) {
                answerItems[charBoxModalData.itemIndex].splitLines = [...charBoxModalData.splitLines];
            } else {
                delete answerItems[charBoxModalData.itemIndex].splitLines;
            }
        }
        renderContentList();
    }

    try {
        const q = questions.find(q => q.id === charBoxModalData.questionId);
        const response = await fetch('/api/questions/' + charBoxModalData.questionId, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: q.question,
                answer: q.answer,
                tags: q.tags,
                sub_questions: q.sub_questions
            })
        });

        const result = await response.json();
        if (result.success) {
            const q = questions.find(q => q.id === charBoxModalData.questionId);
            if (q && result.question) {
                q.question = result.question.question;
                q.answer = result.question.answer;
                q.tags = result.question.tags;
                q.sub_questions = result.question.sub_questions;
            }
            if (currentQuestion && currentQuestion.id === charBoxModalData.questionId) {
                loadQuestionForEdit(charBoxModalData.questionId, true);
            }
            closeCharBoxModal();
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

document.getElementById('charBoxOverlay').addEventListener('mousedown', function(e) {
    if (charBoxModalData.mode === 'splitline') {
        if (e.button === 2) {
            e.preventDefault();
            const rect = this.getBoundingClientRect();
            const y = e.clientY - rect.top;
            const img = document.getElementById('charBoxImage');
            const yRatio = y / img.clientHeight;
            addSplitLine(yRatio);
        }
        return;
    }

    if (e.button !== 0) return;

    const rect = this.getBoundingClientRect();
    charBoxModalData.isDrawing = true;
    charBoxModalData.startX = e.clientX - rect.left;
    charBoxModalData.startY = e.clientY - rect.top;

    clearCharBoxOverlay();

    const box = document.createElement('div');
    box.className = 'char-box-rect';
    box.id = 'tempCharBox';
    box.style.left = charBoxModalData.startX + 'px';
    box.style.top = charBoxModalData.startY + 'px';
    box.style.width = '0px';
    box.style.height = '0px';
    this.appendChild(box);
});

document.getElementById('charBoxOverlay').addEventListener('mousemove', function(e) {
    if (!charBoxModalData.isDrawing) return;

    const rect = this.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    const deltaX = currentX - charBoxModalData.startX;
    const deltaY = currentY - charBoxModalData.startY;

    const size = Math.max(Math.abs(deltaX), Math.abs(deltaY));

    const box = document.getElementById('tempCharBox');
    if (box) {
        let left = charBoxModalData.startX;
        let top = charBoxModalData.startY;

        if (deltaX < 0) left = charBoxModalData.startX - size;
        if (deltaY < 0) top = charBoxModalData.startY - size;

        box.style.left = left + 'px';
        box.style.top = top + 'px';
        box.style.width = size + 'px';
        box.style.height = size + 'px';
    }
});

document.getElementById('charBoxOverlay').addEventListener('mouseup', function(e) {
    if (!charBoxModalData.isDrawing) return;

    charBoxModalData.isDrawing = false;

    const box = document.getElementById('tempCharBox');
    if (box) {
        const img = document.getElementById('charBoxImage');
        const displayWidth = img.clientWidth;
        const displayHeight = img.clientHeight;

        const boxLeft = parseFloat(box.style.left);
        const boxTop = parseFloat(box.style.top);
        const boxSize = parseFloat(box.style.width);

        if (boxSize > 10) {
            charBoxModalData.currentBox = {
                x: boxLeft / displayWidth,
                y: boxTop / displayHeight,
                width: boxSize / displayWidth,
                height: boxSize / displayHeight
            };
        } else {
            clearCharBoxOverlay();
        }
    }
});

document.getElementById('charBoxOverlay').addEventListener('mouseleave', function(e) {
    if (charBoxModalData.isDrawing) {
        charBoxModalData.isDrawing = false;
    }
});

document.getElementById('charBoxOverlay').addEventListener('contextmenu', function(e) {
    if (charBoxModalData.mode === 'splitline') {
        e.preventDefault();
    }
});
