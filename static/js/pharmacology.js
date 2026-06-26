/* ===== 药理学页面 ===== */
const PharmacologyPage = {
    page: 1,
    pageSize: 10,
    search: '',

    async load() {
        try {
            const result = await API.getPharmacologyList({
                search: this.search,
                page: this.page,
                page_size: this.pageSize
            });
            this.renderTable(result.items);
            Pagination.render('pharm-pagination', result.total, result.page, result.page_size, function(p) {
                PharmacologyPage.page = p;
                PharmacologyPage.load();
            });
        } catch (e) {
            Toast.show('加载药理学数据失败: ' + e.message, 'error');
        }
    },

    renderTable(items) {
        const tbody = document.querySelector('#pharm-table tbody');
        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:32px;">暂无数据</td></tr>';
            return;
        }
        let html = '';
        items.forEach(function(p) {
            html += '<tr>';
            html += '<td>' + Utils.escapeHtml(p.id) + '</td>';
            html += '<td><strong>' + Utils.escapeHtml(p.name) + '</strong></td>';
            html += '<td>' + (p.herb_count || '-') + '</td>';
            html += '<td class="actions">';
            html += '<button class="btn-icon" title="查看详情" onclick="PharmacologyPage.viewDetail(\'' + Utils.escapeHtml(p.id) + '\')">&#128065;</button>';
            html += '</td>';
            html += '</tr>';
        });
        tbody.innerHTML = html;
    },

    async viewDetail(id) {
        try {
            const result = await API.getPharmacology(id);
            const p = result.data;
            let html = '<div><label>名称</label><p><strong>' + Utils.escapeHtml(p.name) + '</strong></p></div>';
            html += '<div><label>ID</label><p>' + Utils.escapeHtml(p.id) + '</p></div>';
            
            if (p.herbs && p.herbs.length > 0) {
                html += '<div style="margin-top:16px;"><label>关联药材 (' + p.herbs.length + ')</label><div style="max-height:200px;overflow-y:auto;">';
                p.herbs.forEach(function(h) {
                    html += '<span class="herb-tag">' + Utils.escapeHtml(h.name) + '</span> ';
                });
                html += '</div></div>';
            }
            if (p.ingredients && p.ingredients.length > 0) {
                html += '<div style="margin-top:16px;"><label>关联成分 (' + p.ingredients.length + ')</label><div style="max-height:200px;overflow-y:auto;">';
                p.ingredients.forEach(function(ing) {
                    html += '<span class="herb-tag">' + Utils.escapeHtml(ing.name) + '</span> ';
                });
                html += '</div></div>';
            }
            Modal.open('药理学详情 - ' + p.name, html);
        } catch (e) {
            Toast.show('加载详情失败: ' + e.message, 'error');
        }
    },

    init() {
        const searchInput = document.getElementById('pharm-search');
        if (searchInput) {
            searchInput.addEventListener('input', Utils.debounce(function() {
                PharmacologyPage.search = searchInput.value;
                PharmacologyPage.page = 1;
                PharmacologyPage.load();
            }, 300));
        }
    }
};
