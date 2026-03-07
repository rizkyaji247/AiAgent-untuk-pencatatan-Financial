import os, json, gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Mapping aset ke kolom di sheet "Monitoring" (1-indexed)
# Format: (col_tanggal, col_harga_entry, col_jumlah_beli, col_qty, col_catatan)
ASSET_COLS = {
    "BBRI":    (1,  2,  3,  4,  6),   # A, B, C, D, F
    "BBCA":    (9,  10, 11, 12, 14),  # I, J, K, L, N
    "BITCOIN": (18, 19, 20, 21, 23),  # R, S, T, U, W
    "SOLANA":  (27, 28, 29, 30, 32),  # AA, AB, AC, AD, AF
    "SMRA":    (35, 36, 37, 38, 40),  # AI, AJ, AK, AL, AN
}

# Alias normalisasi
ALIAS = {
    "BTC": "BITCOIN",
    "SOL": "SOLANA",
    "BITCOIN": "BITCOIN",
    "SOLANA": "SOLANA",
}

DATA_START_ROW = 5  # Data mulai dari baris 5


class PortfolioSheets:
    def __init__(self):
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON tidak ditemukan di environment!")
        creds = Credentials.from_service_account_info(
            json.loads(creds_json), scopes=SCOPES
        )
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])

    def _monitoring(self):
        return self.spreadsheet.worksheet("Monitoring")

    def _next_empty_row(self, ws, col_tanggal):
        """Cari baris kosong pertama di kolom tanggal aset mulai dari DATA_START_ROW"""
        col_values = ws.col_values(col_tanggal)
        # col_values index 0 = row 1
        for i in range(DATA_START_ROW - 1, len(col_values)):
            if col_values[i] == "" or col_values[i] is None:
                return i + 1  # convert ke 1-indexed row
        return len(col_values) + 1  # tambah baris baru di bawah

    def _normalize_asset(self, nama):
        nama = nama.upper().strip()
        return ALIAS.get(nama, nama)

    def catat_transaksi(self, asset_name, date, price_entry, total_idr, qty, catatan=""):
        """Tulis transaksi ke kolom yang benar di sheet Monitoring"""
        kode = self._normalize_asset(asset_name)
        if kode not in ASSET_COLS:
            raise ValueError(f"Aset '{kode}' tidak dikenal. Aset yang didukung: {list(ASSET_COLS.keys())}")

        col_tgl, col_harga, col_total, col_qty, col_cat = ASSET_COLS[kode]

        ws = self._monitoring()
        row = self._next_empty_row(ws, col_tgl)

        # Tulis data ke sel yang tepat
        ws.update_cell(row, col_tgl,   str(date))
        ws.update_cell(row, col_harga, float(price_entry) if price_entry else "")
        ws.update_cell(row, col_total, float(total_idr) if total_idr else "")
        ws.update_cell(row, col_qty,   float(qty) if qty else "")
        ws.update_cell(row, col_cat,   str(catatan) if catatan else "")

        return row

    def get_summary(self):
        """Ambil ringkasan transaksi dari sheet Transaksi Bot"""
        try:
            ws = self.spreadsheet.worksheet("Transaksi Bot")
            data = ws.get_all_values()
            if not data:
                return "Belum ada transaksi tercatat."
            lines = ["RINGKASAN TRANSAKSI\n"]
            count = 0
            for row in data:
                if len(row) >= 3 and row[1] in ["BELI", "JUAL"]:
                    lines.append(f"{row[0]} | {row[1]} | {row[2]} | qty:{row[3]} | Rp {row[4]}")
                    count += 1
            if count == 0:
                return "Belum ada transaksi via bot."
            lines.append(f"\nTotal: {count} transaksi")
            return "\n".join(lines)
        except Exception as e:
            return f"Error baca data: {str(e)}"

    def catat_log(self, tanggal, aksi, aset, qty, harga, total, catatan=""):
        """Catat log transaksi di sheet Transaksi Bot sebagai backup"""
        try:
            ws = self.spreadsheet.worksheet("Transaksi Bot")
        except:
            ws = self.spreadsheet.add_worksheet(title="Transaksi Bot", rows=1000, cols=7)
        ws.append_row([tanggal, aksi, aset, qty, harga, total, catatan])
