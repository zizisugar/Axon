from fastapi import FastAPI

# 建立一個 FastAPI 應用實例
app = FastAPI(
    title="Axon Data Governance API",
    description="API for providing data lineage and impact analysis.",
    version="0.1.0",
)

# 定義一個根路徑的 API 端點
@app.get("/")
def read_root():
    return {"message": "Welcome to the Axon Data Governance API!"}

# 定義一個健康檢查的 API 端點
@app.get("/health")
def health_check():
    return {"status": "ok"}