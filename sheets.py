import os, json, gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

ASSET_COLS = {
    "BBRI":    (1,  2,  3,  4,  6),
    "BBCA":    (9,  10, 11, 12, 14),
    "BITCOIN": (18, 19, 20, 21, 23),
    "SOLANA":  (27, 28, 29, 30, 32),
    "SMRA":    (35, 36, 37, 38, 40),
}

ALIAS = {
    "BTC": "BITCOIN",
    "SOL": "SOLANA",
    "BITCOIN": "BITCOIN",
    "SOLANA": "SOLANA",
}

DATA_START_ROW = 5


class PortfolioSheets:
    def __init__(self):
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON tidak ditemukan!")
        creds = Credentials.from_service_account_info(
            json.loads(creds_json), scopes=SCOPES
        )
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])

    def _monitoring(self):
        return self.spreadsheet.worksheet("Monitoring")

    def _next_empty_row(self, ws, col_tanggal):
        col_values = ws.col_values(col_tanggal)
        for i in range(DATA_START_ROW - 1, len(col_values)):
            if col_values[i] == "" or col_values[i] is None:
                return i + 1
        return len(col_values) + 1

    def _normalize_asset(self, nama):
        nama = nama.upper().strip()
        return ALIAS.get(nama, nama)

    def catat_transaksi(self, asset_name, date, price_entry, total_idr, qty, catatan=""):
        kode = self._normalize_asset(asset_name)
        if kode not in ASSET_COLS:
            raise ValueError(f"Aset '{kode}' tidak dikenal. Didukung: {list(ASSET_COLS.keys())}")
        col_tgl, col_harga, col_total, col_qty, col_cat = ASSET_COLS[kode]
        ws = self._monitoring()
        row = self._next_empty_row(ws, col_tgl)
        ws.update_cell(row, col_tgl, str(date))
        if price_entry:
            ws.update_cell(row, col_harga, float(price_entry))
        if total_idr:
            ws.update_cell(row, col_total, float(total_idr))
        if qty:
            ws.update_cell(row, col_qty, float(qty))
        if catatan:
            ws.update_cell(row, col_cat, str(catatan))
        return row

    def get_summary(self):
        try:
            ws = self.spreadsheet.worksheet("Financial Assets")
            data = ws.get_all_values()
            if not data:
                return "Belum ada data."
            
            saham_lines = []
            crypto_lines = []
            cash_lines = []
            total_modal = ""
            total_bersih = ""

            for row in data:
                if len(row) < 6:
                    continue
                nama  = row[2].strip()
                qty   = row[3].strip()
                modal = row[4].strip()
                nilai = row[5].strip()

                if nama in ["BBRI","BBCA","SMRA"]:
                    saham_lines.append(f"  {nama} | {qty}\n  Modal: {modal}\n  Nilai: *{nilai}*")
                elif nama in ["BITCOIN","SOLANA","Pengu"]:
                    crypto_lines.append(f"  {nama} | {qty}\n  Modal: {modal}\n  Nilai: *{nilai}*")
                elif nama in ["Cash","Deposit","Emas"]:
                    if nilai:
                        cash_lines.append(f"  {nama}: {nilai}")

            for row in data:
                if len(row) >= 6 and "TOTAL" in str(row[3]).upper():
                    total_modal = row[4]
                    total_bersih = row[5]
                    break

            lines = [
                "📊 *PORTOFOLIO GW*",
                "───────────────────",
                "🏦 *SAHAM*",
                *saham_lines,
                "",
                "₿ *CRYPTO*",
                *crypto_lines,
                "",
                "💵 *CASH & LAINNYA*",
                *cash_lines,
                "───────────────────",
                f"💼 Total Modal  : {total_modal}",
                f"✨ Total Bersih : *{total_bersih}*",
            ]

            return "\n".join(lines)
        except Exception as e:
            return f"Error baca data: {str(e)}"
