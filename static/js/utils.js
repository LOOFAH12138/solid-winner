/* ===== 工具函数 ===== */
// 配置 marked.js 安全选项
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
    });
}

const Utils = {
    typeLabels: {
        herb: '药材',
        prescription: '方剂',
        component: '成分',
        study: '研究',
        disease: '病症',
        pharmacology: '药理学'
    },

    formatDate(dateStr) {
        if (!dateStr) return '-';
        try {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) return dateStr;
            // 转换为东八区（UTC+8）时间
            const utc8 = new Date(d.getTime() + 8 * 3600000);
            return utc8.getUTCFullYear() + '-' +
                String(utc8.getUTCMonth() + 1).padStart(2, '0') + '-' +
                String(utc8.getUTCDate()).padStart(2, '0') + ' ' +
                String(utc8.getUTCHours()).padStart(2, '0') + ':' +
                String(utc8.getUTCMinutes()).padStart(2, '0');
        } catch (e) {
            return dateStr;
        }
    },

    truncate(str, len = 30) {
        if (!str) return '-';
        return str.length > len ? str.substring(0, len) + '...' : str;
    },

    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    validateRequired(fields) {
        for (const field of fields) {
            if (!field.value || !field.value.trim()) {
                Toast.show(field.label + '不能为空', 'error');
                field.focus();
                return false;
            }
        }
        return true;
    },

    debounce(fn, delay) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },

    /**
     * 将 Markdown 转换为 HTML（不转义）
     */
    renderMarkdown(md) {
        if (typeof marked !== 'undefined') {
            try {
                return marked.parse(md);
            } catch (e) {
                console.error('Markdown render error:', e);
                return Utils.escapeHtml(md).replace(/\n/g, '<br>');
            }
        }
        // fallback: 将换行转为 <br>
        return Utils.escapeHtml(md).replace(/\n/g, '<br>');
    }
};

/* ===== Toast ===== */
const Toast = {
    show(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const el = document.createElement('div');
        el.className = 'toast ' + type;
        
        const icons = { success: '✓', error: '✕', info: 'ℹ' };
        el.innerHTML = '<span style="font-size:16px;">' + (icons[type] || '') + '</span> ' + message;
        
        container.appendChild(el);
        setTimeout(function() {
            el.style.opacity = '0';
            el.style.transition = 'opacity 0.3s';
            setTimeout(function() { el.remove(); }, 300);
        }, 3000);
    }
};

/* ===== 模态框 ===== */
const Modal = {
    open(title, bodyHtml) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = bodyHtml;
        document.getElementById('modal-overlay').classList.add('show');
        document.body.style.overflow = 'hidden';
    },

    close() {
        document.getElementById('modal-overlay').classList.remove('show');
        document.body.style.overflow = '';
    },

    init() {
        document.getElementById('modal-overlay').addEventListener('click', function(e) {
            if (e.target === this) Modal.close();
        });
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                Modal.close();
            }
        });
    }
};

/* ===== 分页组件 ===== */
const Pagination = {
    render(containerId, total, page, pageSize, onPageChange) {
        const totalPages = Math.ceil(total / pageSize);
        const container = document.getElementById(containerId);
        if (!container || totalPages <= 1) {
            if (container) container.innerHTML = '';
            return;
        }
        let html = '';
        html += '<button ' + (page <= 1 ? 'disabled' : '') + ' data-page="' + (page - 1) + '">&laquo; 上一页</button>';

        const start = Math.max(1, page - 2);
        const end = Math.min(totalPages, page + 2);

        if (start > 1) {
            html += '<button data-page="1">1</button>';
            if (start > 2) html += '<span class="page-info">...</span>';
        }

        for (let i = start; i <= end; i++) {
            html += '<button class="' + (i === page ? 'active' : '') + '" data-page="' + i + '">' + i + '</button>';
        }

        if (end < totalPages) {
            if (end < totalPages - 1) html += '<span class="page-info">...</span>';
            html += '<button data-page="' + totalPages + '">' + totalPages + '</button>';
        }

        html += '<button ' + (page >= totalPages ? 'disabled' : '') + ' data-page="' + (page + 1) + '">下一页 &raquo;</button>';
        html += '<span class="page-info">共 ' + total + ' 条</span>';

        container.innerHTML = html;
        container.querySelectorAll('button[data-page]').forEach(function(btn) {
            btn.addEventListener('click', function() {
                onPageChange(parseInt(this.dataset.page));
            });
        });
    }
};