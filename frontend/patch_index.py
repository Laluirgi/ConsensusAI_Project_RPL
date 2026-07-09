import sys
import re

path = r'd:\AIKB\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. currentPlanText reset
code = code.replace(
    'const chat = chatHistory.find(c => c.id === activeChatId);',
    'const chat = chatHistory.find(c => c.id === activeChatId);\n            currentPlanText = "";'
)

# 2. Add mermaid CDN and styling
code = code.replace(
    '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>',
    '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>\n    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>'
)
code = code.replace(
    '/* ====== THEME & BASE ====== */',
    '''/* ====== THEME & BASE ====== */
        .code-wrapper { position: relative; margin-bottom: 1rem; }
        .btn-copy-code { position: absolute; top: 5px; right: 5px; z-index: 10; padding: 4px 8px; font-size: 0.8rem; opacity: 0.7; }
        .btn-copy-code:hover { opacity: 1; }
        .mermaid { background: white; padding: 10px; border-radius: 8px; margin-bottom: 1rem; }
    '''
)

# 3. Add Mermaid initialization
code = code.replace(
    "mermaid.initialize({ startOnLoad: true });", ""
) # Just in case
code = code.replace(
    '// ── Parse markdown ──',
    '''// ── Parse markdown ──
        mermaid.initialize({ startOnLoad: false, theme: 'default' });
        const renderer = new marked.Renderer();
        renderer.code = function(code, language) {
            if (language === 'mermaid') {
                return `<div class="mermaid">${code}</div>`;
            }
            let highlighted = code;
            if (language && hljs.getLanguage(language)) {
                try { highlighted = hljs.highlight(code, { language }).value; } catch (__) {}
            } else {
                highlighted = hljs.highlightAuto(code).value;
            }
            return `<div class="code-wrapper"><button class="btn-action btn-copy-code" onclick="navigator.clipboard.writeText(decodeURIComponent('${encodeURIComponent(code)}'))">📋 Salin Kode</button><pre><code class="hljs ${language}">${highlighted}</code></pre></div>`;
        };
        marked.use({ renderer });
    '''
)

# Fix parseMarkdown to trigger mermaid and use marked.parse instead of marked() if needed, but the original code used parseMarkdown.
code = code.replace(
    'function parseMarkdown(text) {',
    '''function parseMarkdown(text) {
            setTimeout(() => {
                try { mermaid.init(undefined, document.querySelectorAll('.mermaid')); } catch(e){}
            }, 100);'''
)

# Wait, the original parseMarkdown was:
# function parseMarkdown(text) {
#    return marked.parse(text);
# }
# So replacing it will work.

# 4. Add Voice Input
code = code.replace(
    '<button class="send-btn" id="sendBtn" onclick="startPlanning()">↑</button>',
    '<button class="send-btn" id="micBtn" onclick="toggleMic()" style="background:#555; margin-right:5px;">🎙️</button>\n                    <button class="send-btn" id="sendBtn" onclick="startPlanning()">↑</button>'
)

code = code.replace(
    'let activeChatId = null; saveHistory();',
    '''let activeChatId = null; saveHistory();
        
        // ── Voice Input ──
        let recognition;
        let isRecording = false;
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'id-ID';
            recognition.onresult = function(event) {
                const text = event.results[0][0].transcript;
                const input = document.getElementById('questionInput');
                input.value += (input.value ? ' ' : '') + text;
                autoResize(input);
            };
            recognition.onend = function() {
                isRecording = false;
                document.getElementById('micBtn').style.background = '#555';
            };
        }
        function toggleMic() {
            if (!recognition) return alert('Browser tidak mendukung voice input.');
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
                isRecording = true;
                document.getElementById('micBtn').style.background = 'red';
            }
        }
    '''
)

# 5. Add Planner Select to settings
code = code.replace(
    '<div class="setting-item">\n                <div class="setting-label">Iterasi Debat',
    '''<div class="setting-item">
                <div class="setting-label">Planner Model</div>
                <select id="plannerModelSelect" class="settings-select">
                    <option value="gemini_pro">Gemini Flash Core</option>
                    <option value="gemini_flash">Gemini Flash Fast</option>
                    <option value="llama">LLaMA 3.3 70B</option>
                    <option value="mixtral">Mixtral 8x7B</option>
                </select>
            </div>
            <div class="setting-item">\n                <div class="setting-label">Iterasi Debat'''
)

# Update startPlanning to use plannerModelSelect
code = code.replace(
    "await streamAPI('plan', { question: question }, (chunk) => {",
    "const pKey = document.getElementById('plannerModelSelect')?.value || 'gemini_pro';\n                await streamAPI('plan', { question: question, model: MODELS[pKey].name }, (chunk) => {"
)
code = code.replace(
    "appendThinking('Gemini Flash Core (Planner)')",
    "appendThinking((MODELS[document.getElementById('plannerModelSelect')?.value || 'gemini_pro'].name) + ' (Planner)')"
)
code = code.replace(
    "name: 'Gemini Flash Core · Planner'",
    "name: (MODELS[document.getElementById('plannerModelSelect')?.value || 'gemini_pro'].name) + ' · Planner'"
)
code = code.replace(
    "name: isSkipDebate ? 'Gemini Flash Core'",
    "name: isSkipDebate ? MODELS[document.getElementById('plannerModelSelect')?.value || 'gemini_pro'].name"
)
code = code.replace(
    ".textContent = 'Gemini Flash Core'",
    ".textContent = MODELS[document.getElementById('plannerModelSelect')?.value || 'gemini_pro'].name"
)
code = code.replace(
    '<span class="bubble-name">Gemini Flash Core · Planner</span>',
    '<span class="bubble-name">${MODELS[document.getElementById(\'plannerModelSelect\')?.value || \'gemini_pro\'].name} · Planner</span>'
)

# 6. Fix Manual Roles
code = code.replace(
    'let autoRoleAssign = true;',
    'let autoRoleAssign = true; let manualRolesMap = {};'
)
code = code.replace(
    'closeSettings();',
    '''document.querySelectorAll('.rmi-role-select').forEach(sel => {
                manualRolesMap[sel.dataset.model] = sel.value;
            });
            closeSettings();'''
)

code = code.replace(
    '''role: ROLES[Math.min(i, ROLES.length - 2)],
                roleLabel: ROLE_LABELS[Math.min(i, ROLES.length - 2)],''',
    '''role: autoRoleAssign ? ROLES[Math.min(i, ROLES.length - 2)] : (manualRolesMap[key] || ROLES[0]),
                roleLabel: autoRoleAssign ? ROLE_LABELS[Math.min(i, ROLES.length - 2)] : ROLE_LABELS[ROLES.indexOf(manualRolesMap[key] || ROLES[0])],'''
)

# 7. Add Export Download logic
export_js = '''
        async function downloadFile(format) {
            const consensusEl = document.querySelector('#finalConsensus .consensus-body');
            if(!consensusEl) return;
            const text = consensusEl.innerText;
            try {
                const res = await fetch('http://localhost:8000/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: text, format: format })
                });
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `consensus_result.${format}`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch(e) { alert('Gagal ekspor: ' + e.message); }
        }
'''
code = code.replace('function downloadTxt() {', export_js + 'function downloadTxt() {')

code = code.replace(
    '<button class="btn-action" onclick="downloadPdf()">📥 Unduh PDF</button>',
    '''<button class="btn-action" onclick="downloadPdf()">📥 Unduh PDF</button>
          ${originalQuestion.toLowerCase().includes('word') || originalQuestion.toLowerCase().includes('docx') ? '<button class="btn-action" onclick="downloadFile(\\'docx\\')">📥 Unduh Word</button>' : ''}
          ${originalQuestion.toLowerCase().includes('excel') || originalQuestion.toLowerCase().includes('spreadsheet') || originalQuestion.toLowerCase().includes('xlsx') ? '<button class="btn-action" onclick="downloadFile(\\'xlsx\\')">📥 Unduh Excel</button>' : ''}'''
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('Patched index.html!')
