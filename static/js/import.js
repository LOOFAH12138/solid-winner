/* ===== 数据导入页面 ===== */
const ImportPage = {
    tempFile: null,
    fileType: 'csv',

    init() {
        const zone = document.getElementById('import-zone');
        const fileInput = document.getElementById('import-file-input');

        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', function() {
            zone.classList.remove('drag-over');
        });
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            zone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                ImportPage.handleFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                ImportPage.handleFile(fileInput.files[0]);
            }
        });

        document.getElementById('import-file-type').addEventListener('change', function() {
            ImportPage.fileType = this.value;
        });

        document.getElementById('import-cancel-btn').addEventListener('click', function() {
            ImportPage.resetPreview();
        });
    },

    async handleFile(file) {
        const fileType = document.getElementById('import-file-type').value;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', fileType);

        try {
            Toast.show('正在解析文件...', 'info');
            const result = await API.uploadFile(formData);
            const data = result.data;
            ImportPage.tempFile = data.temp_file;
            ImportPage.showPreview(data);
            Toast.show('文件解析成功，请确认后导入', 'success');
        } catch (e) {
            Toast.show('文件解析失败: ' + e.message, 'error');
        }
    },

    showPreview(data) {
        const preview = document.getElementById('import-preview');
        const thead = document.querySelector('#import-preview-table thead');
        const tbody = document.querySelector('#import-preview-table tbody');

        let headHtml = '<tr>';
        data.headers.forEach(function(h) {
            headHtml += '<th>' + Utils.escapeHtml(h) + '</th>';
        });
        headHtml += '</tr>';
        thead.innerHTML = headHtml;

        let bodyHtml = '';
        data.rows.forEach(function(row) {
            bodyHtml += '<tr>';
            data.headers.forEach(function(h) {
                bodyHtml += '<td>' + Utils.truncate(row[h] || '', 40) + '</td>';
            });
            bodyHtml += '</tr>';
        });
        tbody.innerHTML = bodyHtml;

        document.getElementById('import-preview-count').textContent =
            '共 ' + data.total + ' 条数据（预览前 ' + Math.min(data.rows.length, 20) + ' 条）';

        preview.style.display = 'block';

        document.getElementById('import-confirm-btn').onclick = function() {
            ImportPage.confirmImport();
        };
    },

    resetPreview() {
        document.getElementById('import-preview').style.display = 'none';
        this.tempFile = null;
        document.getElementById('import-file-input').value = '';
    },

    async confirmImport() {
        if (!this.tempFile) {
            Toast.show('请先上传文件', 'error');
            return;
        }
        const entityType = document.getElementById('import-entity-type').value;
        try {
            Toast.show('正在导入...', 'info');
            const result = await API.confirmImport({
                temp_file: this.tempFile,
                type: this.fileType,
                entity_type: entityType
            });
            Toast.show('导入成功！共导入 ' + result.data.imported + ' 条数据', 'success');
            this.resetPreview();
            // 刷新仪表盘
            Dashboard.load();
        } catch (e) {
            Toast.show('导入失败: ' + e.message, 'error');
        }
    }
};