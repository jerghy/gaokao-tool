let questions = [];
let selectedIds = new Set();
let allTags = [];
let activeTag = null;
let currentSearchQuery = '';

async function loadQuestions(searchQuery = '') {
    try {
        const data = await API.getQuestions({ page: 1, page_size: 10000, search: searchQuery.trim() || undefined });
        console.log('API response:', data);
        questions = data.questions || [];
        currentSearchQuery = searchQuery;
        console.log('Questions loaded:', questions.length);
        
        if (questions.length > 0) {
            const firstQ = questions[0];
            console.log('First question items:', firstQ.question?.items);
        }

        const urlParams = new URLSearchParams(window.location.search);
        const preselectedIds = urlParams.get('ids');

        if (preselectedIds) {
            const idArray = preselectedIds.split(',');
            idArray.forEach(id => {
                const question = questions.find(q => q.id == id);
                if (question) {
                    selectedIds.add(question.id);
                }
            });
        }

        extractAllTags();
        renderTagFilter();
        renderFileList();

        if (preselectedIds && selectedIds.size > 0) {
            fileListCollapsed = false;
            document.getElementById('fileList').classList.remove('collapsed');
            document.getElementById('fileListToggle').textContent = '▼ 点击折叠';
            renderPreview();
        }
    } catch (e) {
        console.error('Load questions failed:', e);
        document.getElementById('fileList').innerHTML = '<span style="color: red;">加载失败: ' + e.message + '</span>';
    }
}

function extractAllTags() {
    const tagSet = new Set();
    questions.forEach(q => {
        if (q.tags && Array.isArray(q.tags)) {
            q.tags.forEach(tag => tagSet.add(tag));
        }
    });
    allTags = Array.from(tagSet).sort();
}

let expandedTags = new Set();

function renderTagFilter() {
    const container = document.getElementById('tagFilter');
    if (allTags.length === 0) {
        container.innerHTML = '<span class="tag-filter-label">标签筛选:</span><span style="color: #999;">无标签</span>';
        return;
    }

    const tagTree = buildTagTree(allTags);
    
    let html = '<span class="tag-filter-label">标签筛选:</span>';
    html += '<div class="tag-tree">';
    
    html += '<div class="tag-tree-all' + (activeTag === null ? ' active' : '') + '" onclick="filterByTag(null)">全部 (' + questions.length + ')</div>';
    
    html += renderTreeNode(tagTree, '');
    
    html += '</div>';
    container.innerHTML = html;
}

function buildTagTree(tags) {
    const tree = {};
    
    tags.forEach(tag => {
        if (tag.includes('::')) {
            const parts = tag.split('::');
            let current = tree;
            
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                if (!current[part]) {
                    current[part] = { __children__: {} };
                }
                if (i < parts.length - 1) {
                    current = current[part].__children__;
                }
            }
        } else {
            if (!tree[tag]) {
                tree[tag] = { __children__: {} };
            }
        }
    });
    
    return tree;
}

function renderTreeNode(tree, prefix) {
    let html = '';
    
    const sortedKeys = Object.keys(tree).sort();
    
    for (const tag of sortedKeys) {
        const value = tree[tag];
        const fullTag = prefix ? `${prefix}::${tag}` : tag;
        const children = value.__children__ || {};
        const hasChildren = Object.keys(children).length > 0;
        const isExpanded = expandedTags.has(fullTag);
        const isSelected = activeTag === fullTag;
        const count = countQuestionsWithTag(fullTag);
        
        if (count === 0) continue;
        
        html += '<div class="tag-tree-item">';
        html += '<div class="tag-tree-content' + (isSelected ? ' selected' : '') + '" onclick="filterByTag(\'' + escapeHtml(fullTag) + '\')">';
        
        if (hasChildren) {
            html += '<span class="tag-tree-toggle" onclick="event.stopPropagation(); toggleTagExpand(\'' + escapeHtml(fullTag) + '\')">' + (isExpanded ? '▼' : '▶') + '</span>';
        } else {
            html += '<span class="tag-tree-toggle hidden"></span>';
        }
        
        html += '<span class="tag-tree-label">' + escapeHtml(tag) + '</span>';
        html += '<span class="tag-tree-count">(' + count + ')</span>';
        html += '</div>';
        
        if (hasChildren) {
            html += '<div class="tag-tree-children' + (isExpanded ? ' expanded' : '') + '">';
            html += renderTreeNode(children, fullTag);
            html += '</div>';
        }
        
        html += '</div>';
    }
    
    return html;
}

function toggleTagExpand(tag) {
    if (expandedTags.has(tag)) {
        expandedTags.delete(tag);
    } else {
        expandedTags.add(tag);
    }
    renderTagFilter();
}

function countQuestionsWithTag(tag) {
    return questions.filter(q => {
        if (!q.tags) return false;
        return q.tags.some(t => t === tag || t.startsWith(tag + '::'));
    }).length;
}

function filterByTag(tag) {
    activeTag = tag;
    renderTagFilter();
    renderFileList();
}

function getFilteredQuestions() {
    let filtered = questions;

    if (activeTag !== null) {
        filtered = filtered.filter(q => {
            if (!q.tags) return false;
            return q.tags.some(t => t === activeTag || t.startsWith(activeTag + '::'));
        });
    }

    return filtered;
}

let searchTimeout = null;

async function applySearchFilter() {
    const searchQuery = document.getElementById('searchInput').value;
    
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    searchTimeout = setTimeout(async () => {
        await loadQuestions(searchQuery);
    }, 300);
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    loadQuestions('');
}

let fileListCollapsed = false;

function toggleFileList() {
    const fileList = document.getElementById('fileList');
    const toggle = document.getElementById('fileListToggle');
    fileListCollapsed = !fileListCollapsed;
    fileList.classList.toggle('collapsed', fileListCollapsed);
    toggle.textContent = fileListCollapsed ? '▶ 点击展开' : '▼ 点击折叠';
}

function renderFileList() {
    const container = document.getElementById('fileList');
    const countSpan = document.getElementById('selectedCount');
    const filtered = getFilteredQuestions();
    if (filtered.length === 0) {
        container.innerHTML = '<span style="color: #999;">暂无题目</span>';
        return;
    }

    container.innerHTML = filtered.map(q => `
        <div class="file-item ${selectedIds.has(q.id) ? 'selected' : ''}"
             onclick="toggleSelect('${q.id}')">
            ${q.id}
        </div>
    `).join('');

    if (countSpan) {
        countSpan.textContent = selectedIds.size;
    }
}

function toggleSelect(id) {
    if (selectedIds.has(id)) {
        selectedIds.delete(id);
    } else {
        selectedIds.add(id);
    }
    renderFileList();
}

function selectAll() {
    const filtered = getFilteredQuestions();
    filtered.forEach(q => selectedIds.add(q.id));
    renderFileList();
}

function deselectAll() {
    const filtered = getFilteredQuestions();
    filtered.forEach(q => selectedIds.delete(q.id));
    renderFileList();
}

function invertSelection() {
    const filtered = getFilteredQuestions();
    filtered.forEach(q => {
        if (selectedIds.has(q.id)) {
            selectedIds.delete(q.id);
        } else {
            selectedIds.add(q.id);
        }
    });
    renderFileList();
}

function toggleAnnotation() {
    const container = document.getElementById('printContainer');
    if (document.getElementById('showAnnotation').checked) {
        container.classList.add('annotation-mode');
    } else {
        container.classList.remove('annotation-mode');
    }
}

function toggleCompact() {
    const container = document.getElementById('printContainer');
    if (document.getElementById('compactMode').checked) {
        container.classList.add('compact-mode');
    } else {
        container.classList.remove('compact-mode');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderLatex(text) {
    if (!text || typeof text !== 'string') return text;

    let result = text;

    result = result.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
        try {
            return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false, trust: true });
        } catch (e) {
            return match;
        }
    });

    result = result.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
        try {
            return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false, trust: true });
        } catch (e) {
            return match;
        }
    });

    result = result.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        try {
            return katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false, trust: true });
        } catch (e) {
            return match;
        }
    });

    result = result.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
        try {
            return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false, trust: true });
        } catch (e) {
            return match;
        }
    });

    return result;
}

function protectLatexInMarkdown(text) {
    const placeholders = [];
    
    text = text.replace(/\\\\/g, '\\');
    
    text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
        const index = placeholders.length;
        try {
            placeholders.push(katex.renderToString(formula.trim(), { 
                displayMode: true, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(match);
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    text = text.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
        const index = placeholders.length;
        try {
            placeholders.push(katex.renderToString(formula.trim(), { 
                displayMode: true, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(match);
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    text = text.replace(/(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)/g, (match, formula) => {
        const index = placeholders.length;
        try {
            let f = formula.trim();
            const hasComplex = /\\frac|\\dfrac|\\cfrac|\\sqrt|\\sum|\\int|\\prod|\\lim|\\binom|\\dbinom|\\tfrac/.test(f);
            if (hasComplex && !f.includes('\\displaystyle') && !f.includes('\\textstyle')) {
                f = '\\displaystyle ' + f;
            }
            placeholders.push(katex.renderToString(f, { 
                displayMode: false, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(match);
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    text = text.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
        const index = placeholders.length;
        try {
            let f = formula.trim();
            const hasComplex = /\\frac|\\dfrac|\\cfrac|\\sqrt|\\sum|\\int|\\prod|\\lim|\\binom|\\dbinom|\\tfrac/.test(f);
            if (hasComplex && !f.includes('\\displaystyle') && !f.includes('\\textstyle')) {
                f = '\\displaystyle ' + f;
            }
            placeholders.push(katex.renderToString(f, { 
                displayMode: false, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(match);
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    return { text, placeholders };
}

function restoreLatexFromPlaceholders(html, placeholders) {
    placeholders.forEach((latexHtml, index) => {
        html = html.replace(`%%LATEX_PLACEHOLDER_${index}%%`, latexHtml);
    });
    return html;
}

function renderMarkdownWithLatex(content) {
    if (!content) return '';
    
    const { text: protectedText, placeholders } = protectLatexInMarkdown(content);
    
    let html = marked.parse(protectedText, {
        gfm: true,
        breaks: true
    });
    
    html = restoreLatexFromPlaceholders(html, placeholders);
    
    html = html.replace(/(<strong>目标解决)/g, '<hr style="border:none;border-top:1px dashed #666;margin:2mm 0;">$1');
    
    return html;
}

function processTextWithLatex(text) {
    if (!text) return '';
    const placeholders = [];
    
    text = text.replace(/\\\\/g, '\\');
    
    text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
        const index = placeholders.length;
        try {
            placeholders.push(katex.renderToString(formula.trim(), { 
                displayMode: true, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(escapeHtml(match));
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    text = text.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
        const index = placeholders.length;
        try {
            placeholders.push(katex.renderToString(formula.trim(), { 
                displayMode: true, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(escapeHtml(match));
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    text = text.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        const index = placeholders.length;
        try {
            let f = formula.trim();
            const hasComplex = /\\frac|\\dfrac|\\cfrac|\\sqrt|\\sum|\\int|\\prod|\\lim|\\binom|\\dbinom|\\tfrac/.test(f);
            if (hasComplex && !f.includes('\\displaystyle') && !f.includes('\\textstyle')) {
                f = '\\displaystyle ' + f;
            }
            placeholders.push(katex.renderToString(f, { 
                displayMode: false, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(escapeHtml(match));
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    text = text.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
        const index = placeholders.length;
        try {
            let f = formula.trim();
            const hasComplex = /\\frac|\\dfrac|\\cfrac|\\sqrt|\\sum|\\int|\\prod|\\lim|\\binom|\\dbinom|\\tfrac/.test(f);
            if (hasComplex && !f.includes('\\displaystyle') && !f.includes('\\textstyle')) {
                f = '\\displaystyle ' + f;
            }
            placeholders.push(katex.renderToString(f, { 
                displayMode: false, 
                throwOnError: false, 
                trust: true 
            }));
        } catch (e) {
            placeholders.push(escapeHtml(match));
        }
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    text = escapeHtml(text);
    
    placeholders.forEach((latexHtml, index) => {
        text = text.replace(`%%LATEX_PLACEHOLDER_${index}%%`, latexHtml);
    });
    
    return text;
}

function renderRichtextInline(fragments) {
    if (!fragments || !Array.isArray(fragments)) return '';
    let html = '';
    for (const frag of fragments) {
        let text = frag.text || '';
        let isUnderline = frag.underline || false;
        
        if (isUnderline) {
            text = text.replace(/\u3000/g, ' ');
            text = text.replace(/\u00A0/g, ' ');
            text = text.replace(/ /g, '_');
        }
        
        let escaped = escapeHtml(text);
        if (isUnderline) {
            escaped = escaped.replace(/&nbsp;/g, '_');
        }
        
        if (!isUnderline) {
            escaped = renderLatex(escaped);
        }
        
        const withBreaks = escaped.replace(/\r\n/g, '<br>').replace(/\n/g, '<br>').replace(/\r/g, '<br>');
        
        if (isUnderline) {
            html += `<span class="underline-space">${withBreaks}</span>`;
        } else {
            html += withBreaks;
        }
    }
    return html;
}

function renderRichtext(fragments) {
    if (!fragments || !Array.isArray(fragments)) return '';
    let html = '';
    for (const frag of fragments) {
        let text = frag.text || '';
        let isUnderline = frag.underline || false;
        
        if (isUnderline) {
            text = text.replace(/\u3000/g, ' ');
            text = text.replace(/\u00A0/g, ' ');
            text = text.replace(/ /g, '_');
        }
        
        let escaped = escapeHtml(text);
        if (isUnderline) {
            escaped = escaped.replace(/&nbsp;/g, '_');
        }
        
        if (!isUnderline) {
            escaped = renderLatex(escaped);
        }
        
        const withBreaks = escaped.replace(/\r\n/g, '</p><p>').replace(/\n/g, '</p><p>').replace(/\r/g, '</p><p>');
        
        if (isUnderline) {
            html += `<span class="underline-space">${withBreaks}</span>`;
        } else {
            html += withBreaks;
        }
    }
    return html;
}

const splitImageApiCache = {};

async function fetchSplitImageFromServer(item) {
    if (!item.src) {
        console.error('Image src is missing:', item);
        return [{ src: '', width: item.width || 300 }];
    }
    const src = item.src.startsWith('/') ? item.src : '/' + item.src;
    const splitLines = item.splitLines || [];
    let imgWidth = item.width || 300;
    
    if (item.charBox && item.charBox.width && item.charBox.height && item.naturalWidth && item.naturalHeight) {
        const scale = calculateImageScale(item.charBox, item.naturalWidth, item.naturalHeight);
        if (scale && scale > 0) {
            imgWidth = Math.round(item.naturalWidth * scale);
        }
    }
    
    const cacheKey = `${src}_${splitLines.join(',')}_${imgWidth}`;
    if (splitImageApiCache[cacheKey]) {
        return splitImageApiCache[cacheKey];
    }
    
    try {
        const result = await API.splitImage({
            src: src,
            splitLines: splitLines,
            width: imgWidth
        });
        
        if (result.success) {
            splitImageApiCache[cacheKey] = result.parts;
            return result.parts;
        } else {
            console.error('Split image failed:', result.error);
            return [{ src: src, width: imgWidth }];
        }
    } catch (e) {
        console.error('Failed to fetch split image:', e);
        return [{ src: src, width: imgWidth }];
    }
}

function splitImageByLines(item) {
    if (!item.splitLines || item.splitLines.length === 0) {
        return [item];
    }

    const src = item.src.startsWith('/') ? item.src : '/' + item.src;
    const floatClass = item.display ? (item.display === 'center' ? 'center' : `float-${item.display}`) : 'center';
    
    let imgWidth = item.width || 300;
    if (item.charBox && item.charBox.width && item.charBox.height && item.naturalWidth && item.naturalHeight) {
        const scale = calculateImageScale(item.charBox, item.naturalWidth, item.naturalHeight);
        if (scale && scale > 0) {
            imgWidth = Math.round(item.naturalWidth * scale);
        }
    }

    const lines = [0, ...item.splitLines, 1];
    const parts = [];

    for (let i = 0; i < lines.length - 1; i++) {
        const topRatio = lines[i];
        const bottomRatio = lines[i + 1];
        const heightRatio = bottomRatio - topRatio;

        parts.push({
            type: 'image-part',
            src: src,
            floatClass: floatClass,
            width: imgWidth,
            topRatio: topRatio,
            bottomRatio: bottomRatio,
            heightRatio: heightRatio
        });
    }

    return parts;
}

async function renderSplitImagePartsAsync(item) {
    const parts = await fetchSplitImageFromServer(item);
    const floatClass = item.display ? (item.display === 'center' ? 'center' : `float-${item.display}`) : 'center';
    
    return parts.map(part => 
        `<img src="${part.src}" class="question-image ${floatClass}" style="width: ${part.width}px; display: block;">`
    ).join('');
}

function calculateImageScale(charBox, imgNaturalWidth, imgNaturalHeight) {
    if (!charBox || !charBox.width || !charBox.height) return null;
    
    if (!imgNaturalWidth || !imgNaturalHeight) {
        console.log('calculateImageScale: missing natural dimensions', { imgNaturalWidth, imgNaturalHeight });
        return null;
    }
    
    const fontSizeMap = {
        'large': 16,
        'medium': 13,
        'small': 11
    };
    
    const fontSizePx = fontSizeMap[charBox.fontSize] || 16;
    
    const charBoxPixelWidth = charBox.width * imgNaturalWidth;
    const charBoxPixelHeight = charBox.height * imgNaturalHeight;
    const charBoxPixelSize = Math.min(charBoxPixelWidth, charBoxPixelHeight);
    
    const scale = fontSizePx / charBoxPixelSize;
    
    console.log('calculateImageScale:', {
        charBox,
        imgNaturalWidth,
        imgNaturalHeight,
        charBoxPixelWidth,
        charBoxPixelHeight,
        charBoxPixelSize,
        fontSizePx,
        scale,
        newWidth: imgNaturalWidth * scale
    });
    
    return scale;
}

function renderItem(item) {
    if (item.type === 'text') {
        if (typeof item.content === 'string') {
            const processed = processTextWithLatex(item.content);
            const withBreaks = processed.replace(/\r\n/g, '</p><p>').replace(/\n/g, '</p><p>').replace(/\r/g, '</p><p>');
            return `<p>${withBreaks}</p>`;
        } else if (Array.isArray(item.content)) {
            return `<p>${renderRichtext(item.content)}</p>`;
        }
    } else if (item.type === 'richtext') {
        if (item.fragments && Array.isArray(item.fragments)) {
            return `<p>${renderRichtext(item.fragments)}</p>`;
        } else if (typeof item.content === 'string') {
            const processed = processTextWithLatex(item.content);
            const withBreaks = processed.replace(/\r\n/g, '</p><p>').replace(/\n/g, '</p><p>').replace(/\r/g, '</p><p>');
            return `<p>${withBreaks}</p>`;
        }
    } else if (item.type === 'image') {
        if (item.splitLines && item.splitLines.length > 0) {
            return { needsSplit: true, item };
        }
        
        if (!item.src) {
            console.error('Image item missing src:', item);
            return '<p style="color: red;">[图片加载失败: 缺少src]</p>';
        }
        
        if (!item.src) {
            console.error('Image item missing src:', item);
            return '<span style="color: red;">[图片加载失败]</span>';
        }
        
        const floatClass = item.display ? (item.display === 'center' ? 'center' : `float-${item.display}`) : 'center';
        const src = item.src.startsWith('/') ? item.src : '/' + item.src;
        
        let widthStyle = '';
        if (item.charBox && item.charBox.width && item.charBox.height && item.naturalWidth && item.naturalHeight) {
            const scale = calculateImageScale(item.charBox, item.naturalWidth, item.naturalHeight);
            if (scale && scale > 0) {
                const scaledWidth = item.naturalWidth * scale;
                widthStyle = `width: ${Math.round(scaledWidth)}px;`;
            } else {
                widthStyle = item.width ? `width: ${item.width}px;` : '';
            }
        } else {
            widthStyle = item.width ? `width: ${item.width}px;` : '';
        }
        
        return `<img src="${src}" class="question-image ${floatClass}" style="${widthStyle}">`;
    }
    return '';
}

async function renderItemsAsync(items) {
    if (!items || items.length === 0) return '<p style="color: #999;">无内容</p>';
    const results = [];
    for (const item of items) {
        const result = renderItem(item);
        if (result && result.needsSplit) {
            const splitHtml = await renderSplitImagePartsAsync(result.item);
            results.push(splitHtml);
        } else {
            results.push(result);
        }
    }
    return results.join('');
}

function renderItems(items) {
    if (!items || items.length === 0) return '<p style="color: #999;">无内容</p>';
    return items.map(item => {
        const result = renderItem(item);
        if (result && result.needsSplit) {
            return `<div class="split-image-placeholder" data-split-item='${JSON.stringify(result.item)}'></div>`;
        }
        return result;
    }).join('');
}

function renderItemInline(item) {
    if (item.type === 'text') {
        if (typeof item.content === 'string') {
            const processed = processTextWithLatex(item.content);
            return processed.replace(/\r\n/g, '<br>').replace(/\n/g, '<br>').replace(/\r/g, '<br>');
        } else if (Array.isArray(item.content)) {
            return renderRichtextInline(item.content);
        }
    } else if (item.type === 'richtext') {
        if (item.fragments && Array.isArray(item.fragments)) {
            return renderRichtextInline(item.fragments);
        } else if (typeof item.content === 'string') {
            const processed = processTextWithLatex(item.content);
            return processed.replace(/\r\n/g, '<br>').replace(/\n/g, '<br>').replace(/\r/g, '<br>');
        }
    } else if (item.type === 'image') {
        if (item.splitLines && item.splitLines.length > 0) {
            return { needsSplit: true, item };
        }
        
        const floatClass = item.display ? (item.display === 'center' ? 'center' : `float-${item.display}`) : 'center';
        const src = item.src.startsWith('/') ? item.src : '/' + item.src;
        
        let widthStyle = '';
        if (item.charBox && item.charBox.width && item.charBox.height && item.naturalWidth && item.naturalHeight) {
            const scale = calculateImageScale(item.charBox, item.naturalWidth, item.naturalHeight);
            if (scale && scale > 0) {
                const scaledWidth = item.naturalWidth * scale;
                widthStyle = `width: ${Math.round(scaledWidth)}px;`;
            } else {
                widthStyle = item.width ? `width: ${item.width}px;` : '';
            }
        } else {
            widthStyle = item.width ? `width: ${item.width}px;` : '';
        }
        
        return `<img src="${src}" class="question-image ${floatClass}" style="${widthStyle}">`;
    }
    return '';
}

async function renderItemsInlineAsync(items) {
    if (!items || items.length === 0) return '<span style="color: #999;">无内容</span>';
    const results = [];
    for (const item of items) {
        const result = renderItemInline(item);
        if (result && result.needsSplit) {
            const splitHtml = await renderSplitImagePartsAsync(result.item);
            results.push(splitHtml);
        } else {
            results.push(result);
        }
    }
    return results.join('');
}

function renderItemsInline(items) {
    if (!items || items.length === 0) return '<span style="color: #999;">无内容</span>';
    return items.map(item => {
        const result = renderItemInline(item);
        if (result && result.needsSplit) {
            return `<div class="split-image-placeholder" data-split-item='${JSON.stringify(result.item)}'></div>`;
        }
        return result;
    }).join('');
}

function renderNeuralReaction(nr) {
    if (!nr) return '';
    let html = '<div class="neural-reaction">';
    
    if (nr.core_conclusion) {
        html += '<div class="nr-section"><span class="nr-label">核心结论</span><span class="nr-text">' + processTextWithLatex(nr.core_conclusion) + '</span></div>';
    }
    
    const dims = nr.reaction_dimensions;
    if (dims) {
        if (dims['考点锚定反应']) {
            html += '<div class="nr-section"><span class="nr-label">考点锚定</span><span class="nr-text">' + processTextWithLatex(dims['考点锚定反应'].fixed_reaction) + '</span></div>';
        }
        
        if (dims['隐含信息解码反应'] && dims['隐含信息解码反应'].length > 0) {
            html += '<div class="nr-section"><span class="nr-label">隐含信息</span>';
            dims['隐含信息解码反应'].forEach(item => {
                html += '<div class="nr-text"><span class="nr-clue">' + processTextWithLatex(item.trigger_clue) + '</span> → ' + processTextWithLatex(item.fixed_reaction) + '</div>';
            });
            html += '</div>';
        }
        
        if (dims['易错陷阱预警反应'] && dims['易错陷阱预警反应'].length > 0) {
            html += '<div class="nr-section"><span class="nr-label">易错陷阱</span>';
            dims['易错陷阱预警反应'].forEach(trap => {
                html += '<div class="nr-text"><span class="nr-priority">' + trap.priority + '</span> ' + processTextWithLatex(trap.fixed_reaction);
                if (trap.example_application) {
                    html += ' <span style="color:#666;">例:' + processTextWithLatex(trap.example_application) + '</span>';
                }
                html += '</div>';
            });
            html += '</div>';
        }
        
        if (dims['正误判断标尺反应'] && dims['正误判断标尺反应'].length > 0) {
            html += '<div class="nr-section"><span class="nr-label">判断标尺</span>';
            dims['正误判断标尺反应'].forEach(ruler => {
                html += '<div class="nr-text"><span class="nr-ruler-name">[' + ruler.related_option + ']</span> ' + processTextWithLatex(ruler.fixed_standard) + '</div>';
            });
            html += '</div>';
        }
        
        if (dims['同类题迁移锚点反应']) {
            html += '<div class="nr-section"><span class="nr-label">迁移要点</span><span class="nr-text">' + processTextWithLatex(dims['同类题迁移锚点反应'].fixed_reaction) + '</span></div>';
        }
    }
    
    if (nr.core_quick_memory_pack && nr.core_quick_memory_pack.length > 0) {
        html += '<div class="nr-section"><span class="nr-label">速记要点</span>';
        html += '<div class="nr-text">' + nr.core_quick_memory_pack.map(item => '• ' + processTextWithLatex(item)).join('<br>') + '</div>';
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

function renderQuestionAnalysis(qa) {
    if (!qa) return '';
    let html = '<div class="question-analysis">';

    if (qa.question_basic_info) {
        const info = qa.question_basic_info;
        html += '<div class="qa-section"><span class="qa-section-title">题目基本信息</span>';
        if (info.question_type) html += '<div class="qa-text"><span class="qa-label">题型:</span> ' + processTextWithLatex(info.question_type) + '</div>';
        if (info.target_grade) html += '<div class="qa-text"><span class="qa-label">年级:</span> ' + processTextWithLatex(info.target_grade) + '</div>';
        if (info.core_examination_points) html += '<div class="qa-text"><span class="qa-label">考点:</span> ' + processTextWithLatex(info.core_examination_points) + '</div>';
        html += '</div>';
    }

    if (qa.module_1_basic_model_analysis) {
        const m1 = qa.module_1_basic_model_analysis;
        html += '<div class="qa-section"><span class="qa-section-title">基础模型分析</span>';
        if (m1.base_model_name) html += '<div class="qa-text"><span class="qa-label">模型:</span> ' + processTextWithLatex(m1.base_model_name) + '</div>';
        if (m1.standardized_scaffold) html += '<div class="qa-text"><span class="qa-label">解题支架:</span> ' + processTextWithLatex(m1.standardized_scaffold) + '</div>';
        if (m1.core_variation_points) html += '<div class="qa-text"><span class="qa-label">变式要点:</span> ' + processTextWithLatex(m1.core_variation_points) + '</div>';
        if (m1.suitable_practice_stage) html += '<div class="qa-text"><span class="qa-label">适用阶段:</span> ' + processTextWithLatex(m1.suitable_practice_stage) + '</div>';
        html += '</div>';
    }

    if (qa.module_2_student_trial_error_analysis && qa.module_2_student_trial_error_analysis.length > 0) {
        html += '<div class="qa-section"><span class="qa-section-title">学生试错分析</span>';
        qa.module_2_student_trial_error_analysis.forEach(item => {
            html += '<div class="qa-item">';
            html += '<span class="qa-priority">P' + escapeHtml(item.priority) + '</span>';
            if (item.student_thinking_process) html += '<div class="qa-text"><span class="qa-label">思维过程:</span> ' + processTextWithLatex(item.student_thinking_process) + '</div>';
            if (item.trial_error_breakpoint) html += '<div class="qa-text"><span class="qa-label">断点:</span> ' + processTextWithLatex(item.trial_error_breakpoint) + '</div>';
            if (item.knowledge_or_logic_gap) html += '<div class="qa-text"><span class="qa-label">知识缺口:</span> ' + processTextWithLatex(item.knowledge_or_logic_gap) + '</div>';
            if (item.neural_stimulus_warning) html += '<div class="qa-text"><span class="qa-label">预警:</span> ' + processTextWithLatex(item.neural_stimulus_warning) + '</div>';
            if (item.correction_key_action) html += '<div class="qa-text"><span class="qa-label">纠正:</span> ' + processTextWithLatex(item.correction_key_action) + '</div>';
            html += '</div>';
        });
        html += '</div>';
    }

    if (qa.module_3_multi_dimensional_solution_analysis) {
        const m3 = qa.module_3_multi_dimensional_solution_analysis;
        html += '<div class="qa-section"><span class="qa-section-title">多维解题分析</span>';

        if (m3.entry_level_must_learn) {
            html += '<div class="qa-item"><span class="qa-subsection-title">入门必学</span>';
            if (m3.entry_level_must_learn.solution_path) html += '<div class="qa-text">' + processTextWithLatex(m3.entry_level_must_learn.solution_path) + '</div>';
            if (m3.entry_level_must_learn.time_allocation_suggestion) html += '<div class="qa-text" style="color:#666;">' + processTextWithLatex(m3.entry_level_must_learn.time_allocation_suggestion) + '</div>';
            html += '</div>';
        }

        if (m3.basic_consolidation) {
            html += '<div class="qa-item"><span class="qa-subsection-title">基础巩固</span>';
            if (m3.basic_consolidation.solution_path) html += '<div class="qa-text">' + processTextWithLatex(m3.basic_consolidation.solution_path) + '</div>';
            html += '</div>';
        }

        if (m3.advanced_improvement) {
            html += '<div class="qa-item"><span class="qa-subsection-title">进阶提升</span>';
            if (m3.advanced_improvement.solution_path) html += '<div class="qa-text">' + processTextWithLatex(m3.advanced_improvement.solution_path) + '</div>';
            if (m3.advanced_improvement.applicable_boundary) html += '<div class="qa-text" style="color:#666;">适用边界: ' + processTextWithLatex(m3.advanced_improvement.applicable_boundary) + '</div>';
            html += '</div>';
        }
        html += '</div>';
    }

    if (qa.module_4_neural_stimulus_trigger_points) {
        const m4 = qa.module_4_neural_stimulus_trigger_points;
        html += '<div class="qa-section"><span class="qa-section-title">神经刺激触发点</span>';

        const triggerCategories = [
            { key: '考点锚定触发线索', title: '考点锚定' },
            { key: '隐藏信息解码触发线索', title: '隐藏信息解码' },
            { key: '易错坑点预警触发线索', title: '易错坑点预警' },
            { key: '同类题迁移触发线索', title: '同类题迁移' }
        ];

        triggerCategories.forEach(cat => {
            if (m4[cat.key] && m4[cat.key].length > 0) {
                html += '<div class="qa-item"><span class="qa-subsection-title">' + cat.title + '</span>';
                m4[cat.key].forEach(trigger => {
                    html += '<div class="qa-text"><span class="qa-trigger">' + processTextWithLatex(trigger.trigger_clue) + '</span> → <span class="qa-reaction">' + processTextWithLatex(trigger.fixed_reaction) + '</span></div>';
                });
                html += '</div>';
            }
        });
        html += '</div>';
    }

    html += '</div>';
    return html;
}

function renderImmersionThinking(it) {
    if (!it || it.length === 0) return '';
    let html = '<div class="immersion-thinking">';
    it.forEach((process, index) => {
        if (index > 0) {
            html += '<div style="border-top: 1px dashed #ccc; margin-top: 2mm; padding-top: 2mm;"></div>';
        }
        html += '<div class="it-header">';
        html += '<span class="it-label">沉浸式思考</span>';
        html += '</div>';
        html += '<div class="it-content">' + renderMarkdownWithLatex(process.thinking_content || process) + '</div>';
    });
    html += '</div>';
    return html;
}

function renderMathThinkingChain(mtc) {
    if (!mtc || mtc.length === 0) return '';
    let html = '<div class="math-thinking-chain">';
    mtc.forEach((item, index) => {
        if (index > 0) {
            html += '<div style="border-top: 1px dashed #ccc; margin-top: 2mm; padding-top: 2mm;"></div>';
        }
        html += '<div class="mtc-header">';
        html += '<span class="mtc-label">数学思维链</span>';
        if (item.target_label) {
            html += '<span class="mtc-target">' + escapeHtml(item.target_label) + '</span>';
        }
        html += '</div>';
        html += '<div class="mtc-content">' + renderMarkdownWithLatex(item.content || '') + '</div>';
    });
    html += '</div>';
    return html;
}

function renderThinkingProcesses(tp) {
    if (!tp || tp.length === 0) return '';
    let html = '<div class="thinking-process">';
    tp.forEach((process, index) => {
        if (index > 0) {
            html += '<div style="border-top: 1px dashed #ccc; margin-top: 2mm; padding-top: 2mm;"></div>';
        }
        html += '<div class="tp-header">';
        html += '<span class="tp-label">解题思考过程</span>';
        if (process.target_label && process.target_label !== '整个题目') {
            html += '<span class="tp-target">' + escapeHtml(process.target_label) + '</span>';
        }
        html += '</div>';
        html += '<div class="tp-content">' + renderMarkdownWithLatex(process.thinking_content) + '</div>';
    });
    html += '</div>';
    return html;
}

async function renderPreview() {
    const container = document.getElementById('printContainer');
    const selected = questions.filter(q => selectedIds.has(q.id));

    if (selected.length === 0) {
        container.innerHTML = '<div class="a4-page"><div class="no-data">请选择要打印的题目</div></div>';
        return;
    }

    const layoutMode = document.getElementById('layoutMode').value;
    const questionsPerPage = document.getElementById('questionsPerPage').value;
    
    let layout = 'single';
    if (layoutMode === 'double') {
        layout = 'double';
    } else if (layoutMode === 'auto') {
        const avgLen = selected.reduce((sum, q) => {
            const qLen = q.question?.items?.reduce((s, i) => s + (i.content?.length || i.fragments?.reduce((a, f) => a + (f.text?.length || 0), 0) || 0), 0) || 0;
            return sum + qLen;
        }, 0) / selected.length;
        layout = avgLen < 300 ? 'double' : 'single';
    }

    if (questionsPerPage !== 'auto') {
        const perPage = parseInt(questionsPerPage);
        const pages = [];
        for (let i = 0; i < selected.length; i += perPage) {
            pages.push(selected.slice(i, i + perPage));
        }
        
        const pagesHtml = [];
        for (let pageIndex = 0; pageIndex < pages.length; pageIndex++) {
            const pageQuestions = pages[pageIndex];
            const questionsHtml = [];
            for (const q of pageQuestions) {
                const questionHtml = await renderItemsInlineAsync(q.question?.items);
                if (isMathQuestion(q)) {
                    const mathProcessingHtml = renderMathProcessingResult(q.math_processing_result);
                    questionsHtml.push(`<div class="question-block"><div class="question-content"><span class="question-id">${q.id}</span>${questionHtml}</div>${mathProcessingHtml}</div>`);
                } else if (isChemistryQuestion(q)) {
                    const chemistryProcessingHtml = renderChemistryProcessingResult(q);
                    questionsHtml.push(`<div class="question-block"><div class="question-content"><span class="question-id">${q.id}</span>${questionHtml}</div>${chemistryProcessingHtml}</div>`);
                } else {
                    const answerHtml = q.answer?.items?.length > 0 ? await renderItemsInlineAsync(q.answer.items) : '';
                    questionsHtml.push(`<div class="question-block"><div class="question-content"><span class="question-id">${q.id}</span>${questionHtml}</div>${renderNeuralReaction(q.neural_reaction)}${renderQuestionAnalysis(q.question_analysis)}${renderThinkingProcesses(q.thinking_processes)}${renderImmersionThinking(q.immersion_thinking)}${renderMathThinkingChain(q.math_thinking_chain)}${q.answer?.items?.length > 0 ? `<div class="answer-block"><span class="answer-header">答案:</span><span class="answer-content">${answerHtml}</span></div>` : ''}</div>`);
                }
            }
            pagesHtml.push(`<div class="a4-page">
<div class="page-header"><div class="page-title">错题练习</div><div class="page-info">第 ${pageIndex + 1} 页 / 共 ${pages.length} 页</div></div>
<div class="questions-grid ${layout === 'double' ? 'double-column' : 'single-column'}">
${questionsHtml.join('')}
</div>
</div>`);
        }
        container.innerHTML = pagesHtml.join('');
    } else {
        const questionsHtml = [];
        for (const q of selected) {
            const questionHtml = await renderItemsInlineAsync(q.question?.items);
            if (isMathQuestion(q)) {
                const mathProcessingHtml = renderMathProcessingResult(q.math_processing_result);
                questionsHtml.push(`<div class="question-block"><div class="question-content"><span class="question-id">${q.id}</span>${questionHtml}</div>${mathProcessingHtml}</div>`);
            } else if (isChemistryQuestion(q)) {
                const chemistryProcessingHtml = renderChemistryProcessingResult(q);
                questionsHtml.push(`<div class="question-block"><div class="question-content"><span class="question-id">${q.id}</span>${questionHtml}</div>${chemistryProcessingHtml}</div>`);
            } else {
                const answerHtml = q.answer?.items?.length > 0 ? await renderItemsInlineAsync(q.answer.items) : '';
                questionsHtml.push(`<div class="question-block"><div class="question-content"><span class="question-id">${q.id}</span>${questionHtml}</div>${renderNeuralReaction(q.neural_reaction)}${renderQuestionAnalysis(q.question_analysis)}${renderThinkingProcesses(q.thinking_processes)}${renderImmersionThinking(q.immersion_thinking)}${renderMathThinkingChain(q.math_thinking_chain)}${q.answer?.items?.length > 0 ? `<div class="answer-block"><span class="answer-header">答案:</span><span class="answer-content">${answerHtml}</span></div>` : ''}</div>`);
            }
        }
        container.innerHTML = `
<div class="print-content ${layout === 'double' ? 'double-column' : ''}">
${questionsHtml.join('')}
</div>
`;
    }
}

async function generatePreview() {
    if (selectedIds.size === 0) {
        alert('请先选择要打印的题目');
        return;
    }
    await renderPreview();
}

function printSelected() {
    if (selectedIds.size === 0) {
        alert('请先选择要打印的题目');
        return;
    }
    window.print();
}

function isMathQuestion(q) {
    return q.tags && Array.isArray(q.tags) && q.tags.includes('数学');
}

function isChemistryQuestion(q) {
    return q.tags && Array.isArray(q.tags) && q.tags.includes('化学');
}

function renderAccumulation(accumulations) {
    if (!accumulations || !Array.isArray(accumulations) || accumulations.length === 0) return '';
    let html = '<div class="accumulation-section">';
    html += '<div class="accumulation-title">积累训练</div>';
    accumulations.forEach((item, index) => {
        html += '<div class="accumulation-item">';
        html += '<div class="accumulation-tags">';
        if (item.ExerciseType) {
            html += '<span class="accumulation-tag">' + escapeHtml(item.ExerciseType) + '</span>';
        }
        if (item.ExamTag) {
            html += '<span class="accumulation-tag">' + escapeHtml(item.ExamTag) + '</span>';
        }
        if (item.AdaptScore) {
            html += '<span class="accumulation-tag">' + escapeHtml(item.AdaptScore) + '</span>';
        }
        html += '</div>';
        if (item.ExerciseContent) {
            html += '<div class="accumulation-content">' + processTextWithLatex(item.ExerciseContent) + '</div>';
        }
        if (item.AnswerAnalysis) {
            html += '<div class="accumulation-answer">' + processTextWithLatex(item.AnswerAnalysis) + '</div>';
        }
        html += '</div>';
    });
    html += '</div>';
    return html;
}

function renderDifficultyTeaching(q) {
    if (!q.difficulty_teaching || !q.selected_difficulty_ids || !Array.isArray(q.selected_difficulty_ids) || q.selected_difficulty_ids.length === 0) {
        return '';
    }
    const difficulties = q.chemistry_preprocessing?.Difficulties || [];
    const difficultyMap = {};
    difficulties.forEach(d => {
        difficultyMap[d.DifficultyID] = d.DifficultyName;
    });
    
    let html = '<div class="difficulty-teaching-wrapper">';
    html += '<div class="difficulty-teaching-columns">';
    q.selected_difficulty_ids.forEach((id) => {
        const teachingContent = q.difficulty_teaching[String(id)];
        const difficultyName = difficultyMap[id];
        if (teachingContent) {
            html += '<div class="difficulty-teaching-item">';
            if (difficultyName) {
                html += '<div class="difficulty-teaching-title">' + escapeHtml(difficultyName) + '</div>';
            }
            html += '<div class="difficulty-teaching-content">' + renderMarkdownWithLatex(teachingContent) + '</div>';
            html += '</div>';
        }
    });
    html += '</div></div>';
    return html;
}

function renderChemistryProcessingResult(q) {
    if (!q.chemistry_preprocessing && !q.difficulty_teaching) return '';
    let html = '<div class="chemistry-processing">';
    if (q.chemistry_preprocessing?.Accumulation) {
        html += renderAccumulation(q.chemistry_preprocessing.Accumulation);
    }
    html += renderDifficultyTeaching(q);
    html += '</div>';
    return html;
}

function renderMathProcessingResult(mpr) {
    if (!mpr || !Array.isArray(mpr) || mpr.length === 0) return '';
    let html = '<div class="math-processing">';
    mpr.forEach((unit, index) => {
        if (unit.classify_result === '套路知识类') {
            html += renderRoutineKnowledge(unit, index);
        } else if (unit.classify_result === '思维提升类') {
            html += renderThinkingImprovement(unit, index);
        }
    });
    html += '</div>';
    return html;
}

function renderRoutineKnowledge(unit, index) {
    let html = '<div class="math-unit">';
    html += '<div class="math-unit-title">训练单元 ' + (index + 1) + '：套路知识类</div>';
    html += '<div class="math-unit-content">' + processTextWithLatex(unit.unit_content || '') + '</div>';
    
    if (unit.pre_process && Array.isArray(unit.pre_process)) {
        unit.pre_process.forEach(train => {
            if (train.train_type === '套路反射训练') {
                html += renderRoutineReflection(train);
            } else if (train.train_type === '知识易错训练') {
                html += renderKnowledgeErrorTraining(train);
            }
        });
    }
    html += '</div>';
    return html;
}

function renderRoutineReflection(train) {
    let html = '<div class="train-item">';
    html += '<div class="train-question"><strong>问题：</strong>' + processTextWithLatex(train.question || '') + '</div>';
    html += '<div class="train-answer"><strong>答案：</strong>' + processTextWithLatex(train.standard_answer || '') + '</div>';
    html += '</div>';
    return html;
}

function renderKnowledgeErrorTraining(train) {
    let formTag = train.train_form === '判断题' ? '判断题' : '填空题';
    
    let html = '<div class="train-item">';
    html += '<span class="train-form-tag">' + formTag + '</span>';
    html += '<div class="train-question">' + processTextWithLatex(train.train_content || '') + '</div>';
    html += '<div class="train-answer">' + processTextWithLatex(train.answer || '') + '</div>';
    html += '</div>';
    return html;
}

function renderThinkingImprovement(unit, index) {
    let html = '<div class="thinking-improvement">';
    html += '<div class="thinking-improvement-title">训练单元 ' + (index + 1) + '：思维提升类</div>';
    html += '<div class="math-unit-content">' + processTextWithLatex(unit.unit_content || '') + '</div>';
    if (unit.pre_process) {
        html += '<div class="thinking-improvement-content">' + renderMarkdownWithLatex(unit.pre_process) + '</div>';
    }
    html += '</div>';
    return html;
}

loadQuestions();