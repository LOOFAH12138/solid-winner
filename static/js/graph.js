/* ===== 知识图谱页面 ===== */
const GraphPage = {
    async load() {
        this.loadStats();
        this.loadEntitySelect();
    },

    async loadStats() {
        try {
            const result = await API.get('/api/graph/stats');
            const data = result.data;
            let html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';
            html += '<div><strong>节点统计</strong><ul style="list-style:none;margin-top:8px;">';
            for (const [label, count] of Object.entries(data.nodes)) {
                html += '<li style="padding:4px 0;font-size:13px;">' + label + ': <strong>' + count + '</strong></li>';
            }
            html += '</ul></div>';
            html += '<div><strong>关系统计</strong><ul style="list-style:none;margin-top:8px;">';
            for (const [rel, count] of Object.entries(data.relationships)) {
                html += '<li style="padding:4px 0;font-size:13px;">' + rel + ': <strong>' + count + '</strong></li>';
            }
            html += '</ul></div></div>';
            document.getElementById('graph-stats').innerHTML = html || '<p style="color:var(--text-muted);">暂无图谱数据</p>';
        } catch (e) {
            document.getElementById('graph-stats').innerHTML = '<p style="color:var(--text-muted);">加载失败</p>';
        }
    },

    async loadEntitySelect() {
        const typeSel = document.getElementById('graph-entity-type');
        const entityType = typeSel.value;
        if (!entityType) {
            document.getElementById('graph-entity-id').innerHTML = '<option value="">选择具体实体</option>';
            this.clearCanvas();
            return;
        }

        let apiUrl = '';
        if (entityType === 'herb') apiUrl = '/api/herbs/all';
        else if (entityType === 'prescription') apiUrl = '/api/prescriptions?page_size=999';
        else if (entityType === 'disease') apiUrl = '/api/diseases?page_size=999';

        try {
            const result = await API.get(apiUrl);
            const items = result.data || result.items || [];
            const idSel = document.getElementById('graph-entity-id');
            idSel.innerHTML = '<option value="">选择具体实体</option>';
            items.forEach(function(item) {
                idSel.innerHTML += '<option value="' + item.id + '">' + Utils.escapeHtml(item.name) + '</option>';
            });
        } catch (e) {
            document.getElementById('graph-entity-id').innerHTML = '<option value="">加载失败</option>';
        }
    },

    async loadGraph() {
        const entityType = document.getElementById('graph-entity-type').value;
        const entityId = document.getElementById('graph-entity-id').value;
        if (!entityType || !entityId) {
            this.clearCanvas();
            return;
        }

        try {
            const result = await API.get('/api/graph/query?entity_type=' + entityType + '&entity_id=' + entityId);
            this.renderGraph(result.data);
        } catch (e) {
            Toast.show('加载图谱失败: ' + e.message, 'error');
        }
    },

    renderGraph(data) {
        const canvas = document.getElementById('graphCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        const nodes = data.nodes || [];
        const edges = data.edges || [];

        if (nodes.length === 0) {
            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim();
            ctx.font = '14px KaiTi';
            ctx.textAlign = 'center';
            ctx.fillText('暂无图谱数据', w / 2, h / 2);
            return;
        }

        // 节点布局
        const positions = {};
        const cx = w / 2;
        const cy = h / 2;
        const radius = Math.min(w, h) / 2 - 40;

        nodes.forEach(function(node, i) {
            const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
            positions[node.type + '_' + node.id] = {
                x: cx + radius * Math.cos(angle),
                y: cy + radius * Math.sin(angle),
                node: node
            };
        });

        // 颜色映射
        const typeColors = {
            herb: '#8b3a3a',
            prescription: '#c9a96e',
            component: '#1a3c34',
            study: '#6b5e4a',
            disease: '#c75b5b'
        };

        // 绘制边
        edges.forEach(function(edge) {
            const from = positions[edge.source];
            const to = positions[edge.target];
            if (!from || !to) return;

            ctx.beginPath();
            ctx.moveTo(from.x, from.y);
            ctx.lineTo(to.x, to.y);
            ctx.strokeStyle = 'rgba(26, 60, 52, 0.2)';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // 标签
            const mx = (from.x + to.x) / 2;
            const my = (from.y + to.y) / 2;
            ctx.fillStyle = '#9e8f78';
            ctx.font = '10px KaiTi';
            ctx.textAlign = 'center';
            ctx.fillText(edge.relationship, mx, my - 5);
        });

        // 绘制节点
        nodes.forEach(function(node) {
            const pos = positions[node.type + '_' + node.id];
            if (!pos) return;

            const color = typeColors[node.type] || '#1a3c34';

            // 阴影
            ctx.beginPath();
            ctx.arc(pos.x + 2, pos.y + 2, 22, 0, 2 * Math.PI);
            ctx.fillStyle = 'rgba(0,0,0,0.1)';
            ctx.fill();

            // 圆形
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 22, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.strokeStyle = '#fdfaf5';
            ctx.lineWidth = 2;
            ctx.stroke();

            // 名称
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 11px KaiTi';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const name = node.name.length > 4 ? node.name.substring(0, 4) + '..' : node.name;
            ctx.fillText(name, pos.x, pos.y);

            // 类型标签
            ctx.fillStyle = color;
            ctx.font = '9px KaiTi';
            ctx.fillText(node.type, pos.x, pos.y + 30);
        });
    },

    clearCanvas() {
        const canvas = document.getElementById('graphCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    },

    async exportGraph() {
        try {
            Toast.show('正在同步数据到 Neo4j...', 'info');
            const result = await API.post('/api/neo4j/sync', {});
            const data = result.data;
            Toast.show('同步完成！药材' + (data.herb_nodes || 0) + '个, 方剂' + (data.prescription_nodes || 0) + '个, 关系' + (data.edges || 0) + '条', 'success');
            this.loadStats();
        } catch (e) {
            Toast.show('同步失败: ' + e.message, 'error');
        }
    },

    async checkHealth() {
        try {
            const result = await API.get('/api/neo4j/health');
            const data = result.data;
            let html = '';
            if (data.connected) {
                html = '<div style="color:#2d6a4f;font-size:13px;">&#9679; Neo4j 已连接 (' + data.uri + ')</div>';
            } else {
                html = '<div style="color:#c75b5b;font-size:13px;">&#9679; Neo4j 未连接: ' + Utils.escapeHtml(data.error || '未知错误') + '</div>';
                html += '<div style="color:var(--text-muted);font-size:12px;margin-top:4px;">请确保 Neo4j 已启动，然后点击同步按钮</div>';
            }
            document.getElementById('neo4j-status').innerHTML = html;
        } catch (e) {
            document.getElementById('neo4j-status').innerHTML = '<div style="color:#c75b5b;">&#9679; 无法检测 Neo4j 状态</div>';
        }
    },

    init() {
        document.getElementById('graph-entity-type').addEventListener('change', function() {
            GraphPage.loadEntitySelect();
            GraphPage.clearCanvas();
        });
        this.checkHealth();
    }
};