/* ===== 化学成分管理页面 ===== */
const ComponentsPage = {
    page: 1,
    pageSize: 10,
    search: '',
    herbId: '',

    async load() {
        try {
            const result = await API.getComponents({
                search: this.search,
                herb_id: this.herbId,
                page: this.page,
                page_size: this.pageSize
            });
            this.renderTable(result.items);
            Pagination.render('comp-pagination', result.total, result.page, result.page_size, function(p) {
                ComponentsPage.page = p;
                ComponentsPage.load();
            });
        } catch (e) {
            Toast.show('加载成分失败: ' + e.message, 'error');
        }
    },

    renderTable(items) {
        const tbody = document.querySelector('#comp-table tbody');
        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:32px;">暂无数据</td></tr>';
            return;
        }
        let html = '';
        items.forEach(function(c) {
            html += '<tr>';
            html += '<td>' + c.id + '</td>';
            html += '<td><strong>' + Utils.escapeHtml(c.name) + '</strong></td>';
            html += '<td><code>' + Utils.escapeHtml(c.formula) + '</code></td>';
            html += '<td>' + Utils.escapeHtml(c.cas_number) + '</td>';
            html += '<td>' + (c.herb_name ? '<span class="herb-tag">' + Utils.escapeHtml(c.herb_name) + '</span>' : '-') + '</td>';
            html += '<td>' + Utils.truncate(c.bioactivity, 25) + '</td>';
            html += '<td class="actions">';
            html += '<button class="btn-icon" title="查看详情" onclick="ComponentsPage.viewDetail(' + c.id + ')">&#128065;</button>';
            html += '<button class="btn-icon" title="编辑" onclick="ComponentsPage.openForm(' + c.id + ')">&#9998;</button>';
            html += '<button class="btn-icon delete" title="删除" onclick="ComponentsPage.confirmDelete(' + c.id + ', \'' + Utils.escapeHtml(c.name) + '\')">&#10005;</button>';
            html += '</td>';
            html += '</tr>';
        });
        tbody.innerHTML = html;
    },

    async viewDetail(id) {
        try {
            const result = await API.getComponent(id);
            const c = result.data;
            let html = '<div class="form-row">';
            html += '<div><label>成分名称</label><p><strong>' + Utils.escapeHtml(c.name) + '</strong></p></div>';
            html += '<div><label>分子式</label><p><code>' + Utils.escapeHtml(c.formula) + '</code></p></div>';
            html += '</div><div class="form-row">';
            html += '<div><label>CAS号</label><p>' + Utils.escapeHtml(c.cas_number) + '</p></div>';
            html += '<div><label>来源药材</label><p>' + (c.herb_name ? '<span class="herb-tag">' + Utils.escapeHtml(c.herb_name) + '</span>' : '-') + '</p></div>';
            html += '</div>';
            html += '<div><label>生物活性</label><p>' + Utils.escapeHtml(c.bioactivity) + '</p></div>';
            html += '<div><label>创建时间</label><p>' + Utils.formatDate(c.created_at) + '</p></div>';
            Modal.open('成分详情 - ' + c.name, html);
        } catch (e) {
            Toast.show('加载详情失败: ' + e.message, 'error');
        }
    },

    async openForm(id) {
        let comp = { name: '', formula: '', cas_number: '', herb_id: '', bioactivity: '' };
        const isEdit = !!id;
        if (isEdit) {
            try {
                const result = await API.getComponent(id);
                comp = result.data;
            } catch (e) {
                Toast.show('加载成分失败: ' + e.message, 'error');
                return;
            }
        }

        const title = isEdit ? '编辑化学成分' : '新增化学成分';
        let html = '<div class="form-row">';
        html += HerbsPage._field('comp-name', '成分名称', comp.name, 'text', true);
        html += HerbsPage._field('comp-formula', '分子式', comp.formula);
        html += '</div><div class="form-row">';
        html += HerbsPage._field('comp-cas_number', 'CAS号', comp.cas_number);
        html += '<div class="form-group" id="comp-herb-select"><label>来源药材</label><p style="font-size:12px;color:var(--text-muted);">加载中...</p></div>';
        html += '</div>';
        html += HerbsPage._field('comp-bioactivity', '生物活性', comp.bioactivity, 'textarea');
        html += '<div class="form-actions">';
        html += '<button class="btn btn-outline" onclick="Modal.close()">取消</button>';
        html += '<button class="btn btn-primary" id="comp-save-btn">保存</button>';
        html += '</div>';

        Modal.open(title, html);

        try {
            const herbResult = await API.getAllHerbsSimple();
            const allHerbs = herbResult.data;
            let selHtml = '<label>来源药材</label><select id="field-comp-herb_id">';
            selHtml += '<option value="">-- 无 --</option>';
            allHerbs.forEach(function(h) {
                selHtml += '<option value="' + h.id + '"' + (comp.herb_id == h.id ? ' selected' : '') + '>' + Utils.escapeHtml(h.name) + '</option>';
            });
            selHtml += '</select>';
            document.getElementById('comp-herb-select').innerHTML = selHtml;
        } catch (e) {
            document.getElementById('comp-herb-select').innerHTML = '<label>来源药材</label><p style="color:var(--text-muted);">加载失败</p>';
        }

        document.getElementById('comp-save-btn').addEventListener('click', async function() {
            const data = {
                name: document.getElementById('field-comp-name').value,
                formula: document.getElementById('field-comp-formula').value,
                cas_number: document.getElementById('field-comp-cas_number').value,
                herb_id: document.getElementById('field-comp-herb_id').value || null,
                bioactivity: document.getElementById('field-comp-bioactivity').value
            };
            if (!data.name) {
                Toast.show('成分名称不能为空', 'error');
                return;
            }
            try {
                if (isEdit) {
                    await API.updateComponent(id, data);
                    Toast.show('成分更新成功');
                } else {
                    await API.createComponent(data);
                    Toast.show('成分添加成功');
                }
                Modal.close();
                ComponentsPage.load();
            } catch (e) {
                Toast.show('保存失败: ' + e.message, 'error');
            }
        });
    },

    confirmDelete(id, name) {
        if (confirm('确定要删除成分 "' + name + '" 吗？此操作不可撤销。')) {
            this.deleteComponent(id);
        }
    },

    async deleteComponent(id) {
        try {
            await API.deleteComponent(id);
            Toast.show('成分已删除');
            this.load();
        } catch (e) {
            Toast.show('删除失败: ' + e.message, 'error');
        }
    },

    init() {
        const searchInput = document.getElementById('comp-search');
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                ComponentsPage.search = searchInput.value;
                ComponentsPage.page = 1;
                ComponentsPage.load();
            }, 300);
        });

        // 加载药材筛选下拉
        this.loadHerbFilter();
    },

    async loadHerbFilter() {
        try {
            const result = await API.getAllHerbsSimple();
            const herbs = result.data;
            const sel = document.getElementById('comp-filter-herb');
            herbs.forEach(function(h) {
                const opt = document.createElement('option');
                opt.value = h.id;
                opt.textContent = h.name;
                sel.appendChild(opt);
            });
            sel.addEventListener('change', function() {
                ComponentsPage.herbId = sel.value;
                ComponentsPage.page = 1;
                ComponentsPage.load();
            });
        } catch (e) { /* ignore */ }
    }
};