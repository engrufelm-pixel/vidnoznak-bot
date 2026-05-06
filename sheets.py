import gspread
from datetime import datetime
from config import SPREADSHEET_ID

gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.sheet1


def add_row(phone, username, uid, marketplace, order, data_text, req_type):
    try:
        row = [
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            phone or "—",
            f"@{username}" if username else "—",
            str(uid),
            marketplace or "—",
            order or "—",
            data_text or "—",
            req_type
        ]
        ws.append_row(row)
    except Exception as e:
        print(f"Ошибка записи в таблицу: {e}")