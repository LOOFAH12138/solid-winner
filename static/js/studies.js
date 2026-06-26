/* ===== 药理研究管理页面 ===== */
const StudiesPage = {
    page: 1,
    pageSize: 10,
    search: '',
    herbId: '',

    async load() {
        try {
            const result = await API.getStudies({
                search: this.search,
                herb_id: this.herbId,
                page: this.page,
                page_size: this.pageSize
            });
            this.renderTable(result.items);
            Pagination.render('study-pagination', result.total, result.page, result.page_size, function(p) {
                StudiesPage.page = p;
                StudiesPage.load();
            });
        } catch (e) {
            Toast.show('加载研究失败: ' + e.message, 'error');
        }
    },

    renderTable(items) {
        const tbody = document.querySelector('#study-table tbody');
        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:32px;">暂无数据</td></tr>';
            return;
        }
        let html = '';
        items.forEach(function(s) {
            html += '<tr>';
            html += '<td>' + s.id + '</td>';
            html += '<td><strong>' + Utils.truncate(s.title, 30) + '</strong></td>';
            html += '<td>' + (s.herb_name ? '<span class="herb-tag">' + Utils.escapeHtml(s.herb_name) + '</span>' : '-') + '</td>';
            html += '<td>' + (s.component_name ? Utils.escapeHtml(s.component_name) : '-') + '</td>';
            html += '<td>' + Utils.truncate(s.effect, 20) + '</td>';
            html += '<td>' + Utils.truncate(s.reference, 25) + '</td>';
            html += '<td class="actions">';
            html += '<button class="btn-icon" title="查看详情" onclick="StudiesPage.viewDetail(' + s.id + ')">&#128065;</button>';
            html += '<button class="btn-icon" title="编辑" onclick="StudiesPage.openForm(' + s.id + ')">&#9998;</button>';
            html += '<button class="btn-icon delete" title="删除" onclick="StudiesPage.confirmDelete(' + s.id + ')">&#10005;</button>';
            html += '</td>';
            html += '</tr>';
        });
        tbody.innerHTML = html;
    },

    async viewDetail(id) {
        try {
            const result = await API.getStudy(id);
            const s = result.data;
            let html = '<div><label>研究标题</label><p><strong>' + Utils.escapeHtml(s.title) + '</strong></p></div>';
            html += '<div class="form-row" style="margin-top:12px;">';
            html += '<div><label>关联药材</label><p>' + (s.herb_name ? '<span class="herb-tag">' + Utils.escapeHtml(s.herb_name) + '</span>' : '-') + '</p></div>';
            html += '<div><label>关联成分</label><p>' + (s.component_name ? Utils.escapeHtml(s.component_name) : '-') + '</p></div>';
            html += '</div><div class="form-row">';
            html += '<div><label>药理作用</label><p>' + Utils.escapeHtml(s.effect) + '</p></div>';
            html += '<div><label>作用机制</label><p>' + Utils.escapeHtml(s.mechanism) + '</p></div>';
            html += '</div>';
            html += '<div><label>参考文献</label><p style="word-break:break-all;">' + Utils.escapeHtml(s.reference) + '</p></div>';
            html += '<div><label>研究摘要</label><p>' + Utils.escapeHtml(s.summary) + '</p></div>';
            Modal.open('研究详情', html);
        } catch (e) {
            Toast.show('加载详情失败: ' + e.message, 'error');
        }
    },

    async openForm(id) {
        let study = { title: '', herb_id: '', component_id: '', effect: '', mechanism: '', reference: '', summary: '' };
        const isEdit = !!id;
        if (isEdit) {
            try {
                const result = await API.getStudy(id);
                study = result.data;
            } catch (e) {
                Toast.show('加载研究失败: ' + e.message, 'error');
                return;
            }
        }

        const title = isEdit ? '编辑药理研究' : '新增药理研究';
        let html = HerbsPage._field('study-title', '研究标题', study.title, 'text', true);
        html += '<div class="form-row">';
        html += '<div class="form-group" id="study-herb-select"><label>关联药材</label><p style="font-size:12px;color:var(--text-muted);">加载中...</p></div>';
        html += '<div class="form-group" id="study-comp-select"><label>关联成分</label><p style="font-size:12px;color:var(--text-muted);">加载中...</p></div>';
        html += '</div>';
        html += HerbsPage._field('study-effect', '药理作用', study.effect);
        html += HerbsPage._field('study-mechanism', '作用机制', study.mechanism);
        html += HerbsPage._field('study-reference', '参考文献', study.reference);
        html += HerbsPage._field('study-summary', '研究摘要', study.summary, 'textarea');
        html += '<div class="form-actions">';
        html += '<button class="btn btn-outline" onclick="Modal.close()">取消</button>';
        html += '<button class="btn btn-primary" id="study-save-btn">保存</button>';
        html += '</div>';

        Modal.open(title, html);

        try {
            const herbResult = await API.getAllHerbsSimple();
            const allHerbs = herbResult.data;
            let selHtml = '<label>关联药材</label><select id="field-study-herb_id">';
            selHtml += '<option value="">-- 无 --</option>';
            allHerbs.forEach(function(h) {
                selHtml += '<option value="' + h.id + '"' + (study.herb_id == h.id ? ' selected' : '') + '>' + Utils.escapeHtml(h.name) + '</option>';
            });
            selHtml += '</select>';
            document.getElementById('study-herb-select').innerHTML = selHtml;
        } catch (e) {
            document.getElementById('study-herb-select').innerHTML = '<label>关联药材</label><p style="color:var(--text-muted);">加载失败</p>';
        }

        try {
            const compResult = await API.getComponents({ page_size: 999 });
            const allComps = compResult.items;
            let selHtml = '<label>关联成分</label><select id="field-study-component_id">';
            selHtml += '<option value="">-- 无 --</option>';
            allComps.forEach(function(c) {
                selHtml += '<option value="' + c.id + '"' + (study.component_id == c.id ? ' selected' : '') + '>' + Utils.escapeHtml(c.name) + '</option>';
            });
            selHtml += '</select>';
            document.getElementById('study-comp-select').innerHTML = selHtml;
        } catch (e) {
            document.getElementById('study-comp-select').innerHTML = '<label>关联成分</label><p style="color:var(--text-muted);">加载失败</p>';
        }

        document.getElementById('study-save-btn').addEventListener('click', async function() {
            const data = {
                title: document.getElementById('field-study-title').value,
                herb_id: document.getElementById('field-study-herb_id').value || null,
                component_id: document.getElementById('field-study-component_id').value || null,
                effect: document.getElementById('field-study-effect').value,
                mechanism: document.getElementById('field-study-mechanism').value,
                reference: document.getElementById('field-study-reference').value,
                summary: document.getElementById('field-study-summary').value
            };
            if (!data.title) {
                Toast.show('研究标题不能为空', 'error');
                return;
            }
            try {
                if (isEdit) {
                    await API.updateStudy(id, data);
                    Toast.show('研究更新成功');
                } else {
                    await API.createStudy(data);
                    Toast.show('研究添加成功');
                }
                Modal.close();
                StudiesPage.load();
            } catch (e) {
                Toast.show('保存失败: ' + e.message, 'error');
            }
        });
    },

    confirmDelete(id) {
        if (confirm('确定要删除这项研究吗？此操作不可撤销。')) {
            this.deleteStudy(id);
        }
    },

    async deleteStudy(id) {
        try {
            await API.deleteStudy(id);
            Toast.show('研究已删除');
            this.load();
        } catch (e) {
            Toast.show('删除失败: ' + e.message, 'error');
        }
    },

    init() {
        const searchInput = document.getElementById('study-search');
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                StudiesPage.search = searchInput.value;
                StudiesPage.page = 1;
                StudiesPage.load();
            }, 300);
        });
        this.loadHerbFilter();
    },

    async loadHerbFilter() {
        try {
            const result = await API.getAllHerbsSimple();
            const herbs = result.data;
            const sel = document.getElementById('study-filter-herb');
            herbs.forEach(function(h) {
                const opt = document.createElement('option');
                opt.value = h.id;
                opt.textContent = h.name;
                sel.appendChild(opt);
            });
            sel.addEventListener('change', function() {
                StudiesPage.herbId = sel.value;
                StudiesPage.page = 1;
                StudiesPage.load();
            });
        } catch (e) { /* ignore */ }
    }
};