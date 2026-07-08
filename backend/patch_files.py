import sys
import os

# --- PATCH MAIN.PY ---
main_path = r'd:\AIKB\backend\main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main_code = f.read()

# plan endpoint
main_code = main_code.replace(
'''    model_name = data.get("model", "Gemini Flash Core")
    system_prompt = "Kamu adalah Planner AI. Jika input user adalah sapaan ringan, percakapan santai (seperti 'halo', 'apa kabar'), atau sekadar basa-basi yang tidak butuh rencana/debat rumit, maka jawablah langsung layaknya teman mengobrol yang asik, dan WAJIB tambahkan string '[SKIP_DEBATE]' persis di akhir jawabanmu. JIKA input user adalah permintaan tugas (coding, analisis, buatan soal, dll), Buatkan rencana strategis, komprehensif, dan terstruktur langkah demi langkah untuk menjawabnya tanpa string tersebut."
    
    return StreamingResponse(
        generate_stream(model_name, system_prompt, f"Permintaan user: {question}"),
        media_type="text/event-stream"
    )''',
'''    model_name = data.get("model", "Gemini Flash Core")
    files = data.get("files", [])
    system_prompt = "Kamu adalah Planner AI. Jika input user adalah sapaan ringan, percakapan santai (seperti 'halo', 'apa kabar'), atau sekadar basa-basi yang tidak butuh rencana/debat rumit, maka jawablah langsung layaknya teman mengobrol yang asik, dan WAJIB tambahkan string '[SKIP_DEBATE]' persis di akhir jawabanmu. JIKA input user adalah permintaan tugas (coding, analisis, buatan soal, dll), Buatkan rencana strategis, komprehensif, dan terstruktur langkah demi langkah untuk menjawabnya tanpa string tersebut."
    
    return StreamingResponse(
        generate_stream(model_name, system_prompt, f"Permintaan user: {question}", files),
        media_type="text/event-stream"
    )'''
)

# debate endpoint
main_code = main_code.replace(
'''    model_name = data.get("model", "Gemini Flash Core")
    
    return StreamingResponse(
        generate_stream(model_name, system_prompt, message),
        media_type="text/event-stream"
    )''',
'''    model_name = data.get("model", "Gemini Flash Core")
    files = data.get("files", [])
    
    return StreamingResponse(
        generate_stream(model_name, system_prompt, message, files),
        media_type="text/event-stream"
    )'''
)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_code)


# --- PATCH AGENTS.PY ---
agents_path = r'd:\AIKB\backend\agents.py'
with open(agents_path, 'r', encoding='utf-8') as f:
    agents_code = f.read()

# imports
if 'import base64' not in agents_code:
    agents_code = agents_code.replace('import json\n', 'import json\nimport base64\nimport io\ntry:\n    from docx import Document\nexcept ImportError:\n    pass\ntry:\n    import PyPDF2\nexcept ImportError:\n    pass\n')

# function signature
agents_code = agents_code.replace(
    'async def generate_stream(model_name: str, system_prompt: str, message: str) -> AsyncGenerator[str, None]:',
    '''async def generate_stream(model_name: str, system_prompt: str, message: str, files: list = None) -> AsyncGenerator[str, None]:
    if files is None:
        files = []
        
    extracted_text = ""
    gemini_parts = []
    
    for f in files:
        mime = f.get("mime", "")
        name = f.get("name", "file")
        b64 = f.get("data", "")
        
        try:
            if "pdf" in mime:
                pdf_bytes = base64.b64decode(b64)
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\\n"
                extracted_text += f"\\n\\n[Isi Lampiran Dokumen '{name}']:\\n{text}"
            elif "word" in mime or "officedocument.word" in mime:
                doc_bytes = base64.b64decode(b64)
                doc = Document(io.BytesIO(doc_bytes))
                text = "\\n".join([p.text for p in doc.paragraphs])
                extracted_text += f"\\n\\n[Isi Lampiran Dokumen '{name}']:\\n{text}"
            elif "text" in mime:
                text = base64.b64decode(b64).decode('utf-8')
                extracted_text += f"\\n\\n[Isi Lampiran Dokumen '{name}']:\\n{text}"
            elif "image" in mime:
                img_bytes = base64.b64decode(b64)
                gemini_parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
                extracted_text += f"\\n\\n[User melampirkan gambar '{name}', namun gambar ini hanya bisa dilihat oleh Gemini. Jika kamu model teks, abaikan visual gambar ini dan fokus pada teks.]"
        except Exception as e:
            print(f"Error parsing file {name}: {e}")
            
    if extracted_text:
        message = extracted_text + "\\n\\n[PESAN UTAMA USER]:\\n" + message
        
    gemini_parts.append(message)
    '''
)

# gemini call
agents_code = agents_code.replace(
    'contents=[message],',
    'contents=gemini_parts,'
)

with open(agents_path, 'w', encoding='utf-8') as f:
    f.write(agents_code)


# --- PATCH INDEX.HTML ---
index_path = r'd:\AIKB\frontend\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    index_code = f.read()

# add file input UI
if '<input type="file" id="fileInput"' not in index_code:
    index_code = index_code.replace(
        '<div class="input-row">',
        '''
        <div id="filePreviewContainer" style="display:flex; gap:10px; padding:0 20px; flex-wrap:wrap; margin-bottom:10px;"></div>
        <div class="input-row">
            <input type="file" id="fileInput" multiple style="display:none" onchange="handleFileSelect(event)">
            <button class="send-btn" onclick="document.getElementById('fileInput').click()" style="background:#555; margin-right:5px;" title="Lampirkan File (PDF, Word, TXT, Gambar)">📎</button>
        '''
    )

# add file JS
if 'let currentFiles = [];' not in index_code:
    file_js = '''
        let currentFiles = [];
        
        function handleFileSelect(e) {
            for(let file of e.target.files) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    const b64 = evt.target.result.split(',')[1];
                    currentFiles.push({
                        name: file.name,
                        mime: file.type || "application/octet-stream",
                        data: b64,
                        url: evt.target.result // for image preview
                    });
                    renderFilePreview();
                };
                reader.readAsDataURL(file);
            }
            e.target.value = ''; // reset
        }
        
        function renderFilePreview() {
            const container = document.getElementById('filePreviewContainer');
            container.innerHTML = '';
            currentFiles.forEach((f, i) => {
                const chip = document.createElement('div');
                chip.style.cssText = 'background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 12px; font-size: 0.8rem; display: flex; align-items: center; gap: 5px; color: #fff;';
                if(f.mime.includes('image')) {
                    chip.innerHTML = `<img src="${f.url}" style="width:20px; height:20px; border-radius:4px; object-fit:cover;"> <span>${f.name}</span> <span style="cursor:pointer; color:#ff4444;" onclick="removeFile(${i})">✕</span>`;
                } else {
                    chip.innerHTML = `<span>📄 ${f.name}</span> <span style="cursor:pointer; color:#ff4444;" onclick="removeFile(${i})">✕</span>`;
                }
                container.appendChild(chip);
            });
        }
        
        function removeFile(index) {
            currentFiles.splice(index, 1);
            renderFilePreview();
        }
    '''
    index_code = index_code.replace('let isRecording = false;', 'let isRecording = false;\n' + file_js)

# modify startPlanning logic to store files in history and send them
index_code = index_code.replace(
    'chat.messages.push({ type: \'user\', content: question }); saveHistory();',
    'chat.messages.push({ type: \'user\', content: question, files: [...currentFiles] }); saveHistory();'
)

# include files in /plan API call
index_code = index_code.replace(
    "await streamAPI('plan', { question: question, model: MODELS[pKey].name }, (chunk) => {",
    "const payloadFiles = [...currentFiles];\n                currentFiles = []; renderFilePreview();\n                await streamAPI('plan', { question: question, model: MODELS[pKey].name, files: payloadFiles }, (chunk) => {"
)

# modify startDebate to send the saved files
# Wait, in startDebate, we need to get the files from the user message!
index_code = index_code.replace(
    "const userMsg = (r === 1 && agent.role === 'answerer')",
    '''
                    const userMessageObj = chat.messages.find(m => m.type === 'user');
                    const debateFiles = userMessageObj ? (userMessageObj.files || []) : [];
                    const userMsg = (r === 1 && agent.role === 'answerer')'''
)

index_code = index_code.replace(
    "message: userMsg,",
    "message: userMsg,\n                            files: debateFiles,"
)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_code)

print('Patched files successfully!')
