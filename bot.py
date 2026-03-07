"""
Personal Investment Copilot — Telegram Bot
Groq API (Llama 3.1) + Google Sheets Monitoring
"""

import os, json, logging, requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from sheets import PortfolioSheets

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USER_ID = int(os.environ["TELEGRAM_USER_ID"])
GROQ_API_KEY    = os.environ["GROQ_API_KEY"]
sheets = PortfolioSheets()

TODAY = datetime.now().strftime("%Y-%m-%d")

# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT — One-shot classifier + parser
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are a Personal Investment Copilot AI for Telegram.
Your job: classify user message into ONE of 3 types and return ONLY valid JSON.
NO extra text, NO markdown, NO backticks. ONLY JSON.

TODAY = {TODAY}

═══════════════════════════════════════════════
TYPE 1 — TRANSACTION
═══════════════════════════════════════════════
Triggered by: buy/sell intent for stocks or crypto.
Keywords (flexible): "beli", "jual", "buy", "sell", "DCA", "nambah posisi",
"masuk lagi", "exit", "catat", "aku beli", "gw beli", "abis beli", "saya membeli"

Supported assets:
- Stocks (IDX): BBRI, BBCA, SMRA → unit: LOT (1 lot = 100 shares)
- Crypto: BITCOIN (alias: BTC, bitcoin), SOLANA (alias: SOL, solana), PENGU → unit: COIN

Output schema:
{{
  "type": "transaction",
  "action": "buy" | "sell",
  "asset_type": "stock" | "crypto",
  "asset_name": "BBRI" | "BBCA" | "SMRA" | "BITCOIN" | "SOLANA" | "PENGU",
  "date": "YYYY-MM-DD",
  "quantity_lot": number | null,
  "quantity_coin": number | null,
  "total_investment_idr": number | null,
  "price_entry": number | null,
  "notes": "string" | null
}}

Rules:
- asset_name must be UPPERCASE and normalized (BTC→BITCOIN, SOL→SOLANA, btc→BITCOIN)
- For stocks: total_investment_idr = quantity_lot * 100 * price_entry
- For crypto with total only (no quantity): set quantity_coin = total_investment_idr / price_entry (if price known)
- For crypto with quantity only: set total_investment_idr = quantity_coin * price_entry (if price known)
- If price missing, set price_entry = null
- Number formats: 1.1M=1100000, 1.5jt=1500000, 500rb=500000, 1.1miliar=1100000000
- Date if not mentioned = {TODAY}

Examples:
User: "gw abis beli 4 lot bbri di harga 4000"
{{"type":"transaction","action":"buy","asset_type":"stock","asset_name":"BBRI","date":"{TODAY}","quantity_lot":4,"quantity_coin":null,"total_investment_idr":1600000,"price_entry":4000,"notes":null}}

User: "aku beli bitcoin 5 juta"
{{"type":"transaction","action":"buy","asset_type":"crypto","asset_name":"BITCOIN","date":"{TODAY}","quantity_lot":null,"quantity_coin":null,"total_investment_idr":5000000,"price_entry":null,"notes":null}}

User: "gw abis beli bitcoin diharga 68rb dollar dengan 700000idr"
{{"type":"transaction","action":"buy","asset_type":"crypto","asset_name":"BITCOIN","date":"{TODAY}","quantity_lot":null,"quantity_coin":null,"total_investment_idr":700000,"price_entry":null,"notes":"harga USD 68000"}}

User: "jual 5 lot BBRI harga 4200 take profit"
{{"type":"transaction","action":"sell","asset_type":"stock","asset_name":"BBRI","date":"{TODAY}","quantity_lot":5,"quantity_coin":null,"total_investment_idr":2100000,"price_entry":4200,"notes":"take profit"}}

═══════════════════════════════════════════════
TYPE 2 — PORTFOLIO QUERY
═══════════════════════════════════════════════
Triggered by: user wants to check their portfolio.
Keywords: "cek portofolio", "portfolio gw", "porto gw", "lihat porto",
"summary", "total aset", "ringkasan", "/cek"

Output:
{{"type":"portfolio_query"}}

═══════════════════════════════════════════════
TYPE 3 — GENERAL CHAT
═══════════════════════════════════════════════
Triggered by: EVERYTHING else — questions, small talk, requests outside portfolio.
Examples: weather, news, poems, explanations, jokes, greetings

Output:
{{"type":"general_chat","message":"<original user message here>"}}

IMPORTANT: If in doubt between transaction and general_chat, choose general_chat.
ONLY return JSON. Nothing else."""


# ─────────────────────────────────────────────────────────────
# API CALLS
# ─────────────────────────────────────────────────────────────
def call_groq_classify(pesan):
    """Classify + parse message in one shot"""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": pesan}
            ],
            "temperature": 0.1,
            "max_tokens": 400
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"Groq error {resp.status_code}: {resp.text[:200]}")
    raw = resp.json()["choices"][0]["message"]["content"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def call_groq_chat(pesan):
    """Free chat mode — answer anything"""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": (
                    "Kamu adalah asisten AI yang ramah, cerdas, dan helpful. "
                    "Jawab dalam bahasa yang sama dengan user (Indonesia/English/campur). "
                    "Jawab langsung, natural, dan singkat. "
                    "Kamu bisa menjawab apapun: puisi, cerita, pertanyaan umum, dll. "
                    "Untuk pertanyaan yang butuh data real-time (cuaca hari ini, harga saham live, berita terbaru), "
                    "jelaskan bahwa kamu tidak punya akses internet tapi berikan info umum yang kamu tahu."
                )},
                {"role": "user", "content": pesan}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        },
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"Groq error {resp.status_code}: {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────────────────────
# COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────
async def cmd_start(update, ctx):
    if update.effective_user.id != ALLOWED_USER_ID: return
    await update.message.reply_text(
        "Halo! Personal Investment Copilot aktif.\n\n"
        "Ngomong bebas aja:\n"
        "- beli BBRI 2 lot harga 4000\n"
        "- gw abis beli 3 lot bbri seharga 4000\n"
        "- DCA bitcoin 500rb di harga 1.1M\n"
        "- jual SOL 0.1 koin harga 1.5jt\n"
        "- cek portofolio\n"
        "- buatkan puisi tentang investasi\n\n"
        "/cek untuk ringkasan portofolio\n"
        "/help untuk panduan lengkap"
    )

async def cmd_cek(update, ctx):
    if update.effective_user.id != ALLOWED_USER_ID: return
    await update.message.reply_text("Mengambil data portofolio...")
    try:
        await update.message.reply_text(sheets.get_summary())
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def cmd_help(update, ctx):
    if update.effective_user.id != ALLOWED_USER_ID: return
    await update.message.reply_text(
        "PANDUAN — Ngomong bebas!\n\n"
        "BELI SAHAM:\n"
        "• beli BBRI 2 lot harga 4000\n"
        "• gw abis beli 3 lot bbri seharga 4000\n"
        "• nambah posisi BBCA 1 lot di 7200\n\n"
        "BELI CRYPTO:\n"
        "• beli BTC 0.001 koin harga 1.1M\n"
        "• DCA bitcoin 500rb di harga 1.1 miliar\n"
        "• beli solana senilai 500rb\n\n"
        "JUAL:\n"
        "• jual BBRI 5 lot harga 4200 take profit\n"
        "• exit SOL 0.1 koin harga 1.5jt\n\n"
        "CEK PORTOFOLIO:\n"
        "• cek portofolio / /cek\n\n"
        "NGOBROL BEBAS:\n"
        "• buatkan puisi\n"
        "• jelaskan inflasi\n"
        "• dll\n\n"
        "Format angka: 4000 | 1.1M | 1.5jt | 500rb | 1.1miliar"
    )


# ─────────────────────────────────────────────────────────────
# MAIN MESSAGE HANDLER
# ─────────────────────────────────────────────────────────────
async def handle_pesan(update, ctx):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Tidak punya akses.")
        return

    pesan = update.message.text
    await update.message.reply_text("Memproses...")

    try:
        parsed = call_groq_classify(pesan)
        log.info(f"Classified: {parsed}")
        msg_type = parsed.get("type")

        # ── PORTFOLIO QUERY ──────────────────────────────────
        if msg_type == "portfolio_query":
            await update.message.reply_text(sheets.get_summary())
            return

        # ── GENERAL CHAT ─────────────────────────────────────
        if msg_type == "general_chat":
            original = parsed.get("message", pesan)
            jawaban = call_groq_chat(original)
            await update.message.reply_text(jawaban)
            return

        # ── TRANSACTION ──────────────────────────────────────
        if msg_type == "transaction":
            action     = parsed.get("action", "buy")
            asset_type = parsed.get("asset_type")
            asset_name = parsed.get("asset_name", "").upper()
            date       = parsed.get("date", TODAY)
            qty_lot    = parsed.get("quantity_lot")
            qty_coin   = parsed.get("quantity_coin")
            total_idr  = parsed.get("total_investment_idr")
            price      = parsed.get("price_entry")
            notes      = parsed.get("notes") or ""

            qty = qty_lot if asset_type == "stock" else qty_coin

            # Validasi minimal
            if not asset_name:
                await update.message.reply_text("Aset tidak dikenali. Coba: beli BBRI 2 lot harga 4000")
                return

            if not total_idr and not qty:
                await update.message.reply_text(
                    f"Kurang info untuk {asset_name}.\n"
                    "Sebutkan jumlah lot/koin atau total IDR."
                )
                return

            await update.message.reply_text("Menyimpan ke Monitoring...")

            # Tulis ke sheet Monitoring
            row = sheets.catat_transaksi(
                asset_name=asset_name,
                date=date,
                price_entry=price,
                total_idr=total_idr,
                qty=qty,
                catatan=notes
            )

            # Catat juga di log Transaksi Bot
            sheets.catat_log(
                tanggal=date,
                aksi="BELI" if action == "buy" else "JUAL",
                aset=asset_name,
                qty=qty or "",
                harga=price or "",
                total=total_idr or "",
                catatan=notes
            )

            # Format konfirmasi
            aksi_label = "BELI" if action == "buy" else "JUAL"
            qty_label  = f"{qty_lot} lot" if asset_type == "stock" else f"{qty_coin} koin"
            harga_str  = f"Rp {float(price):,.0f}" if price else "dari harga real-time sheet"
            total_str  = f"Rp {float(total_idr):,.0f}" if total_idr else "-"

            await update.message.reply_text(
                f"{aksi_label} {asset_name} TERCATAT (baris {row})\n\n"
                f"Tanggal : {date}\n"
                f"Qty     : {qty_label}\n"
                f"Harga   : {harga_str}\n"
                f"Total   : {total_str}\n"
                f"Catatan : {notes or '-'}"
            )
            return

        # Fallback
        await update.message.reply_text("Tidak mengerti. Coba: beli BBRI 2 lot harga 4000")

    except json.JSONDecodeError:
        await update.message.reply_text("Gagal parse response AI. Coba ulangi lebih jelas.")
    except ValueError as e:
        await update.message.reply_text(f"Error: {str(e)}")
    except Exception as e:
        log.error(str(e), exc_info=True)
        await update.message.reply_text(f"Error: {str(e)}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cek",   cmd_cek))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pesan))
    log.info("Personal Investment Copilot berjalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
