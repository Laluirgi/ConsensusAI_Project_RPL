# 📖 Consensus AI — Dokumentasi Lengkap Proyek

> **Multi-AI Discussion Platform** — Platform yang menggabungkan perspektif dari beberapa model AI berbeda untuk menghasilkan jawaban terbaik melalui mekanisme diskusi dan konsensus.

---

## 📑 Daftar Isi

1. [Gambaran Umum](#-gambaran-umum)
2. [Tech Stack](#-tech-stack)
3. [Arsitektur Sistem](#-arsitektur-sistem)
4. [Alur Kerja Aplikasi](#-alur-kerja-aplikasi)
5. [Struktur File & Penjelasan](#-struktur-file--penjelasan)
6. [API Endpoints](#-api-endpoints)
7. [Model AI yang Digunakan](#-model-ai-yang-digunakan)
8. [Database Schema](#-database-schema)
9. [Fitur-Fitur Utama](#-fitur-fitur-utama)
10. [Cara Instalasi & Menjalankan](#-cara-instalasi--menjalankan)
11. [Environment Variables](#-environment-variables)
12. [Kontributor](#-kontributor)

---

## 🌟 Gambaran Umum

**Consensus AI** adalah platform diskusi berbasis web yang memanfaatkan **beberapa model AI** secara bersamaan. Alih-alih hanya mengandalkan satu AI, platform ini mempertemukan hingga **5 model AI** dalam sebuah "debat" multi-ronde untuk mencapai **konsensus** — jawaban final yang menggabungkan insight terbaik dari semua perspektif AI.

### Konsep Utama

| Konsep | Penjelasan |
|--------|-----------|
| **Multi-AI Consensus** | 5 model AI berdiskusi dalam beberapa ronde untuk menghasilkan jawaban terbaik |
| **Planner Phase** | Satu AI membuat rencana strategis sebelum diskusi dimulai |
| **Debate Phase** | Setiap AI memberikan perspektifnya, saling mengoreksi dan melengkapi |
| **Consensus Phase** | Jawaban final yang menggabungkan semua insight terbaik |
| **Solo Mode** | Mode alternatif untuk bertanya ke satu AI saja tanpa debat |

---

## 🛠 Tech Stack

### Backend
| Teknologi | Fungsi |
|-----------|--------|
| **Python 3.x** | Bahasa pemrograman utama backend |
| **FastAPI** | Framework web API (async, high-performance) |
| **Uvicorn** | ASGI server untuk menjalankan FastAPI |
| **Google GenAI SDK** (`google-genai`) | Koneksi ke model Gemini dari Google |
| **Groq SDK** (`groq`) | Koneksi ke model LLaMA, GPT-OSS, Qwen via Groq Cloud |
| **aiosqlite** | Database SQLite asinkronus |
| **python-dotenv** | Manajemen environment variables |
| **python-docx** | Generate file Word (.docx) untuk export |
| **openpyxl** | Generate file Excel (.xlsx) untuk export |
| **PyPDF2** | Parsing file PDF yang diupload user |

### Frontend
| Teknologi | Fungsi |
|-----------|--------|
| **HTML5 + CSS3 + JavaScript (Vanilla)** | Single-page application tanpa framework |
| **marked.js** | Rendering Markdown ke HTML |
| **DOMPurify** | Sanitasi HTML untuk keamanan (XSS prevention) |
| **highlight.js** | Syntax highlighting untuk blok kode |
| **html2pdf.js** | Export ke PDF dari browser |
| **Web Speech API** | Voice input (speech-to-text) |
| **Google Fonts (Inter, JetBrains Mono)** | Typography |

### Data Storage
| Teknologi | Fungsi |
|-----------|--------|
| **SQLite** (`consensus.db`) | Menyimpan feedback & rating (server-side) |
| **localStorage** | Menyimpan riwayat chat, settings, dan session user (client-side) |

---

## 🏗 Arsitektur Sistem

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (Browser)                 │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ index.html│  │admin.html│  │  localStorage     │  │
│  │ (Main UI)│  │(Admin UI)│  │  - Chat History    │  │
│  │          │  │          │  │  - User Session    │  │
│  │          │  │          │  │  - Settings        │  │
│  └────┬─────┘  └────┬─────┘  └───────────────────┘  │
│       │              │                                │
│       └──────┬───────┘                                │
│              │  HTTP / SSE (Server-Sent Events)       │
└──────────────┼────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│               BACKEND (FastAPI @ port 8000)           │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ main.py  │  │ agents.py│  │   database.py     │   │
│  │ (Routes) │  │ (AI Core)│  │   (SQLite ORM)    │   │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       │              │                  │             │
│       │              │           ┌──────┴──────┐     │
│       │              │           │ consensus.db │     │
│       │              │           └─────────────┘     │
│       │              │                                │
│       │         ┌────┴────────────────┐               │
│       │         │    AI Provider APIs  │               │
│       │         │  ┌────────────────┐  │               │
│       │         │  │ Google GenAI   │  │               │
│       │         │  │ (Gemini Flash) │  │               │
│       │         │  └────────────────┘  │               │
│       │         │  ┌────────────────┐  │               │
│       │         │  │   Groq Cloud   │  │               │
│       │         │  │ (LLaMA, Qwen,  │  │               │
│       │         │  │  GPT-OSS)      │  │               │
│       │         │  └────────────────┘  │               │
│       │         └─────────────────────┘               │
└───────┴───────────────────────────────────────────────┘
```

### Komunikasi

- **Frontend → Backend**: HTTP POST requests dengan JSON body
- **Backend → Frontend**: Server-Sent Events (SSE) untuk streaming respons AI secara real-time
- **Backend → AI APIs**: REST API calls ke Google GenAI dan Groq Cloud

---

## 🔄 Alur Kerja Aplikasi

### Mode Konsensus (Multi-AI Discussion)

```
User mengetik pertanyaan
        │
        ▼
┌─ FASE 1: PLANNING ─────────────────────────┐
│  POST /plan                                  │
│  Planner AI membuat rencana strategis        │
│                                              │
│  Jika pertanyaan ringan (sapaan/basa-basi):  │
│    → Jawab langsung + [SKIP_DEBATE]          │
│    → Selesai (tanpa debat)                   │
│                                              │
│  Jika pertanyaan serius:                     │
│    → Buat rencana langkah demi langkah       │
│    → User bisa Setujui / Revisi              │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─ FASE 2: DEBATE (Maks 5 Ronde) ────────────┐
│  POST /debate (per model per ronde)          │
│                                              │
│  Untuk setiap ronde:                         │
│    Untuk setiap model AI aktif:              │
│      1. Baca riwayat diskusi sebelumnya      │
│      2. Berikan perspektif sendiri           │
│      3. Koreksi kesalahan model lain         │
│      4. Tag [SETUJU] atau [BELUM SETUJU]     │
│                                              │
│  Jika SEMUA model [SETUJU] → Lanjut Final   │
│  Jika maks ronde tercapai → Lanjut Final    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─ FASE 3: KONSENSUS FINAL ──────────────────┐
│  POST /debate (model pertama)                │
│                                              │
│  Gabungkan semua insight terbaik menjadi     │
│  jawaban final yang komprehensif             │
│                                              │
│  User bisa:                                  │
│    📋 Salin    📥 Export (TXT/PDF/Word/Excel) │
│    ✏️ Minta Revisi    ⭐ Beri Rating          │
└─────────────────────────────────────────────┘
```

### Mode Solo

```
User mengetik pertanyaan
        │
        ▼
┌─ DIRECT RESPONSE ──────────────────────────┐
│  POST /solo                                  │
│  Satu model AI menjawab langsung            │
│  Mendukung follow-up (riwayat percakapan)   │
│  User bisa memilih model dari dropdown      │
└─────────────────────────────────────────────┘
```

### Alur Revisi

```
User klik "✏️ Minta Revisi"
        │
        ▼
┌─ REVISION ─────────────────────────────────┐
│  POST /revise                                │
│  User mengetik permintaan revisi             │
│  AI merevisi jawaban sebelumnya              │
│  Tanpa mengulangi seluruh proses debat       │
└─────────────────────────────────────────────┘
```

---

## 📁 Struktur File & Penjelasan

```
AIKB/
├── .gitignore                  # File yang diabaikan Git
├── README.md                   # Readme singkat proyek
├── DOCUMENTATION.md            # Dokumentasi lengkap (file ini)
│
├── backend/                    # ═══ SERVER-SIDE ═══
│   ├── main.py                 # Entry point FastAPI, semua route/endpoint
│   ├── agents.py               # Core AI logic: streaming, model mapping, file parsing
│   ├── database.py             # Database layer (SQLite): CRUD feedback & rating
│   ├── requirements.txt        # Daftar dependency Python
│   ├── .env                    # API keys (JANGAN commit ke repo publik!)
│   ├── consensus.db            # SQLite database (auto-generated)
│   ├── patch_main.py           # Script patch: menambah export & dynamic planner
│   ├── patch_files.py          # Script patch: menambah file upload support
│   └── patch_fallback.py       # Script patch: menambah fallback logic Gemini
│
└── frontend/                   # ═══ CLIENT-SIDE ═══
    ├── index.html              # Halaman utama (SPA: HTML + CSS + JS dalam 1 file)
    ├── admin.html              # Halaman admin panel (standalone)
    └── patch_index.py          # Script patch: menambah voice, mermaid, planner select
```

### Detail per File

#### `backend/main.py` — Entry Point & API Routes
File utama server. Berisi semua endpoint REST API:
- **AI Endpoints**: `/plan`, `/solo`, `/debate`, `/revise`
- **Export Endpoint**: `/export` (convert ke DOCX, XLSX, MD, TXT)
- **Feedback Endpoints**: `/feedback`, `/admin/feedbacks`, update & delete
- **Rating Endpoints**: `/rate`, `/admin/ratings`
- **Stats Endpoint**: `/admin/stats`
- CORS middleware untuk mengizinkan akses dari frontend
- Lifecycle management (init database on startup)

#### `backend/agents.py` — Core AI Logic
Otak dari sistem AI:
- **Model Mapping**: Memetakan nama model user-friendly ke ID model API
- **`generate_stream()`**: Fungsi utama untuk streaming respons dari AI
  - Mendukung Gemini (via Google GenAI) dan model Groq (LLaMA, Qwen, GPT-OSS)
  - Automatic fallback ke LLaMA jika Gemini kena rate limit
  - Mendukung file upload (PDF, Word, TXT, Image)
- **`extract_file_content()`**: Parser file yang diupload user
- **`parse_consensus_status()`**: Parser tag [SETUJU]/[BELUM SETUJU] dari respons AI
- Rate limit handling dengan notifikasi ke frontend

#### `backend/database.py` — Database Layer
Abstraksi database menggunakan aiosqlite:
- **Tabel `feedbacks`**: Menyimpan feedback user (kategori: bug/saran/lainnya, status: pending/in_progress/done)
- **Tabel `ratings`**: Menyimpan rating 1-5 bintang per sesi chat
- Fungsi CRUD lengkap: add, get, update, delete
- Fungsi statistik: count per kategori, rata-rata rating

#### `backend/requirements.txt` — Python Dependencies
Daftar semua library Python yang diperlukan:
```
fastapi, uvicorn[standard], python-dotenv, groq, google-genai,
python-docx, openpyxl, PyPDF2, aiosqlite
```

#### `frontend/index.html` — Main Application (Single Page App)
File terbesar (~970 baris). Berisi seluruh aplikasi frontend:
- **CSS** (~430 baris): Dark theme, glassmorphism, animasi, responsive design
- **HTML** (~190 baris): Layout sidebar + main panel + modals
- **JavaScript** (~350 baris): Seluruh logika aplikasi

Fitur frontend:
- Dual mode: Solo & Konsensus
- Chat history management (localStorage)
- File upload & preview (PDF, Word, TXT, Gambar)
- Real-time streaming SSE
- Voice input (Web Speech API)
- Rating & feedback system
- Export ke berbagai format
- Admin panel (in-app)
- Auth (login/register) dengan localStorage
- Progress bar konsensus
- Side-by-side view untuk debat
- Prompt templates

#### `frontend/admin.html` — Admin Panel (Standalone)
Halaman admin terpisah untuk mengelola feedback & rating:
- Dashboard dengan statistik
- Filter feedback per kategori (Bug/Saran/Lainnya)
- Update status feedback (Pending → In Progress → Done)
- Hapus feedback
- Lihat semua rating

#### File `patch_*.py` — Script Patch (Development Tools)
File-file ini adalah **script development** yang digunakan selama pengembangan untuk memodifikasi kode secara otomatis. **Tidak perlu dijalankan lagi** karena perubahan sudah diterapkan:
- `patch_main.py`: Menambah export endpoint & dynamic planner model
- `patch_files.py`: Menambah dukungan file upload ke semua endpoint
- `patch_fallback.py`: Menambah fallback logic saat Gemini kena rate limit
- `patch_index.py`: Menambah voice input, Mermaid diagram, planner model select

---

## 🔌 API Endpoints

### AI Endpoints

| Method | Endpoint | Deskripsi | Body |
|--------|----------|-----------|------|
| `POST` | `/plan` | Fase planner: buat rencana jawaban | `{ question, model, files[] }` |
| `POST` | `/solo` | Mode solo: satu AI jawab langsung | `{ question, model, files[], history[] }` |
| `POST` | `/debate` | Fase debat: diskusi antar AI | `{ system_prompt, message, model, files[] }` |
| `POST` | `/revise` | Revisi jawaban tanpa debat ulang | `{ revision_request, original_answer, model, files[] }` |

> Semua AI endpoints mengembalikan **`text/event-stream`** (SSE) untuk streaming real-time.

### Export Endpoint

| Method | Endpoint | Deskripsi | Body |
|--------|----------|-----------|------|
| `POST` | `/export` | Export hasil konsensus ke file | `{ content, format }` |

Format yang didukung: `docx`, `xlsx`, `md`, `txt`

### Feedback & Rating Endpoints

| Method | Endpoint | Deskripsi | Body/Params |
|--------|----------|-----------|-------------|
| `POST` | `/feedback` | Kirim feedback baru | `{ category, message }` |
| `GET` | `/admin/feedbacks` | Ambil semua feedback | `?category=bug/saran/lainnya` |
| `PATCH` | `/admin/feedbacks/{id}` | Update status feedback | `{ status }` |
| `DELETE` | `/admin/feedbacks/{id}` | Hapus feedback | — |
| `POST` | `/rate` | Kirim rating (1-5) | `{ chat_id, rating }` |
| `GET` | `/admin/ratings` | Ambil semua rating | — |
| `GET` | `/admin/stats` | Statistik gabungan | — |

---

## 🤖 Model AI yang Digunakan

| Nama di App | Model ID | Provider | API |
|-------------|----------|----------|-----|
| **Gemini Flash** | `gemini-2.0-flash-lite` | Google | Google GenAI |
| **LLaMA 3.3 70B** | `llama-3.3-70b-versatile` | Meta | Groq Cloud |
| **LLaMA 3.1 8B** | `llama-3.1-8b-instant` | Meta | Groq Cloud |
| **GPT-OSS 120B** | `openai/gpt-oss-120b` | OpenAI | Groq Cloud |
| **Qwen 3 32B** | `qwen/qwen3-32b` | Alibaba | Groq Cloud |

### Mekanisme Fallback
- Jika **Gemini** kena rate limit (429), otomatis fallback ke **LLaMA 3.3 70B** via Groq
- Jika **Groq model** kena rate limit, debat di-skip dengan tag `[SKIP_DEBATE]`
- Frontend menampilkan notifikasi rate limit ke user

---

## 🗄 Database Schema

### Tabel `feedbacks`
```sql
CREATE TABLE feedbacks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    category   TEXT NOT NULL CHECK(category IN ('bug', 'saran', 'lainnya')),
    message    TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending' 
               CHECK(status IN ('pending', 'in_progress', 'done')),
    created_at TEXT NOT NULL  -- ISO 8601 UTC
);
```

### Tabel `ratings`
```sql
CREATE TABLE ratings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    TEXT NOT NULL,
    rating     INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    created_at TEXT NOT NULL  -- ISO 8601 UTC
);
```

---

## ✨ Fitur-Fitur Utama

### 1. 🧠 Mode Konsensus (Multi-AI Discussion)
- 5 model AI berdiskusi hingga 5 ronde
- Sistem voting [SETUJU]/[BELUM SETUJU]
- Progress bar real-time
- Side-by-side comparison view

### 2. 💬 Mode Solo
- Tanya langsung ke 1 model AI pilihan
- Mendukung follow-up percakapan
- Dropdown pemilihan model

### 3. 📎 File Upload
- Mendukung: PDF, Word (.docx), TXT, dan Gambar
- File diparse otomatis dan disertakan sebagai konteks ke AI
- Gambar hanya diproses oleh Gemini (multimodal)

### 4. 📥 Multi-Format Export
- **TXT**: Plain text
- **PDF**: Via html2pdf.js di browser
- **Word (.docx)**: Via python-docx di server
- **Excel (.xlsx)**: Via openpyxl di server
- **Markdown (.md)**: Raw markdown

### 5. 🎙 Voice Input
- Dikte suara menggunakan Web Speech API
- Bahasa Indonesia (`id-ID`)
- Toggle recording dengan tombol mikrofon

### 6. ✏️ Revisi Jawaban
- Minta revisi tanpa mengulang seluruh proses debat
- AI merevisi berdasarkan jawaban sebelumnya + instruksi baru

### 7. 📢 Sistem Feedback
- User bisa kirim feedback: Bug, Saran, atau Lainnya
- Admin bisa kelola status: Pending → In Progress → Done

### 8. ⭐ Rating System
- Rating 1-5 bintang untuk setiap hasil konsensus
- Statistik rata-rata di admin panel

### 9. 🔐 Autentikasi User
- Login & Register (disimpan di localStorage)
- Guest bisa melihat-lihat, tapi harus login untuk bertanya
- Admin panel hanya untuk username `admin`

### 10. 💾 Riwayat Chat
- Semua percakapan tersimpan di localStorage
- Bisa load ulang, rename, dan hapus
- Persist antar sesi browser

### 11. 🎨 UI/UX Premium
- Dark theme dengan glassmorphism
- Animasi halus (fade-up bubbles, pulsing dot)
- Responsive design (desktop & mobile)
- Sidebar collapsible
- Prompt templates (Esai, Code, Analisis, Belajar)

---

## 🚀 Cara Instalasi & Menjalankan

### Prasyarat
- Python 3.9+ terinstall
- Browser modern (Chrome/Edge/Firefox)
- API Key untuk Google Gemini dan/atau Groq

### Langkah 1: Clone Repository
```bash
git clone https://github.com/Laluirgi/ConsensusAI_Project_RPL.git
cd ConsensusAI_Project_RPL
```

### Langkah 2: Setup Backend
```bash
cd backend

# Buat virtual environment (opsional tapi disarankan)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Langkah 3: Konfigurasi API Keys
Buat file `.env` di folder `backend/`:
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **Dapatkan API key gratis:**
> - Groq: [console.groq.com](https://console.groq.com)
> - Gemini: [aistudio.google.com](https://aistudio.google.com)

### Langkah 4: Jalankan Backend
```bash
python main.py
```
Server akan berjalan di `http://localhost:8000`

### Langkah 5: Buka Frontend
Buka file `frontend/index.html` di browser.  
Atau gunakan Live Server extension di VS Code.

> **Catatan**: Frontend mengakses backend di `http://localhost:8000`. Pastikan backend sudah berjalan sebelum menggunakan aplikasi.

---

## 🔑 Environment Variables

| Variable | Deskripsi | Wajib? |
|----------|-----------|--------|
| `GROQ_API_KEY` | API key untuk Groq Cloud (LLaMA, Qwen, GPT-OSS) | Ya (untuk model Groq) |
| `GEMINI_API_KEY` | API key untuk Google Gemini | Ya (untuk Gemini Flash) |

---

## 👥 Kontributor

| Nama | Peran |
|------|-------|
| **Aril** | Developer |
| **Tim RPL** | Kolaborator |

---

## 📝 Catatan untuk Tim

1. **Jangan commit file `.env`** — sudah ada di `.gitignore`. Setiap anggota tim harus membuat `.env` sendiri dengan API key masing-masing.
2. **File `patch_*.py`** adalah artifact pengembangan. Tidak perlu dijalankan karena semua perubahan sudah diterapkan ke kode utama.
3. **Database `consensus.db`** akan otomatis dibuat saat backend pertama kali dijalankan.
4. **localStorage** menyimpan data chat di browser masing-masing. Data ini tidak tersinkronisasi antar perangkat.
5. Untuk akses **Admin Panel**, login dengan username `admin`.

---

*Dokumentasi ini terakhir diperbarui: Juli 2026*
