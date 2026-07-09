import sys

path = r'd:\AIKB\backend\agents.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

old_logic = '''        # Karena API Key Free Tier terkena limit 0 untuk 3.1-Pro dan 404/503 untuk model lain,
        # kita force menggunakan 'gemini-1.5-flash' yang limitnya jauh lebih besar (1500 per hari).
        actual_model = "gemini-1.5-flash"
        
        try:
            def fetch_gemini():
                return gemini_client.models.generate_content_stream(
                    model=actual_model,
                    contents=gemini_parts,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7
                    )
                )
            
            stream = await asyncio.to_thread(fetch_gemini)
            for chunk in stream:
                if chunk.text:
                    yield f"data: {json.dumps({'content': chunk.text})}\\n\\n"
                    await asyncio.sleep(0.01)
        except Exception as e:
            yield f"data: {json.dumps({'content': f'[Error Gemini: {str(e)}]'})}\\n\\n"'''

new_logic = '''        # Gunakan model terbaru, tapi siapkan fallback ke 1.5 jika kena limit
        actual_model = "gemini-flash-latest"
        
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
                # Ambil chunk pertama untuk tes apakah error (API melempar error saat iterasi pertama)
                # karena stream bukan list, kita bisa pakai iterasi biasa yang langsung tertangkap exception
                for chunk in stream:
                    if chunk.text:
                        yield f"data: {json.dumps({'content': chunk.text})}\\n\\n"
                        await asyncio.sleep(0.01)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "exhausted" in err_str or "quota" in err_str:
                    # Fallback ke gemini-1.5-flash
                    stream_fallback = await asyncio.to_thread(fetch_gemini, "gemini-1.5-flash")
                    for chunk in stream_fallback:
                        if chunk.text:
                            yield f"data: {json.dumps({'content': chunk.text})}\\n\\n"
                            await asyncio.sleep(0.01)
                else:
                    raise e
                    
        except Exception as e:
            yield f"data: {json.dumps({'content': f'[Error Gemini: {str(e)}]'})}\\n\\n"'''

code = code.replace(old_logic, new_logic)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('Patched agents.py fallback!')
