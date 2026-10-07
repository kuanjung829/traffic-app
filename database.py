# database.py
import json
import os

DB_FILE = "users_db.json"

def load_db():
    """讀取本地資料庫"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}} # 預設空資料庫

def save_db(db_data):
    """將資料寫入本地資料庫"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)