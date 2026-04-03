/**
 * Image handling utilities
 * @namespace ImageHandler
 */
const ImageHandler = {
    /**
     * Handle image paste event
     * @async
     * @param {File} file - Image file
     * @param {Object} callbacks - Callback functions
     * @param {Function} callbacks.getItemId - Function to get unique item ID
     * @param {Function} callbacks.onSuccess - Function called on success with new item
     * @param {Function} [callbacks.onError] - Function called on error
     */
    async handleImagePaste(file, callbacks) {
        if (!file) return;

        try {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const base64 = e.target.result;

                const result = await API.uploadImage(base64);

                if (result.success) {
                    const newItem = {
                        id: callbacks.getItemId(),
                        type: 'image',
                        image_id: result.image_id,
                        config_id: null,
                        src: result.path,
                        display: 'center',
                        width: 300,
                        height: 'auto',
                        base64: base64
                    };
                    callbacks.onSuccess(newItem);
                } else {
                    callbacks.onError?.('图片上传失败: ' + result.error);
                }
            };
            reader.readAsDataURL(file);
        } catch (error) {
            callbacks.onError?.('图片上传失败: ' + error.message);
        }
    },

    /**
     * Update image display mode
     * @param {number} index - Item index
     * @param {string} display - Display mode: 'center', 'float-left', 'float-right'
     * @param {Array} items - Items array
     * @param {Function} setItems - Function to update items
     */
    updateImageDisplay(index, display, items, setItems) {
        items[index].display = display;
        setItems(items);
    },

    /**
     * Update image size
     * @param {number} index - Item index
     * @param {string} dimension - 'width' or 'height'
     * @param {string|number} value - New size value
     * @param {Array} items - Items array
     * @param {Function} setItems - Function to update items
     */
    updateImageSize(index, dimension, value, items, setItems) {
        items[index][dimension] = value === '' ? 'auto' : parseInt(value) || 300;
        setItems(items);
    },

    /**
     * Normalize image source URL
     * @param {string} src - Image source
     * @param {string} [base64] - Base64 data
     * @returns {string} Normalized URL
     */
    normalizeImageSrc(src, base64) {
        if (base64) return base64;
        if (!src) return '';
        if (src.startsWith('http')) return src;
        if (src.startsWith('/')) return src;
        return '/' + src;
    },

    /**
     * Load split image parts
     * @async
     * @param {string} src - Image source
     * @param {Array} splitLines - Split line positions
     * @param {number} width - Image width
     * @returns {Promise<Array<{src: string, width: number}>>}
     */
    async loadSplitImageParts(src, splitLines, width) {
        if (!splitLines || splitLines.length === 0) {
            return [{ src: src, width: width }];
        }

        const result = await API.splitImage({
            src: src,
            splitLines: splitLines,
            width: width
        });

        if (result.success) {
            return result.parts;
        }
        return [{ src: src, width: width }];
    }
};
