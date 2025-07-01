// API基础URL
const API_BASE = '/api';

// 状态管理
let scripts = [];
let templates = [];
let currentScriptId = null;
let hasUnsavedChanges = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    loadScripts();
    loadTemplates();
    
    // 绑定表单提交事件
    document.getElementById('scriptForm').addEventListener('submit', saveScript);
    
    // 监听表单变化
    const formInputs = document.querySelectorAll('#scriptForm input, #scriptForm textarea, #scriptForm select');
    formInputs.forEach(input => {
        input.addEventListener('change', () => {
            hasUnsavedChanges = true;
        });
        input.addEventListener('input', () => {
            hasUnsavedChanges = true;
        });
    });
    
    // 监听cron表达式输入变化
    document.getElementById('cronExpression').addEventListener('input', debounce(updateCronDescription, 500));
});

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 更新cron描述
async function updateCronDescription() {
    const cronExpression = document.getElementById('cronExpression').value.trim();
    const descriptionDiv = document.getElementById('cronDescription');
    
    if (!cronExpression) {
        descriptionDiv.textContent = '请输入cron表达式';
        descriptionDiv.className = 'cron-description';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/cron/parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cron_expression: cronExpression })
        });
        
        const result = await response.json();
        
        if (result.valid) {
            descriptionDiv.textContent = result.description;
            descriptionDiv.className = 'cron-description valid';
        } else {
            descriptionDiv.textContent = result.description;
            descriptionDiv.className = 'cron-description invalid';
        }
    } catch (error) {
        descriptionDiv.textContent = '解析失败';
        descriptionDiv.className = 'cron-description invalid';
    }
}

// 将UTC时间转换为北京时间
function toBeijingTime(utcTimeStr) {
    if (!utcTimeStr) return '';
    
    const date = new Date(utcTimeStr);
    // 添加8小时转换为北京时间
    const beijingDate = new Date(date.getTime() + 8 * 60 * 60 * 1000);
    
    return beijingDate.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// 加载脚本列表
async function loadScripts() {
    try {
        const response = await fetch(`${API_BASE}/scripts`);
        scripts = await response.json();
        renderScripts();
    } catch (error) {
        console.error('加载脚本失败:', error);
        alert('加载脚本失败，请刷新页面重试');
    }
}

// 加载模板列表
async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/templates`);
        templates = await response.json();
    } catch (error) {
        console.error('加载模板失败:', error);
    }
}

// 渲染脚本列表
function renderScripts() {
    const grid = document.getElementById('scriptsGrid');
    
    if (scripts.length === 0) {
        grid.innerHTML = '<div class="empty-state">还没有脚本，点击上方按钮创建第一个脚本</div>';
        return;
    }
    
    grid.innerHTML = scripts.map(script => {
        let scheduleInfo = '';
        if (script.cron_expression) {
            scheduleInfo = `Cron: ${script.cron_expression}`;
            if (script.next_run_time) {
                scheduleInfo += `<br><small>下次运行: ${script.next_run_time}</small>`;
            }
        } else {
            scheduleInfo = '手动运行';
        }
        
        return `
            <div class="script-card">
                <div class="script-header">
                    <h3>${escapeHtml(script.name)}</h3>
                    <div class="script-status ${script.is_active ? 'active' : 'inactive'}">
                        ${script.is_active ? '运行中' : '已停止'}
                    </div>
                </div>
                <p class="script-description">${escapeHtml(script.description || '无描述')}</p>
                <div class="script-meta">
                    <span>${scheduleInfo}</span>
                </div>
                <div class="script-actions">
                    <button class="btn btn-sm" onclick="runScript(${script.id})">▶ 运行</button>
                    <button class="btn btn-sm" onclick="editScript(${script.id})">✏️ 编辑</button>
                    <button class="btn btn-sm" onclick="showHistory(${script.id})">📊 历史</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteScript(${script.id})">🗑️ 删除</button>
                </div>
            </div>
        `;
    }).join('');
}

// 显示创建脚本模态框
function showCreateScriptModal() {
    currentScriptId = null;
    hasUnsavedChanges = false;
    document.getElementById('modalTitle').textContent = '创建新脚本';
    document.getElementById('scriptForm').reset();
    document.getElementById('scriptId').value = '';
    document.getElementById('cronExpression').value = '';
    document.getElementById('cronDescription').textContent = '请输入cron表达式';
    document.getElementById('cronDescription').className = 'cron-description';
    document.getElementById('scriptModal').style.display = 'block';
}

// 编辑脚本
function editScript(id) {
    const script = scripts.find(s => s.id === id);
    if (!script) return;
    
    currentScriptId = id;
    hasUnsavedChanges = false;
    document.getElementById('modalTitle').textContent = '编辑脚本';
    document.getElementById('scriptId').value = id;
    document.getElementById('scriptName').value = script.name;
    document.getElementById('scriptDescription').value = script.description || '';
    document.getElementById('cronExpression').value = script.cron_expression || '';
    document.getElementById('scriptActive').checked = script.is_active;
    document.getElementById('scriptCode').value = script.code;
    
    // 更新cron描述
    updateCronDescription();
    
    document.getElementById('scriptModal').style.display = 'block';
}

// 保存脚本
async function saveScript(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('scriptName').value.trim(),
        description: document.getElementById('scriptDescription').value.trim(),
        code: document.getElementById('scriptCode').value,
        cron_expression: document.getElementById('cronExpression').value.trim(),
        is_active: document.getElementById('scriptActive').checked
    };
    
    // 验证必填字段
    if (!formData.name) {
        alert('请输入脚本名称');
        return;
    }
    
    if (!formData.code) {
        alert('请输入脚本代码');
        return;
    }
    
    try {
        let response;
        const isUpdating = !!currentScriptId;

        if (isUpdating) {
            response = await fetch(`${API_BASE}/scripts/${currentScriptId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        } else {
            response = await fetch(`${API_BASE}/scripts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        }
        
        if (response.ok) {
            hasUnsavedChanges = false;
            const successMessage = isUpdating ? '脚本更新成功！' : '脚本创建成功！';
            closeScriptModal();
            loadScripts();
            alert(successMessage);
        } else {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.message || '保存失败');
        }
    } catch (error) {
        console.error('保存脚本失败:', error);
        alert('保存脚本失败：' + error.message);
    }
}

// 运行脚本
async function runScript(id) {
    if (!confirm('确定要立即运行这个脚本吗？')) return;
    
    try {
        const response = await fetch(`${API_BASE}/scripts/${id}/run`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                alert('脚本运行成功！\n输出：' + (result.output || '无输出').substring(0, 200));
            } else {
                alert('脚本运行失败！\n错误：' + (result.error || '未知错误'));
            }
        } else {
            throw new Error('运行失败');
        }
    } catch (error) {
        console.error('运行脚本失败:', error);
        alert('运行脚本失败，请重试');
    }
}

// 删除脚本
async function deleteScript(id) {
    if (!confirm('确定要删除这个脚本吗？此操作不可恢复。')) return;
    
    try {
        const response = await fetch(`${API_BASE}/scripts/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadScripts();
            alert('脚本删除成功！');
        } else {
            throw new Error('删除失败');
        }
    } catch (error) {
        console.error('删除脚本失败:', error);
        alert('删除脚本失败，请重试');
    }
}

// 显示运行历史
async function showHistory(scriptId) {
    try {
        const response = await fetch(`${API_BASE}/scripts/${scriptId}/runs`);
        const runs = await response.json();
        
        const historyList = document.getElementById('historyList');
        
        if (runs.length === 0) {
            historyList.innerHTML = '<div class="empty-state">暂无运行记录</div>';
        } else {
            historyList.innerHTML = runs.map(run => `
                <div class="history-item ${run.status}">
                    <div class="history-header">
                        <span class="history-time">${toBeijingTime(run.created_at)}</span>
                        <span class="history-status">${getStatusText(run.status)}</span>
                    </div>
                    ${run.output ? `<pre class="history-output">${escapeHtml(run.output)}</pre>` : ''}
                    ${run.error ? `<pre class="history-error">${escapeHtml(run.error)}</pre>` : ''}
                </div>
            `).join('');
        }
        
        document.getElementById('historyModal').style.display = 'block';
    } catch (error) {
        console.error('加载运行历史失败:', error);
        alert('加载运行历史失败，请重试');
    }
}

// 显示模板选择模态框
function showTemplatesModal() {
    const grid = document.getElementById('templatesGrid');
    
    grid.innerHTML = templates.map((template, index) => `
        <div class="template-card" onclick="useTemplate(${index})">
            <h4>${escapeHtml(template.name)}</h4>
            <p>${escapeHtml(template.description)}</p>
        </div>
    `).join('');
    
    document.getElementById('templatesModal').style.display = 'block';
}

// 使用模板
function useTemplate(index) {
    const template = templates[index];
    if (!template) return;
    
    document.getElementById('scriptName').value = template.name;
    document.getElementById('scriptDescription').value = template.description;
    document.getElementById('scriptCode').value = template.code;
    hasUnsavedChanges = true;
    
    closeTemplatesModal();
}

// 关闭模态框函数
function closeScriptModal() {
    if (hasUnsavedChanges) {
        if (!confirm('有未保存的更改，确定要关闭吗？')) {
            return;
        }
    }
    document.getElementById('scriptModal').style.display = 'none';
    currentScriptId = null;
    hasUnsavedChanges = false;
}

function closeTemplatesModal() {
    document.getElementById('templatesModal').style.display = 'none';
}

function closeHistoryModal() {
    document.getElementById('historyModal').style.display = 'none';
}

// 插入常用cron表达式
function insertCronPreset() {
    const preset = document.getElementById('cronPreset').value;
    if (preset) {
        document.getElementById('cronExpression').value = preset;
        hasUnsavedChanges = true;
        updateCronDescription();
    }
}

// 工具函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getStatusText(status) {
    const statusMap = {
        'running': '运行中',
        'success': '成功',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

// 点击模态框外部关闭 - 现在需要确认
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        if (event.target.id === 'scriptModal' && hasUnsavedChanges) {
            if (!confirm('有未保存的更改，确定要关闭吗？')) {
                return;
            }
        }
        event.target.style.display = 'none';
        if (event.target.id === 'scriptModal') {
            currentScriptId = null;
            hasUnsavedChanges = false;
        }
    }
}