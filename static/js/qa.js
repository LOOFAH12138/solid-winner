/* ===== 智能问答页面 - Agent 工作链版 v4 ===== */
const QAPage = {
    currentModel: 'agnes-2.0-flash',
    models: [],
    currentMsgEl: null,
    thinkingProcessEl: null,

    async load() {
        this.loadModels();
        this.loadHistory();
        this.init();
    },

    loadModels() {
        this.models = [
            { id: 'agnes-1.5-flash', name: 'Agnes-1.5-Flash (快速)' },
            { id: 'agnes-2.0-flash', name: 'Agnes-2.0-Flash (高性能)' }
        ];
        const sel = document.getElementById('qa-model-select');
        sel.innerHTML = '';
        this.models.forEach(m => {
            sel.innerHTML += `<option value="${m.id}"${m.id === this.currentModel ? ' selected' : ''}>${m.name}</option>`;
        });
        sel.addEventListener('change', () => {
            this.currentModel = sel.value;
        });
    },

    createThinkingPanel() {
        const panelId = 'thinking-panel-' + Date.now();
        return `
            <div id="${panelId}" class="thinking-panel" style="margin: 12px 0; padding: 12px; background: #fafafa; border-radius: 8px; border: 1px solid #e0e0e0;">
                <div style="font-weight: 600; margin-bottom: 10px; color: #333; display: flex; align-items: center; gap: 8px;">
                    <span>🧠</span>
                    <span>AI 思考过程</span>
                    <span style="font-size: 11px; color: #999; font-weight: normal;">实时显示 Agent 执行状态</span>
                </div>
                <div class="thinking-steps">
                    <div class="thinking-step" data-step="router" style="padding: 10px 12px; margin: 6px 0; background: white; border-radius: 6px; border-left: 3px solid #ccc; transition: all 0.3s;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 16px;">🔀</span>
                                <span style="font-weight: 500;">Router Agent</span>
                                <span style="font-size: 11px; color: #666;">分析问题类型</span>
                            </div>
                            <span class="step-status" style="color: #999; font-size: 12px;">⏳ 等待中</span>
                        </div>
                    </div>
                    <div class="thinking-step" data-step="localdb" style="padding: 10px 12px; margin: 6px 0; background: white; border-radius: 6px; border-left: 3px solid #ccc; transition: all 0.3s;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 16px;">🗄️</span>
                                <span style="font-weight: 500;">LocalDB Agent</span>
                                <span style="font-size: 11px; color: #666;">查询本地数据库</span>
                            </div>
                            <span class="step-status" style="color: #999; font-size: 12px;">⏳ 等待中</span>
                        </div>
                    </div>
                    <div class="thinking-step" data-step="graphdb" style="padding: 10px 12px; margin: 6px 0; background: white; border-radius: 6px; border-left: 3px solid #ccc; transition: all 0.3s;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 16px;">🌐</span>
                                <span style="font-weight: 500;">GraphDB Agent</span>
                                <span style="font-size: 11px; color: #666;">查询云端图谱</span>
                            </div>
                            <span class="step-status" style="color: #999; font-size: 12px;">⏳ 等待中</span>
                        </div>
                    </div>
                    <div class="thinking-step" data-step="synthesizer" style="padding: 10px 12px; margin: 6px 0; background: white; border-radius: 6px; border-left: 3px solid #ccc; transition: all 0.3s;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 16px;">✍️</span>
                                <span style="font-weight: 500;">Synthesizer Agent</span>
                                <span style="font-size: 11px; color: #666;">生成最终回答</span>
                            </div>
                            <span class="step-status" style="color: #999; font-size: 12px;">⏳ 等待中</span>
                        </div>
                    </div>
                </div>
                <div class="thinking-log" style="margin-top: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-size: 11px; color: #666; max-height: 100px; overflow-y: auto; font-family: monospace;">
                    <div style="color: #999;">等待开始...</div>
                </div>
            </div>
        `;
    },

    updateThinkingStep(step, status, message) {
        const panel = document.querySelector('.thinking-panel');
        if (!panel) return;

        const stepEl = panel.querySelector(`[data-step="${step}"]`);
        if (!stepEl) return;

        const statusEl = stepEl.querySelector('.step-status');
        const stepBorder = stepEl.style.borderLeftColor;

        if (status === 'running') {
            stepEl.style.background = '#e3f2fd';
            stepEl.style.borderLeftColor = '#2196F3';
            statusEl.innerHTML = '<span style="color: #2196F3;">⏳ 运行中...</span>';
            this.addLog(message || '执行中...');
        } else if (status === 'complete') {
            stepEl.style.background = '#e8f5e9';
            stepEl.style.borderLeftColor = '#4CAF50';
            statusEl.innerHTML = `<span style="color: #4CAF50;">✓ ${message || '完成'}</span>`;
            this.addLog(`✓ ${message || '完成'}`, '#4CAF50');
        } else if (status === 'error') {
            stepEl.style.background = '#ffebee';
            stepEl.style.borderLeftColor = '#f44336';
            statusEl.innerHTML = `<span style="color: #f44336;">✗ ${message || '失败'}</span>`;
            this.addLog(`✗ ${message || '失败'}`, '#f44336');
        }
    },

    addLog(message, color = '#666') {
        const logEl = document.querySelector('.thinking-log');
        if (!logEl) return;

        const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        const logEntry = document.createElement('div');
        logEntry.style.color = color;
        logEntry.style.marginTop = '4px';
        logEntry.textContent = `[${time}] ${message}`;
        logEl.appendChild(logEntry);
        logEl.scrollTop = logEl.scrollHeight;
    },

    async ask() {
        const input = document.getElementById('qa-input');
        const question = input.value.trim();
        if (!question) return;

        this.appendMessage('user', Utils.escapeHtml(question));
        input.value = '';
        input.disabled = true;

        const model = document.getElementById('qa-model-select').value;

        // 创建思考过程面板
        const panelHtml = this.createThinkingPanel();
        const loadingId = this.appendMessage('assistant',
            `${panelHtml}<div style="margin-top: 8px;"><span class="qa-loading-spinner"></span> Agent 工作链正在执行...</div>`, true);
        this.currentMsgEl = document.getElementById(loadingId);

        // 清空日志
        this.addLog('开始分析问题...', '#2196F3');

        try {
            const result = await API.post('/api/qa/search', {
                question: question,
                model: model
            });

            if (this.currentMsgEl) {
                this.currentMsgEl.remove();
            }

            const data = result.data;

            // 更新所有步骤状态
            this.updateThinkingStep('router', 'complete', '分析完成');
            this.updateThinkingStep('localdb', 'complete', `查询完成（${data.local_results_count || 0}条结果）`);
            this.updateThinkingStep('graphdb', 'complete', `查询完成（${data.graph_results_count || 0}条结果）`);
            this.updateThinkingStep('synthesizer', 'complete', '回答生成完成');
            this.addLog('全部完成！', '#4CAF50');

            // 使用 Markdown 渲染
            const renderedAnswer = Utils.renderMarkdown(data.answer);
            let html = `<div>${renderedAnswer}</div>`;

            // 模型和来源信息
            const sourceBadge = data.source && data.source.includes('agent')
                ? '<span style="color: var(--ink-green);">✓ Agent 工作链 v4</span>'
                : '<span style="color: var(--seal-red);">✓ 检索模式</span>';
            html += `<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-light); font-size: 12px; color: var(--text-muted);">
                ${sourceBadge} | 模型: ${Utils.escapeHtml(data.model)} | 耗时: ${data.elapsed_seconds || '?'}s
            </div>`;

            // 显示数据来源摘要
            if (data.local_results_count > 0 || data.graph_results_count > 0) {
                html += '<div style="margin-top: 10px; padding: 10px; background: #f0f7ff; border-radius: 6px; font-size: 12px;">';
                html += '<strong style="color: #1976d2;">📊 数据来源：</strong><br>';

                if (data.local_results_count > 0) {
                    html += `<span style="display: inline-block; margin: 4px 8px 4px 0; padding: 4px 8px; background: white; border-radius: 4px; border: 1px solid #bbdefb;">
                        🗄️ [本地数据库] ${data.local_results_count} 条（属性信息）
                    </span>`;
                }
                if (data.graph_results_count > 0) {
                    html += `<span style="display: inline-block; margin: 4px 8px 4px 0; padding: 4px 8px; background: white; border-radius: 4px; border: 1px solid #c8e6c9;">
                        🌐 [云端图谱] ${data.graph_results_count} 条（关系信息）
                    </span>`;
                }

                html += '<div style="margin-top: 6px; color: #666; font-size: 11px;">';
                html += '💡 <strong>优先级说明：</strong>关系型问题优先使用云端图谱，属性型问题优先使用本地数据库';
                html += '</div>';
                html += '</div>';
            }

            this.appendMessage('assistant', html, true);
            this.loadHistory();

        } catch (e) {
            if (this.currentMsgEl) {
                this.currentMsgEl.remove();
            }
            this.addLog(`错误: ${e.message || '未知错误'}`, '#f44336');
            this.appendMessage('assistant', `抱歉，请求失败: ${Utils.escapeHtml(e.message || '未知错误')}`);
        }

        input.disabled = false;
        input.focus();
    },

    appendMessage(role, content, isHtml) {
        const container = document.getElementById('qa-messages');
        const welcome = container.querySelector('.qa-welcome');
        if (welcome) welcome.style.display = 'none';

        const msgId = 'qa-msg-' + Date.now();
        const div = document.createElement('div');
        div.className = `qa-message qa-${role}`;
        div.id = msgId;
        div.innerHTML = isHtml ? content : Utils.escapeHtml(content);
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return msgId;
    },

    async loadHistory() {
        try {
            const result = await API.get('/api/qa/history');
            const items = result.data || [];
            const container = document.getElementById('qa-history-list');

            if (items.length === 0) {
                container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;text-align:center;">暂无问答记录</p>';
                return;
            }

            container.innerHTML = items.map(item => `
                <div class="qa-history-item">
                    <div class="qa-history-q"><strong>Q:</strong> ${Utils.truncate(item.question, 60)}</div>
                    <div class="qa-history-meta">
                        ${Utils.formatDate(item.created_at)}
                        ${item.model_name ? ` | ${Utils.escapeHtml(item.model_name)}` : ''}
                    </div>
                </div>
            `).join('');

        } catch (e) {
            /* ignore */
        }
    },

    init() {
        const input = document.getElementById('qa-input');
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.ask();
                }
            });
        }
    }
};
