/* ===== 病症管理页面 ===== */
const DiseasesPage = {
    page: 1,
    pageSize: 10,
    search: '',

    async load() {
        try {
            const result = await API.getDiseases({
                search: this.search,
                page: this.page,
                page_size: this.pageSize
            });
            this.renderTable(result.items);
            Pagination.render('disease-pagination', result.total, result.page, result.page_size, function(p) {
                DiseasesPage.page = p;
                DiseasesPage.load();
            });
        } catch (e) {
            Toast.show('加载病症失败: ' + e.message, 'error');
        }
    },

    renderTable(items) {
        const tbody = document.querySelector('#disease-table tbody');
        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:32px;">暂无数据</td></tr>';
            return;
        }
        let html = '';
        items.forEach(function(d) {
            html += '<tr>';
            html += '<td>' + d.id + '</td>';
            html += '<td><strong>' + Utils.escapeHtml(d.name) + '</strong></td>';
            html += '<td>' + Utils.escapeHtml(d.category || '-') + '</td>';
            html += '<td>' + Utils.escapeHtml(d.tcm_syndrome || '-') + '</td>';
            html += '<td>' + Utils.truncate(d.description, 30) + '</td>';
            html += '<td class="actions">';
            html += '<button class="btn-icon" title="查看详情" onclick="DiseasesPage.viewDetail(' + d.id + ')">&#128065;</button>';
            html += '<button class="btn-icon" title="编辑" onclick="DiseasesPage.openForm(' + d.id + ')">&#9998;</button>';
            html += '<button class="btn-icon delete" title="删除" onclick="DiseasesPage.confirmDelete(' + d.id + ', \'' + Utils.escapeHtml(d.name) + '\')">&#10005;</button>';
            html += '</td>';
            html += '</tr>';
        });
        tbody.innerHTML = html;
    },

    async viewDetail(id) {
        try {
            const result = await API.getDisease(id);
            const d = result.data;
            let html = '<div style="max-height:60vh;overflow-y:auto;">';
            html += '<div class="form-row">';
            html += '<div><label>病症名称</label><p><strong>' + Utils.escapeHtml(d.name) + '</strong></p></div>';
            html += '<div><label>分类</label><p>' + Utils.escapeHtml(d.category || '-') + '</p></div>';
            html += '</div><div class="form-row">';
            html += '<div><label>中医证型</label><p>' + Utils.escapeHtml(d.tcm_syndrome || '-') + '</p></div>';
            html += '<div><label>创建时间</label><p>' + Utils.formatDate(d.created_at) + '</p></div>';
            html += '</div>';
            if (d.description) {
                html += '<div style="margin-top:12px;"><label>描述</label><p>' + Utils.escapeHtml(d.description) + '</p></div>';
            }

            if (d.herbs && d.herbs.length > 0) {
                html += '<div style="margin-top:12px;"><label>关联药材</label><div style="margin-top:4px;">';
                d.herbs.forEach(function(h) {
                    html += '<span class="herb-tag">' + Utils.escapeHtml(h.name) + (h.evidence_level ? ' [' + Utils.escapeHtml(h.evidence_level) + ']' : '') + '</span> ';
                });
                html += '</div></div>';
            }
            if (d.prescriptions && d.prescriptions.length > 0) {
                html += '<div style="margin-top:12px;"><label>关联方剂</label><div style="margin-top:4px;">';
                d.prescriptions.forEach(function(p) {
                    html += '<span class="herb-tag" style="background:rgba(201,169,110,0.08);color:var(--amber-dark);">' + Utils.escapeHtml(p.name) + '</span> ';
                });
                html += '</div></div>';
            }
            html += '</div>';
            Modal.open('病症详情 - ' + d.name, html);
        } catch (e) {
            Toast.show('加载详情失败: ' + e.message, 'error');
        }
    },

    async openForm(id) {
        let disease = { name: '', category: '', description: '', tcm_syndrome: '' };
        const isEdit = !!id;
        if (isEdit) {
            try {
                const result = await API.getDisease(id);
                disease = result.data;
            } catch (e) {
                Toast.show('加载病症失败: ' + e.message, 'error');
                return;
            }
        }

        const title = isEdit ? '编辑病症' : '新增病症';
        let html = '<div class="form-row">';
        html += this._field('disease-name', '病症名称', disease.name, 'text', true);
        html += this._field('disease-category', '分类', disease.category);
        html += '</div><div class="form-row">';
        html += this._field('disease-tcm_syndrome', '中医证型', disease.tcm_syndrome);
        html += '</div>';
        html += this._field('disease-description', '描述', disease.description, 'textarea');
        html += '<div class="form-actions">';
        html += '<button class="btn btn-outline" onclick="Modal.close()">取消</button>';
        html += '<button class="btn btn-primary" id="disease-save-btn">保存</button>';
        html += '</div>';

        Modal.open(title, html);
        document.getElementById('disease-save-btn').addEventListener('click', async function() {
            const data = {
                name: document.getElementById('field-disease-name').value,
                category: document.getElementById('field-disease-category').value,
                tcm_syndrome: document.getElementById('field-disease-tcm_syndrome').value,
                description: document.getElementById('field-disease-description').value
            };
            if (!data.name) {
                Toast.show('病症名称不能为空', 'error');
                return;
            }
            try {
                if (isEdit) {
                    await API.updateDisease(id, data);
                    Toast.show('病症更新成功');
                } else {
                    await API.createDisease(data);
                    Toast.show('病症添加成功');
                }
                Modal.close();
                DiseasesPage.load();
            } catch (e) {
                Toast.show('保存失败: ' + e.message, 'error');
            }
        });
    },

    _field(name, label, value, type, required, options) {
        type = type || 'text';
        let html = '<div class="form-group">';
        html += '<label for="field-' + name + '">' + label + (required ? ' <span style="color:var(--seal-red)">*</span>' : '') + '</label>';
        if (type === 'textarea') {
            html += '<textarea id="field-' + name + '" rows="3">' + Utils.escapeHtml(value || '') + '</textarea>';
        } else if (type === 'select' && options) {
            html += '<select id="field-' + name + '">';
            html += '<option value="">-- 请选择 --</option>';
            options.forEach(function(o) {
                html += '<option value="' + o + '"' + (value === o ? ' selected' : '') + '>' + o + '</option>';
            });
            html += '</select>';
        } else {
            html += '<input type="' + type + '" id="field-' + name + '" value="' + Utils.escapeHtml(value || '') + '">';
        }
        html += '</div>';
        return html;
    },

    confirmDelete(id, name) {
        if (confirm('确定要删除病症 "' + name + '" 吗？此操作不可撤销。')) {
            this.deleteDisease(id);
        }
    },

    async deleteDisease(id) {
        try {
            await API.deleteDisease(id);
            Toast.show('病症已删除');
            this.load();
        } catch (e) {
            Toast.show('删除失败: ' + e.message, 'error');
        }
    },

    init() {
        const searchInput = document.getElementById('disease-search');
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                DiseasesPage.search = searchInput.value;
                DiseasesPage.page = 1;
                DiseasesPage.load();
            }, 300);
        });
    }
};