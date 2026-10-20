# passenger_app/database.py
import json
import os

# 🌟 修改路徑：指向上一層的 shared_data 資料夾
DB_FILE = "../shared_data/users_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        # 初始化資料庫結構
        default_db = {"users": {}}
        save_db(default_db)
        return default_db
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db_data):
    # 確保儲存時資料夾存在
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)