/**
 * API module for backend communication
 * @namespace API
 */
var API = {
    BASE_URL: window.location.origin,
    _version: '1.0.1-' + Date.now(),

    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.error && !data.success) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
                throw new Error('网络连接失败，请检查服务器是否运行');
            }
            throw error;
        }
    },

    async uploadImage(base64) {
        return this.request(`${this.BASE_URL}/api/upload-image`, {
            method: 'POST',
            body: JSON.stringify({ image: base64 })
        });
    },

    async saveQuestion(data) {
        return this.request(`${this.BASE_URL}/api/save`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async getQuestions(params = {}) {
        const filteredParams = Object.fromEntries(
            Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '')
        );
        const query = new URLSearchParams(filteredParams).toString();
        const url = `${this.BASE_URL}/api/questions${query ? '?' + query : ''}`;
        return this.request(url);
    },

    async updateQuestion(id, data) {
        return this.request(`${this.BASE_URL}/api/questions/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async deleteQuestion(id) {
        return this.request(`${this.BASE_URL}/api/questions/${id}`, {
            method: 'DELETE'
        });
    },

    async getTags() {
        return this.request(`${this.BASE_URL}/api/tags`);
    },

    async batchAddTag(recordIds, tag) {
        return this.request(`${this.BASE_URL}/api/questions/batch-add-tag`, {
            method: 'POST',
            body: JSON.stringify({ record_ids: recordIds, tag: tag })
        });
    },

    async splitImage(data) {
        return this.request(`${this.BASE_URL}/api/split-image`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async checkScreenshot() {
        return this.request(`${this.BASE_URL}/api/screenshot/check`);
    },

    async consumeScreenshot(screenshotId) {
        return this.request(`${this.BASE_URL}/api/screenshot/consume/${screenshotId}`, {
            method: 'POST'
        });
    },

    async uploadScreenshot(base64) {
        return this.request(`${this.BASE_URL}/api/screenshot/upload`, {
            method: 'POST',
            body: JSON.stringify({ image: base64 })
        });
    },

    async getImages() {
        return this.request(`${this.BASE_URL}/api/images`);
    },

    async getImageConfig(configId) {
        return this.request(`${this.BASE_URL}/api/images/${configId}`);
    }
};

console.log('API module loaded successfully, version:', API._version);
