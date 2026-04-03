/**
 * @typedef {Object} TextItem
 * @property {string} type - 'text' or 'richtext'
 * @property {string} content - Text content
 * @property {Array<{text: string, underline: boolean}>} [fragments] - Richtext fragments
 */

/**
 * @typedef {Object} ImageItem
 * @property {string} type - 'image'
 * @property {string} src - Image source URL
 * @property {string} [base64] - Base64 encoded image data
 * @property {string} display - Display mode: 'center', 'float-left', 'float-right'
 * @property {number} width - Image width in pixels
 * @property {number|string} height - Image height in pixels or 'auto'
 * @property {string} [image_id] - Image ID
 * @property {string} [config_id] - Config ID
 * @property {Object} [charBox] - Character box annotation
 * @property {Array} [splitLines] - Split lines data
 */

/**
 * @typedef {TextItem|ImageItem} ContentItem
 */

const Utils = {
    /**
     * Escape HTML special characters and convert newlines to <br>
     * @param {string} text - Text to escape
     * @returns {string} Escaped HTML string
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    },

    /**
     * Render LaTeX formulas in text using KaTeX
     * @param {string} text - Text containing LaTeX formulas
     * @returns {string} HTML string with rendered formulas
     */
    renderLatex(text) {
        if (!text || typeof text !== 'string') return text;
        
        if (typeof katex === 'undefined') {
            return text;
        }
        
        let result = text;
        
        result = result.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
            try {
                return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
            } catch (e) {
                return match;
            }
        });
        
        result = result.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
            try {
                return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
            } catch (e) {
                return match;
            }
        });
        
        result = result.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
            try {
                return katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false });
            } catch (e) {
                return match;
            }
        });
        
        result = result.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
            try {
                return katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
            } catch (e) {
                return match;
            }
        });
        
        return result;
    },

    /**
     * Process text with LaTeX formulas
     * @param {string} text - Text to process
     * @returns {string} Processed HTML string
     */
    processTextWithLatex(text) {
        if (!text) return '';
        const escaped = this.escapeHtml(text);
        const withBreaks = escaped.replace(/\r\n/g, '<br>').replace(/\n/g, '<br>').replace(/\r/g, '<br>');
        return this.renderLatex(withBreaks);
    },

    /**
     * Render richtext fragments to HTML
     * @param {Array<{text: string, underline: boolean}>} fragments - Richtext fragments
     * @returns {string} HTML string
     */
    renderRichtext(fragments) {
        let html = '';
        for (const frag of fragments) {
            let text = frag.text;
            let isUnderline = frag.underline;
            
            if (isUnderline) {
                text = text.replace(/\u3000/g, ' ');
                text = text.replace(/ /g, '_');
            }
            const escaped = this.escapeHtml(text);
            
            if (!isUnderline) {
                const withLatex = this.renderLatex(escaped);
                const withBreaks = withLatex.replace(/\r\n/g, '<br>').replace(/\n/g, '<br>').replace(/\r/g, '<br>');
                html += withBreaks;
            } else {
                const withLatex = this.renderLatex(escaped);
                const withBreaks = withLatex.replace(/\r\n/g, '<br>').replace(/\n/g, '<br>').replace(/\r/g, '<br>');
                html += '<span class="underline-space">' + withBreaks + '</span>';
            }
        }
        return html;
    },

    /**
     * Clean image item by removing temporary properties
     * @param {ImageItem} item - Image item to clean
     * @returns {ImageItem} Cleaned image item
     */
    cleanImageItem(item) {
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
    },

    /**
     * Clean array of content items
     * @param {Array<ContentItem>} items - Items to clean
     * @returns {Array<ContentItem>} Cleaned items
     */
    cleanItems(items) {
        return items.map(item => {
            if (item.type === 'image') {
                return this.cleanImageItem(item);
            } else if (item.type === 'richtext') {
                return {
                    type: 'richtext',
                    content: item.content,
                    fragments: item.fragments
                };
            }
            return { ...item };
        });
    }
};
