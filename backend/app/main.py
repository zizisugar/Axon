from fastapi import FastAPI
from app.api.v1 import lineage # <--- 步驟 1: 匯入我們在 lineage.py 中建立的 router
from app.db import close_db_connection # 匯入關閉連線的函式

# 建立 FastAPI 主應用實例
app = FastAPI(
    title="Axon Data Governance API",
    description="API for providing data lineage and impact analysis.",
    version="0.1.0",
)

# 註冊應用程式關閉時要執行的事件
@app.on_event("shutdown")
def shutdown_event():
    close_db_connection()

# 步驟 2: 將 lineage.py 的 router 包含進主應用中
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