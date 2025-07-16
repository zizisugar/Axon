import os
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv

# 讀取 .env 檔案中的環境變數
load_dotenv()

# --- 從環境變數讀取設定 ---
# 提供了預設值，以防 .env 中沒有設定
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# --- 建立一個全域共享的 Driver 實例 ---
# driver 是執行緒安全的，可以在整個應用程式的生命週期中共享
# 我們將它初始化為 None，稍後在應用程式啟動時再建立
driver: Driver = None

def get_db_driver() -> Driver:
    """
    這個函式會回傳 Driver 實例。
    在 FastAPI 中，我們將用它來進行「依賴注入」。
    它確保了我們的 API 端點能拿到一個可用的 Driver。
    """
    return driver

def connect_to_db():
    """在應用程式啟動時，呼叫此函式來建立連線。"""
    global driver
    if NEO4J_USER and NEO4J_PASSWORD:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        print("Neo4j Driver 連線已建立。")
    else:
        raise ValueError("資料庫憑證未設定，請檢查您的 .env 檔案。")

def close_db_connection():
    """在應用程式關閉時，呼叫此函式來優雅地關閉連線。"""
    global driver
    if driver:
        driver.close()
        print("Neo4j Driver 連線已關閉。")