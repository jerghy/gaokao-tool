/**
 * Content rendering utilities
 * @namespace ContentRenderer
 */
const ContentRenderer = {
    /**
     * Render a text item element
     * @param {import('./utils.js').TextItem} item - Text item
     * @param {number} index - Item index
     * @param {Object} callbacks - Callback functions
     * @returns {HTMLDivElement}
     */
    renderTextItem(item, index, callbacks) {
        const div = document.createElement('div');
        div.className = 'text-item';
        const content = item.type === 'richtext' 
            ? Utils.renderRichtext(item.fragments) 
            : Utils.escapeHtml(item.content);
        div.innerHTML = `
            <div class="text-item-content" ondblclick="callbacks?.onEdit?.(${index})">${content}</div>
            <button class="delete-btn" onclick="callbacks?.onDelete?.(${index}, 'text')">删除</button>
        `;
        return div;
    },

    /**
     * Render an image item element
     * @param {import('./utils.js').ImageItem} item - Image item
     * @param {number} index - Item index
     * @param {Object} callbacks - Callback functions
     * @returns {HTMLDivElement}
     */
    renderImageItem(item, index, callbacks) {
        const div = document.createElement('div');
        div.className = 'image-card';
        const imgSrc = ImageHandler.normalizeImageSrc(item.src, item.base64);
        const hasCharBox = item.charBox ? true : false;
        div.innerHTML = `
            <img src="${imgSrc}" class="image-preview" alt="图片">
            <div class="image-controls">
                <label>显示方式:</label>
                <select onchange="callbacks?.onDisplayChange?.(${index}, this.value)">
                    <option value="center" ${item.display === 'center' ? 'selected' : ''}>居中显示</option>
                    <option value="float-left" ${item.display === 'float-left' ? 'selected' : ''}>文字环绕(左)</option>
                    <option value="float-right" ${item.display === 'float-right' ? 'selected' : ''}>文字环绕(右)</option>
                </select>
                <label>宽度:</label>
                <input type="number" value="${item.width || 300}" onchange="callbacks?.onSizeChange?.(${index}, 'width', this.value)">
                <label>高度:</label>
                <input type="number" value="${item.height === 'auto' ? '' : item.height}" onchange="callbacks?.onSizeChange?.(${index}, 'height', this.value)" placeholder="自动">
                <button class="char-box-btn-annotate ${hasCharBox ? 'has-box' : ''}" onclick="callbacks?.onCharBox?.(${index})">${hasCharBox ? '已标注' : '标注字框'}</button>
                <button class="delete-btn" onclick="callbacks?.onDelete?.(${index}, 'image')">删除</button>
            </div>
        `;
        return div;
    },

    /**
     * Render content list to container
     * @param {HTMLElement} container - Container element
     * @param {Array<import('./utils.js').ContentItem>} items - Content items
     * @param {Object} callbacks - Callback functions
     */
    renderContentList(container, items, callbacks) {
        const addTextBtn = container.querySelector('.add-text-btn');
        container.innerHTML = '';

        items.forEach((item, index) => {
            let element;
            if (item.type === 'text' || item.type === 'richtext') {
                element = this.renderTextItem(item, index, callbacks);
            } else if (item.type === 'image') {
                element = this.renderImageItem(item, index, callbacks);
            }
            if (element) {
                container.appendChild(element);
            }
        });

        if (addTextBtn) {
            container.appendChild(addTextBtn);
        }
    },

    /**
     * Render a tag item element
     * @param {string} tag - Tag text
     * @param {Function} onRemove - Remove callback
     * @returns {HTMLSpanElement}
     */
    renderTagItem(tag, onRemove) {
        const span = document.createElement('span');
        span.className = 'tag-item';
        span.innerHTML = `
            ${Utils.escapeHtml(tag)}
            <span class="tag-remove" onclick="(${onRemove})('${tag}')">×</span>
        `;
        return span;
    },

    /**
     * Render tags to container
     * @param {HTMLElement} container - Container element
     * @param {Array<string>} tags - Tags array
     * @param {Function} onRemove - Remove callback
     */
    renderTags(container, tags, onRemove) {
        container.innerHTML = '';
        tags.forEach(tag => {
            const tagElement = this.renderTagItem(tag, onRemove);
            container.appendChild(tagElement);
        });
    },

    /**
     * Render a preview item element
     * @param {import('./utils.js').ContentItem} item - Content item
     * @returns {HTMLElement|null}
     */
    renderPreviewItem(item) {
        if (item.type === 'text') {
            const div = document.createElement('div');
            div.className = 'preview-text';
            div.innerHTML = Utils.processTextWithLatex(item.content);
            return div;
        } else if (item.type === 'richtext') {
            const div = document.createElement('div');
            div.className = 'preview-text';
            div.innerHTML = Utils.renderRichtext(item.fragments);
            return div;
        } else if (item.type === 'image') {
            const img = document.createElement('img');
            img.src = ImageHandler.normalizeImageSrc(item.src, item.base64);
            img.style.width = item.width + 'px';
            if (item.height !== 'auto') {
                img.style.height = item.height + 'px';
            }
            img.className = 'preview-image';
            return img;
        }
        return null;
    },

    /**
     * Render preview to container
     * @param {HTMLElement} container - Container element
     * @param {Array<import('./utils.js').ContentItem>} items - Content items
     */
    renderPreview(container, items) {
        container.innerHTML = '';
        items.forEach(item => {
            const element = this.renderPreviewItem(item);
            if (element) {
                container.appendChild(element);
            }
        });
    }
};
