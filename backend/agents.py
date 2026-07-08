import os
import json
import base64
import io
import re
try:
    from docx import Document
except ImportError:
    pass
try:
    import PyPDF2
except ImportError:
    pass
import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv

from google import genai
from google.genai import types
from groq import AsyncGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY and "masukkan" not in GROQ_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY and "masukkan" not in GEMINI_API_KEY else None

# ── Model Mapping ──
# Gemini Flash → via Google GenAI API
# Semua lainnya → via Groq API
MODEL_MAP = {
    "LLaMA 3.3 70B": "llama-3.3-70b-versatile",
    "LLaMA 3.1 8B": "llama-3.1-8b-instant",
    "GPT-OSS 120B": "openai/gpt-oss-120b",
    "Qwen 3 32B": "qwen/qwen3-32b",
}

GEMINI_MODEL_NAME = "Gemini Flash"


def parse_consensus_status(text: str) -> dict:
    """Parse [SETUJU] atau [BELUM SETUJU] dari akhir respons AI.
    
    Returns:
        { "agreed": bool, "clean_text": str }
    """
    clean = text.strip()
    
    # Cek [SETUJU] di akhir teks (case insensitive)
    setuju_pattern = re.compile(r'\[SETUJU\]\s*$', re.IGNORECASE)
    belum_pattern = re.compile(r'\[BELUM\s*SETUJU\]\s*$', re.IGNORECASE)
    
    if belum_pattern.search(clean):
        clean_text = belum_pattern.sub('', clean).strip()
        return {"agreed": False, "clean_text": clean_text}
    elif setuju_pattern.search(clean):
        clean_text = setuju_pattern.sub('', clean).strip()
        return {"agreed": True, "clean_text": clean_text}
    else:
        # Tidak ada tag → anggap belum setuju
        return {"agreed": False, "clean_text": clean}


def extract_file_content(files: list) -> tuple:
    """Extract text and image parts from uploaded files.
    
    Returns:
        (extracted_text: str, gemini_parts: list)
    """
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
                    text += page.extract_text() + "\n"
                extracted_text += f"\n\n[Isi Lampiran Dokumen '{name}']:\n{text}"
            elif "word" in mime or "officedocument.word" in mime:
                doc_bytes = base64.b64decode(b64)
                doc = Document(io.BytesIO(doc_bytes))
                text = "\n".join([p.text for p in doc.paragraphs])
                extracted_text += f"\n\n[Isi Lampiran Dokumen '{name}']:\n{text}"
            elif "text" in mime:
                text = base64.b64decode(b64).decode('utf-8')
                extracted_text += f"\n\n[Isi Lampiran Dokumen '{name}']:\n{text}"
            elif "image" in mime:
                img_bytes = base64.b64decode(b64)
                gemini_parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
                extracted_text += f"\n\n[User melampirkan gambar '{name}'. Jika kamu model teks non-Gemini, abaikan visual gambar ini.]"
        except Exception as e:
            print(f"Error parsing file {name}: {e}")
    
    return extracted_text, gemini_parts


async def generate_stream(model_name: str, system_prompt: str, message: str, files: list = None) -> AsyncGenerator[str, None]:
    """Stream respons dari AI model (Gemini atau Groq)."""
    if files is None:
        files = []
    
    extracted_text, gemini_parts = extract_file_content(files)
    
    if extracted_text:
        message = extracted_text + "\n\n[PESAN UTAMA USER]:\n" + message
    
    gemini_parts.append(message)
    
    if model_name == GEMINI_MODEL_NAME:
        # ── Gemini Flash via Google GenAI API ──
        if not gemini_client:
            yield f"data: {json.dumps({'content': '[Error: Gemini API Key belum di-set di .env]'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        actual_model = "gemini-2.0-flash-lite"
        
        try:
            def fetch_gemini(mdl):
                return gemini_client.models.generate_content_stream(
                    model=mdl,
                    contents=gemini_parts,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7
                    )
                )
            
            try:
                stream = await asyncio.to_thread(fetch_gemini, actual_model)
                for chunk in stream:
                    if chunk.text:
                        yield f"data: {json.dumps({'content': chunk.text})}\n\n"
                        await asyncio.sleep(0.01)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "exhausted" in err_str or "quota" in err_str:
                    # Opsi A: Fallback langsung ke LLaMA 3.3 70B jika Gemini limit
                    yield f"data: {json.dumps({'rate_limit': True, 'model': 'Gemini Flash'})}\n\n"
                    
                    if groq_client:
                        llama_model = MODEL_MAP.get("LLaMA 3.3 70B")
                        try:
                            stream_llama = await groq_client.chat.completions.create(
                                model=llama_model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": message}
                                ],
                                stream=True,
                                temperature=0.7
                            )
                            async for chunk in stream_llama:
                                if chunk.choices[0].delta.content:
                                    text = chunk.choices[0].delta.content
                                    yield f"data: {json.dumps({'content': text})}\n\n"
                        except Exception as fallback_e:
                            yield f"data: {json.dumps({'content': f'[Error Fallback LLaMA: {str(fallback_e)}]'})}\n\n"
                else:
                    yield f"data: {json.dumps({'content': f'[Error Gemini: {str(e)}]'})}\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'content': f'[Error Gemini: {str(e)}]'})}\n\n"
            
    else:
        # ── Groq API (LLaMA, Mixtral, DeepSeek R1, Gemma 2) ──
        if not groq_client:
            yield f"data: {json.dumps({'content': '[Error: Groq API Key belum di-set di .env]'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        actual_model = MODEL_MAP.get(model_name, "llama-3.3-70b-versatile")
        try:
            stream = await groq_client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                stream=True,
                temperature=0.7
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'content': text})}\n\n"
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "rate limit" in err_str:
                yield f"data: {json.dumps({'rate_limit': True, 'model': model_name})}\n\n"
                # Skip debate token
                yield f"data: {json.dumps({'content': '[SKIP_DEBATE]'})}\n\n"
            else:
                yield f"data: {json.dumps({'content': f'[Error Groq: {str(e)}]'})}\n\n"
            
    yield "data: [DONE]\n\n"
