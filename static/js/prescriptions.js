/* ===== 方剂管理页面 ===== */
const PrescriptionsPage = {
    page: 1,
    pageSize: 10,
    search: '',
    efficacy: '',

    async load() {
        try {
            const result = await API.getPrescriptions({
                search: this.search,
                efficacy: this.efficacy,
                page: this.page,
                page_size: this.pageSize
            });
            this.renderTable(result.items);
            Pagination.render('pres-pagination', result.total, result.page, result.page_size, function(p) {
                PrescriptionsPage.page = p;
                PrescriptionsPage.load();
            });
        } catch (e) {
            Toast.show('加载方剂失败: ' + e.message, 'error');
        }
    },

    renderTable(items) {
        const tbody = document.querySelector('#pres-table tbody');
        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:32px;">暂无数据</td></tr>';
            return;
        }
        let html = '';
        items.forEach(function(p) {
            let herbTags = '';
            if (p.herbs && p.herbs.length > 0) {
                p.herbs.slice(0, 5).forEach(function(h) {
                    herbTags += '<span class="herb-tag">' + Utils.escapeHtml(h.name) + (h.dosage ? ' ' + Utils.escapeHtml(h.dosage) : '') + '</span>';
                });
                if (p.herbs.length > 5) herbTags += '<span class="herb-tag" style="opacity:0.6">+' + (p.herbs.length - 5) + '</span>';
            }
            html += '<tr>';
            html += '<td>' + Utils.escapeHtml(p.id) + '</td>';
            html += '<td><strong>' + Utils.escapeHtml(p.name) + '</strong></td>';
            html += '<td>' + Utils.truncate(p.efficacy, 30) + '</td>';
            html += '<td>' + Utils.truncate(p.source, 20) + '</td>';
            html += '<td>' + (herbTags || '-') + '</td>';
            html += '<td class="actions">';
            html += '<button class="btn-icon" title="查看详情" onclick="PrescriptionsPage.viewDetail(\'' + Utils.escapeHtml(p.id) + '\')">&#128065;</button>';
            html += '</td>';
            html += '</tr>';
        });
        tbody.innerHTML = html;
    },

    async viewDetail(id) {
        try {
            const result = await API.getPrescription(id);
            const p = result.data;
            let html = '<div class="form-row">';
            html += '<div><label>方剂名称</label><p><strong>' + Utils.escapeHtml(p.name) + '</strong></p></div>';
            html += '<div><label>ID</label><p>' + Utils.escapeHtml(p.id) + '</p></div>';
            html += '</div><div class="form-row">';
            html += '<div><label>功效</label><p>' + Utils.escapeHtml(p.efficacy) + '</p></div>';
            html += '<div><label>出处</label><p>' + Utils.escapeHtml(p.source) + '</p></div>';
            html += '</div>';
            if (p.category) {
                html += '<div><label>分类</label><p>' + Utils.escapeHtml(p.category) + '</p></div>';
            }
            if (p.indications) {
                html += '<div><label>主治</label><p>' + Utils.escapeHtml(p.indications) + '</p></div>';
            }
            html += '<div style="margin-top:16px;"><label>组成药材</label>';
            if (p.herbs && p.herbs.length > 0) {
                p.herbs.forEach(function(h) {
                    html += '<span class="herb-tag">' + Utils.escapeHtml(h.name) + (h.dosage ? ' ' + Utils.escapeHtml(h.dosage) : '') + '</span> ';
                });
            } else {
                html += '<span style="color:var(--text-muted)">无</span>';
            }
            html += '</div>';
            Modal.open('方剂详情 - ' + p.name, html);
        } catch (e) {
            Toast.show('加载详情失败: ' + e.message, 'error');
        }
    },

    init() {
        const searchInput = document.getElementById('pres-search');
        if (searchInput) {
            searchInput.addEventListener('input', Utils.debounce(function() {
                PrescriptionsPage.search = searchInput.value;
                PrescriptionsPage.page = 1;
                PrescriptionsPage.load();
            }, 300));
        }
    }
};