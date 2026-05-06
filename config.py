import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID"))
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "").split(",")))
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")