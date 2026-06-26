/* ===== 仪表盘页面 ===== */
const Dashboard = {
    async load() {
        try {
            const result = await API.getStats();
            const data = result.data;

            // 统计数字
            document.getElementById('stat-herbs').textContent = data.counts.herbs;
            document.getElementById('stat-prescriptions').textContent = data.counts.prescriptions;
            document.getElementById('stat-components').textContent = data.counts.components;
            document.getElementById('stat-diseases').textContent = data.counts.diseases || 0;

            // 时间线
            this.renderTimeline(data.recent);

            // 饼图
            this.renderTasteChart(data.taste_distribution);
        } catch (e) {
            console.error('加载仪表盘失败:', e);
        }
    },

    renderTimeline(recent) {
        const container = document.getElementById('timeline');
        if (!recent || recent.length === 0) {
            container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px;">暂无数据</p>';
            return;
        }
        let html = '';
        recent.forEach(function(item) {
            const typeName = Utils.typeLabels[item.type] || item.type;
            html += '<div class="timeline-item">';
            html += '<div class="timeline-title">' + Utils.escapeHtml(item.title) + '</div>';
            html += '<div class="timeline-meta">';
            html += '<span class="timeline-type type-' + item.type + '">' + typeName + '</span>';
            html += Utils.formatDate(item.created_at);
            html += '</div></div>';
        });
        container.innerHTML = html;
    },

    renderTasteChart(distribution) {
        const canvas = document.getElementById('tasteChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        if (!distribution || distribution.length === 0) {
            ctx.fillStyle = 'var(--text-muted)';
            ctx.font = '14px var(--font-body)';
            ctx.textAlign = 'center';
            ctx.fillText('暂无数据', w / 2, h / 2);
            return;
        }

        const colors = ['#c9a96e', '#8b3a3a', '#1a3c34', '#6b5e4a', '#e0c78a', '#234d43', '#c75b5b', '#9e8f78'];
        const total = distribution.reduce(function(s, d) { return s + d.cnt; }, 0);
        const cx = w / 2;
        const cy = h / 2;
        const radius = Math.min(cx, cy) - 20;
        let startAngle = -Math.PI / 2;

        distribution.forEach(function(d, i) {
            const sliceAngle = (d.cnt / total) * 2 * Math.PI;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = colors[i % colors.length];
            ctx.fill();
            ctx.strokeStyle = 'var(--paper-white)';
            ctx.lineWidth = 2;
            ctx.stroke();

            // 标签
            const midAngle = startAngle + sliceAngle / 2;
            const labelR = radius * 0.65;
            const lx = cx + Math.cos(midAngle) * labelR;
            const ly = cy + Math.sin(midAngle) * labelR;
            ctx.fillStyle = 'white';
            ctx.font = 'bold 12px var(--font-body)';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            if (sliceAngle > 0.3) {
                ctx.fillText(d.taste + ' ' + d.cnt, lx, ly);
            }

            startAngle += sliceAngle;
        });
    }
};