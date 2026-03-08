# 🤖 Personal Investment Copilot — Telegram Bot

> Catat transaksi saham & crypto kamu cukup dengan **ngobrol natural di Telegram** — tanpa form, tanpa klik-klik, langsung masuk ke Google Sheets.

---

## ✨ Apa ini?

**Personal Investment Copilot** adalah AI Agent berbasis Telegram yang membantu kamu mencatat dan memantau portofolio investasi secara otomatis. Cukup kirim pesan seperti *"gw abis beli 4 lot BBRI di harga 4000"* — bot akan mengerti, memproses, dan langsung menyimpan data ke Google Sheets kamu.

Tidak perlu buka spreadsheet, tidak perlu isi form. Cukup chat.

---

## 🚀 Fitur Utama

- **📝 Pencatatan Otomatis** — Tulis transaksi dengan bahasa natural (Indonesia/Inggris/campur), bot langsung parse dan catat ke Google Sheets
- **📊 Cek Portofolio** — Lihat ringkasan semua transaksi kapan saja dengan satu pesan
- **💬 AI Chat Bebas** — Tanya apapun di luar investasi, bot tetap bisa jawab (powered by Llama 3.1)
- **🔒 Private & Aman** — Bot hanya merespons user ID yang kamu whitelist sendiri

---

## 📦 Aset yang Didukung

| Tipe    | Aset              | Alias yang Dikenali     |
|---------|-------------------|--------------------------|
| Saham   | BBRI, BBCA, SMRA  | Nama langsung            |
| Crypto  | Bitcoin, Solana   | BTC, SOL, BITCOIN, SOLANA |
| Crypto  | PENGU             | PENGU                    |

---

## 💬 Contoh Penggunaan

```
# Catat beli saham
gw abis beli 4 lot BBRI di harga 4000
beli BBCA 2 lot seharga 9500

# Catat beli crypto
DCA bitcoin 500rb
beli SOL 0.5 koin harga 1.5jt
beli bitcoin diharga 68rb dollar dengan 700000idr

# Jual
jual BBRI 5 lot harga 4200 take profit
exit SOL 0.1 koin harga 1.5jt

# Cek portofolio
cek portofolio
porto gw
/cek
```

---

## 🛠️ Tech Stack

| Komponen       | Teknologi                          |
|----------------|------------------------------------|
| AI / NLP       | Groq API — Llama 3.1 8B Instant    |
| Bot Platform   | Telegram Bot (python-telegram-bot) |
| Data Storage   | Google Sheets via gspread          |
| Auth           | Google Service Account             |
| Deployment     | Heroku (Procfile + runtime.txt)    |
| Language       | Python 3                           |

---

## ⚙️ Cara Kerja

```
User kirim pesan di Telegram
        ↓
Bot kirim ke Groq AI (Llama 3.1) untuk klasifikasi
        ↓
AI menentukan tipe pesan:
  ├── TRANSACTION → parse detail, hitung total, simpan ke Google Sheets
  ├── PORTFOLIO QUERY → ambil data ringkasan dari sheet
  └── GENERAL CHAT → jawab bebas pakai AI
        ↓
Bot balas user dengan konfirmasi / ringkasan / jawaban
```

---

## 🔧 Setup & Instalasi

### 1. Clone repo

```bash
git clone https://github.com/rizkyaji247/AiAgent-untuk-pencatatan-Financial.git
cd AiAgent-untuk-pencatatan-Financial
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_USER_ID=your_telegram_user_id
GROQ_API_KEY=your_groq_api_key
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
```

### 3. Jalankan

```bash
python bot.py
```

---

## 📁 Struktur Project

```
├── bot.py           # Main bot logic + AI classification
├── sheets.py        # Google Sheets integration
├── requirements.txt # Python dependencies
├── Procfile         # Heroku deployment config
└── runtime.txt      # Python version config
```

---

## 📝 Catatan

Proyek ini dibuat dengan pendekatan **vibe-driven development** — ide besar, eksekusi dengan bantuan AI. Masih dalam pengembangan aktif.

---

*Built with 🤖 AI + ☕ semangat belajar oleh [@rizkyaji247](https://github.com/rizkyaji247)*
