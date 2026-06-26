/* ===== API 调用封装 ===== */
const API = {
    baseUrl: '',
    pendingRequests: 0,

    async request(method, url, data) {
        this.pendingRequests++;
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json' }
            };
            if (data && method !== 'GET') {
                options.body = JSON.stringify(data);
            }
            const response = await fetch(this.baseUrl + url, options);
            
            if (!response.ok) {
                let errorMessage = '请求失败';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = 'HTTP ' + response.status + ': ' + response.statusText;
                }
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || '请求失败');
            }
            return result;
        } finally {
            this.pendingRequests--;
        }
    },

    get(url) { return this.request('GET', url); },
    post(url, data) { return this.request('POST', url, data); },
    put(url, data) { return this.request('PUT', url, data); },
    del(url) { return this.request('DELETE', url); },

    // 上传文件
    async uploadFile(formData) {
        const response = await fetch(this.baseUrl + '/api/import/preview', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || '上传失败');
        }
        return result;
    },

    async confirmImport(data) {
        return this.post('/api/import/confirm', data);
    },

    async getStats() {
        return this.get('/api/stats');
    },

    // 药材
    async getHerbs(params) {
        const qs = new URLSearchParams(params).toString();
        return this.get('/api/herbs?' + qs);
    },
    async getHerb(id) { return this.get('/api/herbs/' + id); },
    async getAllHerbsSimple() { return this.get('/api/herbs/all'); },

    // 方剂
    async getPrescriptions(params) {
        const qs = new URLSearchParams(params).toString();
        return this.get('/api/prescriptions?' + qs);
    },
    async getPrescription(id) { return this.get('/api/prescriptions/' + id); },

    // 药理学
    async getPharmacologyList(params) {
        const qs = new URLSearchParams(params).toString();
        return this.get('/api/pharmacology?' + qs);
    },
    async getPharmacology(id) { return this.get('/api/pharmacology/' + id); },

    // 成分
    async getComponents(params) {
        const qs = new URLSearchParams(params).toString();
        return this.get('/api/components?' + qs);
    },
    async getComponent(id) { return this.get('/api/components/' + id); },

    // 病症
    async getDiseases(params) {
        const qs = new URLSearchParams(params).toString();
        return this.get('/api/diseases?' + qs);
    },
    async getDisease(id) { return this.get('/api/diseases/' + id); },

    // QA
    async qaSearch(question, model) {
        return this.post('/api/qa/search', { question, model });
    },
    async qaHistory(limit) {
        return this.get('/api/qa/history?limit=' + limit);
    },
    async qaRate(qa_id, rating, feedback) {
        return this.post('/api/qa/rate', { qa_id, rating, feedback });
    },
};