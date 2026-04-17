const API_BASE = '';

let questionItems = [];
let answerItems = [];
let currentTab = 'question';
let itemCounter = 0;
let activeMainPaste = null;
let tags = [];
let subQuestions = [];
let subQuestionCounter = 0;
let activeSubQuestionId = null;

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

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        const tabName = tab.dataset.tab;
        document.getElementById(`${tabName}-tab`).classList.add('active');
        currentTab = tabName;
        activeMainPaste = tabName;
        updateMainPasteButtons();
    });
});

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
                    <button class="char-box-btn-annotate ${hasCharBox ? 'has-box' : ''}" onclick="openCharBoxModal(${index}, '${target}')">${hasCharBox ? '已标注' : '标注字框'}</button>
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

function addTextToSubQuestion(sqId) {
    const sq = subQuestions.find(s => s.id === sqId);
    if (!sq) return;

    if (!sq.questionText) {
        sq.questionText = { items: [] };
    }
    if (!sq.questionText.items) {
        sq.questionText.items = [];
    }

    const newItem = {
        id: ++itemCounter,
        type: 'text',
        content: ''
    };
    sq.questionText.items.push(newItem);
    renderSubQuestions();

    setTimeout(() => {
        const card = document.querySelector(`[data-sq-id="${sqId}"]`);
        if (card) {
            const textItems = card.querySelectorAll('.text-item');
            if (textItems.length > 0) {
                const lastTextItem = textItems[textItems.length - 1];
                const textContent = lastTextItem.querySelector('.text-item-content');
                if (textContent) {
                    const newIndex = sq.questionText.items.length - 1;
                    doEditTextForSubQuestion(textContent, newIndex, sqId);
                }
            }
        }
    }, 10);
}

function doEditTextForSubQuestion(element, index, sqId) {
    const sq = subQuestions.find(s => s.id === sqId);
    if (!sq || !sq.questionText || !sq.questionText.items) return;

    const items = sq.questionText.items;
    const item = items[index];
    if (!item) return;

    const currentContent = item.content || '';
    element.contentEditable = 'true';
    element.classList.add('editing');

    element.addEventListener('blur', function onBlur() {
        const newContent = element.textContent;
        items[index].content = newContent;
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

function renderPreview() {
    const questionPreview = document.getElementById('question-preview');
    const answerPreview = document.getElementById('answer-preview');

    questionPreview.innerHTML = renderItemsPreview(questionItems);
    answerPreview.innerHTML = renderItemsPreview(answerItems);
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
            html += `<img src="${item.base64 || item.src}" class="${imgClass}" style="width: ${item.width}px; height: ${heightStyle};" alt="图片">`;
        }
    });

    return html;
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
    const id = ++subQuestionCounter;
    subQuestions.push({
        id: id,
        title: `第${id}小问`,
        questionText: { items: [] },
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
    container.innerHTML = '';

    subQuestions.forEach(sq => {
        const card = document.createElement('div');
        card.className = 'sub-question-card';
        card.dataset.sqId = sq.id;

        const itemsHtml = (sq.questionText?.items || []).map((item, idx) => {
            if (item.type === 'text' || item.type === 'richtext') {
                return `<div class="text-item">
                    <div class="text-item-content" ondblclick="doEditTextForSubQuestion(this, ${idx}, ${sq.id})">${item.type === 'richtext' ? Utils.renderRichtext(item.fragments) : Utils.escapeHtml(item.content)}</div>
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
                <button class="add-text-btn" onclick="addTextToSubQuestion(${sq.id})">+ 添加文本</button>
                ${itemsHtml}
                <div class="sub-question-tags" id="sq-tags-${sq.id}">
                    ${sq.tags.map((tag, idx) => `
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

function activateSubQuestionPaste(id) {
    activeSubQuestionId = id;
    activeMainPaste = null;
    updateMainPasteButtons();
    renderSubQuestions();
}

function updateSubQuestionPasteButtons() {
    subQuestions.forEach(sq => {
        const btn = document.getElementById(`sq-paste-btn-${sq.id}`);
        if (btn) {
            btn.classList.toggle('active', activeSubQuestionId === sq.id);
        }
    });
}

function removeSubQuestionContent(id, contentIndex) {
    const sq = subQuestions.find(s => s.id === id);
    if (sq && sq.questionText && sq.questionText.items) {
        sq.questionText.items.splice(contentIndex, 1);
        renderSubQuestions();
    }
}

function updateSubQuestionImageDisplay(sqId, itemIndex, display) {
    const sq = subQuestions.find(s => s.id === sqId);
    if (sq && sq.questionText && sq.questionText.items && sq.questionText.items[itemIndex]) {
        sq.questionText.items[itemIndex].display = display;
        renderSubQuestions();
    }
}

function updateSubQuestionImageSize(sqId, itemIndex, dimension, value) {
    const sq = subQuestions.find(s => s.id === sqId);
    if (sq && sq.questionText && sq.questionText.items && sq.questionText.items[itemIndex]) {
        if (dimension === 'height' && !value) {
            sq.questionText.items[itemIndex][dimension] = 'auto';
        } else {
            sq.questionText.items[itemIndex][dimension] = parseInt(value) || 300;
        }
        renderSubQuestions();
    }
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
        sq.questionText.items.push({
            id: ++itemCounter,
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
        sq.questionText.items.push({
            id: ++itemCounter,
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
                    sq.questionText.items.push({
                        id: ++itemCounter,
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

function handleSubQuestionTagInput(id, event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const input = event.target;
        addSubQuestionTag(id, input.value);
        input.value = '';
    }
}

document.getElementById('tag-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        const input = e.target;
        addTag(input.value);
        input.value = '';
    }
});

document.getElementById('save-btn').addEventListener('click', async () => {
    if (questionItems.length === 0 && answerItems.length === 0) {
        alert('请先添加内容');
        return;
    }

    const cleanItems = (items) => {
        return Utils.cleanItems(items);
    };

    const cleanSubQuestions = () => {
        return subQuestions.map(sq => ({
            id: sq.id,
            title: sq.title,
            question_text: {
                items: cleanItems(sq.questionText.items)
            },
            tags: [...sq.tags]
        }));
    };

    const data = {
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
        const result = await API.saveQuestion(data);

        if (result.success) {
            alert('保存成功！题目ID: ' + result.id);

            questionItems = [];
            answerItems = [];
            itemCounter = 0;
            tags = [];

            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector('[data-tab="question"]').classList.add('active');
            document.getElementById('question-tab').classList.add('active');
            currentTab = 'question';

            document.getElementById('question-content-list').innerHTML = '';
            document.getElementById('answer-content-list').innerHTML = '';
            subQuestions = [];
            subQuestionCounter = 0;
            renderSubQuestions();

            renderPreview();
            renderTags();
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
});

renderPreview();
renderContentList();

let pollInterval = null;

function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(checkForScreenshots, 1000);
    checkForScreenshots();
    console.log('开始轮询检查截图...');
}

function checkForScreenshots() {
    fetch(`${API_BASE}/api/screenshot/check`)
        .then(response => response.json())
        .then(result => {
            if (result.success && result.has_screenshot) {
                result.screenshots.forEach(screenshot => {
                    consumeScreenshot(screenshot.id);
                });
            }
        })
        .catch(error => {
            console.error('检查截图失败:', error);
        });
}

async function consumeScreenshot(screenshotId) {
    try {
        const result = await API.consumeScreenshot(screenshotId);
        if (result.success) {
            const target = currentTab;
            const items = getCurrentItems(target);
            const newItem = {
                id: ++itemCounter,
                type: 'image',
                image_id: result.image_id,
                config_id: null,
                src: result.path,
                display: 'center',
                width: 300,
                height: 'auto'
            };
            items.push(newItem);
            setCurrentItems(items, target);

            const contentList = getCurrentContentList(target);
            renderContentList(contentList, items, target);
            renderPreview();
            console.log('截图已加载:', result.path);
        }
    } catch (error) {
        console.error('消费截图失败:', error);
    }
}

let charBoxModalData = {
    itemIndex: null,
    target: null,
    isDrawing: false,
    startX: 0,
    startY: 0,
    currentBox: null,
    imageWidth: 0,
    imageHeight: 0,
    mode: 'charbox',
    splitLines: []
};

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

function openCharBoxModal(itemIndex, target) {
    const items = getCurrentItems(target);
    const item = items[itemIndex];
    if (!item || item.type !== 'image') return;

    charBoxModalData.itemIndex = itemIndex;
    charBoxModalData.target = target;
    charBoxModalData.currentBox = item.charBox ? { ...item.charBox } : null;
    charBoxModalData.splitLines = item.splitLines ? [...item.splitLines] : [];
    charBoxModalData.mode = 'charbox';

    const modal = document.getElementById('charBoxModal');
    const img = document.getElementById('charBoxImage');
    const imgSrc = item.base64 || (item.src && !item.src.startsWith('http') ? '/' + item.src : item.src);

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

function closeCharBoxModal() {
    const modal = document.getElementById('charBoxModal');
    modal.style.display = 'none';
    clearCharBoxOverlay();
    clearSplitLines();
    charBoxModalData = {
        itemIndex: null,
        target: null,
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
    rect.style.width = (box.size * displayWidth) + 'px';
    rect.style.height = (box.size * displayWidth) + 'px';

    overlay.appendChild(rect);
}

function confirmCharBox() {
    if (!charBoxModalData.currentBox && charBoxModalData.mode === 'charbox') {
        alert('请先绘制字框');
        return;
    }

    const items = getCurrentItems(charBoxModalData.target);
    const item = items[charBoxModalData.itemIndex];
    if (item) {
        if (charBoxModalData.currentBox) {
            item.charBox = {
                ...charBoxModalData.currentBox,
                fontSize: document.getElementById('charBoxFontSize').value
            };
        }
        if (charBoxModalData.splitLines.length > 0) {
            item.splitLines = [...charBoxModalData.splitLines];
        } else {
            delete item.splitLines;
        }
        setCurrentItems(items, charBoxModalData.target);

        const contentList = getCurrentContentList(charBoxModalData.target);
        renderContentList(contentList, items, charBoxModalData.target);
        renderPreview();
    }

    closeCharBoxModal();
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
                size: boxSize / displayWidth
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

startPolling();
