# 修复 Markdown 与 LaTeX 渲染冲突计划

## 问题诊断

### 根本原因
当前代码在渲染包含 LaTeX 公式的 Markdown 内容时，处理顺序错误：
1. **先** 调用 `marked.parse()` 渲染 Markdown
2. **后** 调用 `renderMathInElement()` 渲染 LaTeX

这导致 Markdown 解析器会错误地处理 LaTeX 公式中的特殊字符：
- `$x_i$` 中的 `_` 被 Markdown 解释为斜体标记，变成 `<em>x</em>i$`
- 公式边界被破坏，LaTeX 无法正确渲染

### 受影响的函数
| 函数名 | 行号 | 问题代码 |
|--------|------|----------|
| `renderThinkingProcesses` | 1884 | `marked.parse(process.thinking_content)` |
| `renderImmersionThinking` | 1830 | `marked.parse(process.thinking_content \|\| process)` |
| `renderMathThinkingChain` | 1849 | `marked.parse((item.content \|\| '').replace(/\n/g, '<br>'))` |

## 解决方案

### 核心思路：占位符替换法
1. **提取 LaTeX 公式**：在 Markdown 渲染前，识别并提取所有 LaTeX 公式
2. **替换为占位符**：用唯一占位符替换公式位置
3. **渲染 Markdown**：对不含公式的文本进行 Markdown 渲染
4. **还原 LaTeX**：将占位符替换回已渲染的 LaTeX HTML

### 实现步骤

#### 步骤 1：创建 LaTeX 保护函数
新增 `protectLatexInMarkdown(text)` 函数：
```javascript
function protectLatexInMarkdown(text) {
    const placeholders = [];
    
    // 保护 $$...$$ (display mode)
    text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
        const index = placeholders.length;
        placeholders.push(katex.renderToString(formula.trim(), { 
            displayMode: true, 
            throwOnError: false, 
            trust: true 
        }));
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    // 保护 \[...\] (display mode)
    text = text.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
        const index = placeholders.length;
        placeholders.push(katex.renderToString(formula.trim(), { 
            displayMode: true, 
            throwOnError: false, 
            trust: true 
        }));
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    // 保护 $...$ (inline mode) - 注意避免匹配 $$
    text = text.replace(/(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)/g, (match, formula) => {
        const index = placeholders.length;
        placeholders.push(katex.renderToString(formula.trim(), { 
            displayMode: false, 
            throwOnError: false, 
            trust: true 
        }));
        return `%%LATEX_PLACEHOLDER_${index}%%`;
    });
    
    // 保护 \(...\) (inline mode)
    text = text.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
        const index = placeholders.length;
        placeholders.push(katex.renderToString(formula.trim(), { 
            displayMode: false, 
            throwOnError: false, 
            trust: true 
        }));
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
```

#### 步骤 2：创建统一的 Markdown+LaTeX 渲染函数
新增 `renderMarkdownWithLatex(content)` 函数：
```javascript
function renderMarkdownWithLatex(content) {
    if (!content) return '';
    
    // 1. 保护 LaTeX 公式
    const { text: protectedText, placeholders } = protectLatexInMarkdown(content);
    
    // 2. 渲染 Markdown
    let html = marked.parse(protectedText);
    
    // 3. 还原 LaTeX
    html = restoreLatexFromPlaceholders(html, placeholders);
    
    return html;
}
```

#### 步骤 3：修改三个受影响的函数

**修改 `renderThinkingProcesses`**（第 1871-1904 行）：
```javascript
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
```

**修改 `renderImmersionThinking`**（第 1820-1834 行）：
```javascript
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
```

**修改 `renderMathThinkingChain`**（第 1836-1869 行）：
```javascript
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
```

#### 步骤 4：清理冗余代码
- 移除 `renderPreview` 函数末尾的 `renderMathInElement` 调用（第 1966-1982 行），因为 LaTeX 已在 Markdown 渲染时处理
- 移除 `renderThinkingProcesses` 和 `renderMathThinkingChain` 中的 `renderMathInElement` 调用

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `d:\space\html\print\static\print.html` | 新增函数、修改现有函数、移除冗余代码 |

## 预期效果

修复后：
- `$x_i$` 将正确渲染为数学公式（下标），而不会被 Markdown 解释为斜体
- Markdown 语法（标题、列表、粗体等）继续正常工作
- LaTeX 公式（行内和块级）正确渲染
