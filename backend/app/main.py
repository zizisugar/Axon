from fastapi import FastAPI
from app.api.v1 import lineage # <--- 步驟 A1: 匯入我們在 lineage.py 中建立的 router
from app.db import connect_to_db, close_db_connection
# 步驟 B1: 匯入 CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

# 建立 FastAPI 主應用實例
app = FastAPI(
    title="Axon Data Governance API",
    description="API for providing data lineage and impact analysis.",
    version="0.1.0",
)


# 步驟 B2: 設定允許的來源
# 在開發階段，我們可以用最寬鬆的設定，允許所有來源。
origins = [
    "*", # 允許所有來源
]

# 步驟 B3: 將 CORS 中介軟體加入到您的應用程式中
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 允許所有 HTTP 方法
    allow_headers=["*"], # 允許所有 HTTP 標頭
)

# 註冊應用程式啟動時要執行的事件
@app.on_event("startup")
def startup_event():
    connect_to_db()

# 註冊應用程式關閉時要執行的事件
@app.on_event("shutdown")
def shutdown_event():
    close_db_connection()
    
# 步驟 A2: 將 lineage.py 的 router 包含進主應用中
# 這一行是關鍵！它告訴 FastAPI 所有 lineage.py 裡的 API
# 都應該在 /api/v1/lineage 這個路徑下生效。
app.include_router(lineage.router, prefix="/api/v1/lineage", tags=["Lineage"])


# ----------------------------------------------------
# 以下是原本就在 main.py 中的基本端點
# ----------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to the Axon Data Governance API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}