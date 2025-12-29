# MahaInsight 📊

Wadah publikasi hasil analisis data (Data Analyst Portfolio) berupa artikel insight lokal Indonesia.

## Fitur Utama

- ✅ **Publikasi Artikel** - Tulis insight dengan format Markdown
- ✅ **Upload Data** - Lampirkan file CSV/Excel untuk pembaca download
- ✅ **Visualisasi** - Tampilkan chart dan grafik hasil analisis
- ✅ **Sumber Kredibel** - Cantumkan link ke sumber data asli
- ✅ **Admin Panel** - Kelola konten dengan mudah

## Tech Stack

- **Backend:** Python (Flask)
- **Database & Storage:** Supabase (PostgreSQL + Storage)
- **Frontend:** HTML + Tailwind CSS (CDN) + Jinja2 Templates
- **Markdown Editor:** SimpleMDE

## Quick Start

### 1. Setup Supabase

1. Buat akun di [Supabase](https://supabase.com)
2. Buat project baru
3. Buat tabel `posts` dengan struktur berikut:

```sql
CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content_md TEXT NOT NULL,
    source_link TEXT,
    source_name TEXT,
    data_url TEXT,
    thumbnail_url TEXT
);
```

4. Buat Storage Bucket `mahainsight-files` (Set Public: ON)
5. Copy URL & API Key

### 2. Setup Project

```bash
# Clone/masuk ke folder project
cd mahainsight

# Copy env template
cp .env.example .env

# Edit .env dengan kredensial Supabase kamu
nano .env

# Install dependencies
pip install -r requirements.txt

# Jalankan server
flask run --debug
```

### 3. Akses Aplikasi

- **Homepage:** http://localhost:5000
- **Login Admin:** http://localhost:5000/login
- **Admin Dashboard:** http://localhost:5000/admin

## Struktur Folder

```
/mahainsight
├── .env                  # Kredensial (JANGAN commit!)
├── .env.example          # Template kredensial
├── .gitignore            # Files to ignore
├── app.py                # Flask routes
├── db.py                 # Supabase helpers
├── requirements.txt      # Python dependencies
├── README.md             # Dokumentasi ini
└── templates/
    ├── base.html         # Layout utama
    ├── index.html        # Homepage
    ├── detail.html       # Halaman baca artikel
    ├── login.html        # Login admin
    ├── admin.html        # Dashboard admin
    ├── admin_create.html # Form buat artikel
    └── admin_edit.html   # Form edit artikel
```

## Environment Variables

| Variable | Deskripsi |
|----------|-----------|
| `SUPABASE_URL` | URL project Supabase |
| `SUPABASE_KEY` | Anon atau Service Role Key |
| `SECRET_KEY` | Random string untuk Flask session |
| `ADMIN_PASS` | Password login admin |

## License

MIT License - Bebas digunakan untuk kebutuhan personal maupun komersial.
