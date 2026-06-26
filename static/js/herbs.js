/* ===== 药材管理页面 ===== */
const HerbsPage = {
    page: 1,
    pageSize: 10,
    search: '',
    nature: '',
    taste: '',

    async load() {
        try {
            const result = await API.getHerbs({
                search: this.search,
                nature: this.nature,
                taste: this.taste,
                page: this.page,
                page_size: this.pageSize
            });
            this.renderTable(result.items);
            Pagination.render('herb-pagination', result.total, result.page, result.page_size, function(p) {
                HerbsPage.page = p;
                HerbsPage.load();
            });
        } catch (e) {
            Toast.show('加载药材失败: ' + e.message, 'error');
        }
    },

    renderTable(items) {
        const tbody = document.querySelector('#herb-table tbody');
        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--text-muted);padding:32px;">暂无数据</td></tr>';
            return;
        }
        let html = '';
        items.forEach(function(h) {
            html += '<tr>';
            html += '<td>' + h.id + '</td>';
            html += '<td><strong>' + Utils.escapeHtml(h.name) + '</strong></td>';
            html += '<td style="font-style:italic">' + Utils.escapeHtml(h.latin_name) + '</td>';
            html += '<td>' + Utils.escapeHtml(h.category) + '</td>';
            html += '<td>' + Utils.escapeHtml(h.nature) + '</td>';
            html += '<td>' + Utils.escapeHtml(h.taste) + '</td>';
            html += '<td>' + Utils.escapeHtml(h.meridian) + '</td>';
            html += '<td>' + Utils.truncate(h.pinyin_name || '', 8) + '</td>';
            html += '<td>' + Utils.escapeHtml(h.tcm_name_en || '') + '</td>';
            html += '<td class="actions">';
            html += '<button class="btn-icon" title="查看详情" onclick="HerbsPage.viewDetail(' + h.id + ')">&#128065;</button>';
            html += '<button class="btn-icon" title="编辑" onclick="HerbsPage.openForm(' + h.id + ')">&#9998;</button>';
            html += '<button class="btn-icon delete" title="删除" onclick="HerbsPage.confirmDelete(' + h.id + ', \'' + Utils.escapeHtml(h.name) + '\')">&#10005;</button>';
            html += '</td>';
            html += '</tr>';
        });
        tbody.innerHTML = html;
    },

    async viewDetail(id) {
        try {
            const result = await API.getHerb(id);
            const h = result.data;

            let html = '<div style="max-height:60vh;overflow-y:auto;">';

            // 基本信息
            html += '<h4 style="margin-bottom:8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">基本信息</h4>';
            html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
            html += '<div><label>药材名称</label><p><strong>' + Utils.escapeHtml(h.name) + '</strong></p></div>';
            html += '<div><label>拼音</label><p>' + Utils.escapeHtml(h.pinyin_name) + '</p></div>';
            html += '<div><label>拉丁学名</label><p style="font-style:italic">' + Utils.escapeHtml(h.latin_name) + '</p></div>';
            html += '<div><label>英文名</label><p>' + Utils.escapeHtml(h.tcm_name_en) + '</p></div>';
            html += '<div><label>分类</label><p>' + Utils.escapeHtml(h.category) + '</p></div>';
            html += '<div><label>药用部位</label><p>' + Utils.escapeHtml(h.use_part) + '</p></div>';
            html += '<div><label>四气</label><p>' + Utils.escapeHtml(h.nature) + '</p></div>';
            html += '<div><label>五味</label><p>' + Utils.escapeHtml(h.taste) + '</p></div>';
            html += '<div><label>归经</label><p>' + Utils.escapeHtml(h.meridian) + '</p></div>';
            html += '<div><label>毒性</label><p>' + Utils.escapeHtml(h.toxicity) + '</p></div>';
            html += '<div><label>用量</label><p>' + Utils.escapeHtml(h.dosage) + '</p></div>';
            html += '<div><label>创建时间</label><p>' + Utils.formatDate(h.created_at) + '</p></div>';
            html += '</div>';

            // 功效主治
            if (h.efficacy || h.indication) {
                html += '<h4 style="margin:16px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">功效主治</h4>';
                if (h.efficacy) html += '<div style="margin-bottom:8px;"><label>功效</label><p>' + Utils.escapeHtml(h.efficacy) + '</p></div>';
                if (h.indication) html += '<div style="margin-bottom:8px;"><label>主治</label><p>' + Utils.escapeHtml(h.indication) + '</p></div>';
                if (h.clinical_manifestations) html += '<div style="margin-bottom:8px;"><label>临床表现</label><p>' + Utils.escapeHtml(h.clinical_manifestations) + '</p></div>';
            }

            // TCMBank 信息
            if (h.tcmbank_id || h.level1_name_en || h.therapeutic_cn_class || h.tcmid_id) {
                html += '<h4 style="margin:16px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">TCMBank 关联</h4>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
                if (h.tcmbank_id) html += '<div><label>TCMBank ID</label><p>' + Utils.escapeHtml(h.tcmbank_id) + '</p></div>';
                if (h.level1_name_en) html += '<div><label>一级分类(EN)</label><p>' + Utils.escapeHtml(h.level1_name_en) + '</p></div>';
                if (h.therapeutic_cn_class) html += '<div><label>治疗分类</label><p>' + Utils.escapeHtml(h.therapeutic_cn_class) + '</p></div>';
                if (h.therapeutic_en_class) html += '<div><label>治疗分类(EN)</label><p>' + Utils.escapeHtml(h.therapeutic_en_class) + '</p></div>';
                if (h.tcmid_id) html += '<div><label>TCMID</label><p>' + Utils.escapeHtml(h.tcmid_id) + '</p></div>';
                if (h.tcm_id_id) html += '<div><label>TCM-ID</label><p>' + Utils.escapeHtml(h.tcm_id_id) + '</p></div>';
                if (h.symmap_id) html += '<div><label>SymMap</label><p>' + Utils.escapeHtml(h.symmap_id) + '</p></div>';
                if (h.tcmsp_id) html += '<div><label>TCMSP</label><p>' + Utils.escapeHtml(h.tcmsp_id) + '</p></div>';
                if (h.herb_external_id) html += '<div><label>Herb_ID</label><p>' + Utils.escapeHtml(h.herb_external_id) + '</p></div>';
                html += '</div>';
            }

            if (h.description) {
                html += '<h4 style="margin:16px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">描述</h4>';
                html += '<p>' + Utils.escapeHtml(h.description) + '</p>';
            }

            if (h.prescriptions && h.prescriptions.length > 0) {
                html += '<h4 style="margin:16px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">关联方剂</h4>';
                h.prescriptions.forEach(function(p) {
                    html += '<span class="herb-tag">' + Utils.escapeHtml(p.name) + (p.dosage ? ' (' + Utils.escapeHtml(p.dosage) + ')' : '') + '</span> ';
                });
            }

            if (h.components && h.components.length > 0) {
                html += '<h4 style="margin:16px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">含有成分</h4>';
                h.components.forEach(function(c) {
                    html += '<span class="herb-tag" style="background:rgba(26,60,52,0.08);color:var(--ink-green);">' + Utils.escapeHtml(c.name) + '</span> ';
                });
            }

            html += '</div>';
            Modal.open('药材详情 - ' + h.name, html);
        } catch (e) {
            Toast.show('加载详情失败: ' + e.message, 'error');
        }
    },

    async openForm(id) {
        let herb = {
            name: '', latin_name: '', category: '', nature: '', taste: '', meridian: '',
            efficacy: '', toxicity: '', dosage: '', description: '',
            tcmbank_id: '', level1_name_en: '', pinyin_name: '', tcm_name_en: '',
            use_part: '', indication: '', clinical_manifestations: '',
            therapeutic_en_class: '', therapeutic_cn_class: '',
            tcmid_id: '', tcm_id_id: '', symmap_id: '', tcmsp_id: '', herb_external_id: ''
        };
        const isEdit = !!id;

        if (isEdit) {
            try {
                const result = await API.getHerb(id);
                herb = result.data;
            } catch (e) {
                Toast.show('加载药材失败: ' + e.message, 'error');
                return;
            }
        }

        const title = isEdit ? '编辑药材' : '新增药材';
        let html = '<div style="max-height:60vh;overflow-y:auto;padding-right:4px;">';

        // 基本信息
        html += '<h4 style="margin-bottom:8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">基本信息</h4>';
        html += '<div class="form-row">';
        html += this._field('name', '药材名称', herb.name, 'text', true);
        html += this._field('pinyin_name', '拼音', herb.pinyin_name);
        html += '</div><div class="form-row">';
        html += this._field('latin_name', '拉丁学名', herb.latin_name);
        html += this._field('tcm_name_en', '英文名', herb.tcm_name_en);
        html += '</div><div class="form-row">';
        html += this._field('category', '二级分类', herb.category);
        html += this._field('use_part', '药用部位', herb.use_part);
        html += '</div>';

        // 性味归经
        html += '<h4 style="margin:12px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">性味归经</h4>';
        html += '<div class="form-row">';
        html += this._field('nature', '四气', herb.nature, 'select', false, ['寒', '热', '温', '凉', '平']);
        html += this._field('taste', '五味', herb.taste);
        html += '</div><div class="form-row">';
        html += this._field('meridian', '归经', herb.meridian);
        html += this._field('toxicity', '毒性', herb.toxicity);
        html += '</div>';

        // 功效主治
        html += '<h4 style="margin:12px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;">功效主治</h4>';
        html += this._field('efficacy', '功效', herb.efficacy, 'textarea');
        html += this._field('indication', '主治', herb.indication, 'textarea');
        html += this._field('clinical_manifestations', '临床表现', herb.clinical_manifestations, 'textarea');
        html += '<div class="form-row">';
        html += this._field('dosage', '用量', herb.dosage);
        html += '</div>';

        // TCMBank 扩展字段 (可折叠)
        html += '<h4 style="margin:12px 0 8px;border-bottom:1px solid #e0d5c1;padding-bottom:4px;cursor:pointer;" onclick="var t=document.getElementById(\'tcmbank-fields\');t.style.display=t.style.display===\'none\'?\'block\':\'none\';var i=this.querySelector(\'span\');i.textContent=i.textContent===\'&#9650;\'?\'&#9660;\':\'&#9650\';">TCMBank 关联信息 <span style="font-size:11px;">&#9660;</span></h4>';
        html += '<div id="tcmbank-fields" style="display:none;">';
        html += '<div class="form-row">';
        html += this._field('tcmbank_id', 'TCMBank ID', herb.tcmbank_id);
        html += this._field('herb_external_id', 'Herb ID', herb.herb_external_id);
        html += '</div><div class="form-row">';
        html += this._field('level1_name_en', '一级分类(EN)', herb.level1_name_en);
        html += this._field('therapeutic_cn_class', '治疗分类', herb.therapeutic_cn_class);
        html += '</div><div class="form-row">';
        html += this._field('therapeutic_en_class', '治疗分类(EN)', herb.therapeutic_en_class);
        html += '</div>';
        html += '<h5 style="margin:8px 0;">外部数据库 ID 映射</h5>';
        html += '<div class="form-row">';
        html += this._field('tcmid_id', 'TCMID', herb.tcmid_id);
        html += this._field('tcm_id_id', 'TCM-ID', herb.tcm_id_id);
        html += '</div><div class="form-row">';
        html += this._field('symmap_id', 'SymMap', herb.symmap_id);
        html += this._field('tcmsp_id', 'TCMSP', herb.tcmsp_id);
        html += '</div>';
        html += '</div>';

        html += this._field('description', '描述', herb.description, 'textarea');
        html += '</div>';

        html += '<div class="form-actions">';
        html += '<button class="btn btn-outline" onclick="Modal.close()">取消</button>';
        html += '<button class="btn btn-primary" id="herb-save-btn">保存</button>';
        html += '</div>';

        Modal.open(title, html);

        document.getElementById('herb-save-btn').addEventListener('click', async function() {
            const data = {
                name: document.getElementById('field-name').value,
                latin_name: document.getElementById('field-latin_name').value,
                category: document.getElementById('field-category').value,
                nature: document.getElementById('field-nature').value,
                taste: document.getElementById('field-taste').value,
                meridian: document.getElementById('field-meridian').value,
                efficacy: document.getElementById('field-efficacy').value,
                toxicity: document.getElementById('field-toxicity').value,
                dosage: document.getElementById('field-dosage').value,
                description: document.getElementById('field-description').value,
                tcmbank_id: document.getElementById('field-tcmbank_id').value,
                level1_name_en: document.getElementById('field-level1_name_en').value,
                pinyin_name: document.getElementById('field-pinyin_name').value,
                tcm_name_en: document.getElementById('field-tcm_name_en').value,
                use_part: document.getElementById('field-use_part').value,
                indication: document.getElementById('field-indication').value,
                clinical_manifestations: document.getElementById('field-clinical_manifestations').value,
                therapeutic_en_class: document.getElementById('field-therapeutic_en_class').value,
                therapeutic_cn_class: document.getElementById('field-therapeutic_cn_class').value,
                tcmid_id: document.getElementById('field-tcmid_id').value,
                tcm_id_id: document.getElementById('field-tcm_id_id').value,
                symmap_id: document.getElementById('field-symmap_id').value,
                tcmsp_id: document.getElementById('field-tcmsp_id').value,
                herb_external_id: document.getElementById('field-herb_external_id').value
            };
            if (!data.name) {
                Toast.show('药材名称不能为空', 'error');
                return;
            }
            try {
                if (isEdit) {
                    await API.updateHerb(id, data);
                    Toast.show('药材更新成功');
                } else {
                    await API.createHerb(data);
                    Toast.show('药材添加成功');
                }
                Modal.close();
                HerbsPage.load();
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
        if (confirm('确定要删除药材 "' + name + '" 吗？此操作不可撤销。')) {
            this.deleteHerb(id);
        }
    },

    async deleteHerb(id) {
        try {
            await API.deleteHerb(id);
            Toast.show('药材已删除');
            this.load();
        } catch (e) {
            Toast.show('删除失败: ' + e.message, 'error');
        }
    },

    init() {
        const searchInput = document.getElementById('herb-search');
        const filterNature = document.getElementById('herb-filter-nature');
        const filterTaste = document.getElementById('herb-filter-taste');

        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                HerbsPage.search = searchInput.value;
                HerbsPage.page = 1;
                HerbsPage.load();
            }, 300);
        });

        filterNature.addEventListener('change', function() {
            HerbsPage.nature = filterNature.value;
            HerbsPage.page = 1;
            HerbsPage.load();
        });

        filterTaste.addEventListener('change', function() {
            HerbsPage.taste = filterTaste.value;
            HerbsPage.page = 1;
            HerbsPage.load();
        });
    }
};