from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver

from app.db import get_db_driver
# 注意：我們現在引入的是重構後的服務
from app.core.lineage_service import Neo4jLineageService, LineageStorageInterface 

# 建立一個新的 API Router
router = APIRouter()

# ===================================================================
# 依賴注入 (Dependency Injection)
# ===================================================================
def get_lineage_service(driver: Driver = Depends(get_db_driver)) -> LineageStorageInterface:
    """
    這個函式會建立一個 Neo4jLineageService 的實例。
    我們的 API 端點將會依賴這個函式來獲取服務，而不是自己建立。
    回傳的型別是介面，這讓未來替換實作成為可能。
    """
    return Neo4jLineageService(driver)

# ===================================================================
# API 端點 (API Endpoints)
# ===================================================================
@router.get("/graph", response_model=Dict[str, Any])
def get_lineage_graph(
    lineage_service: LineageStorageInterface = Depends(get_lineage_service)
):
    """
    獲取完整的資料血緣圖數據（所有節點和邊）。
    """
    graph_data = lineage_service.get_full_graph()
    return graph_data

@router.get("/impact/{node_id}", response_model=Dict[str, Any])
def get_impact_analysis(
    node_id: str,
    lineage_service: LineageStorageInterface = Depends(get_lineage_service)
):
    """
    對指定的 node_id 執行下游衝擊分析。
    """
    try:
        dependencies = lineage_service.find_downstream_dependencies(node_id)
        return {"node_id": node_id, "impacted_nodes": dependencies}
    except Exception as e:
        # 如果查詢過程中發生任何錯誤，回傳一個標準的 500 錯誤
        raise HTTPException(status_code=500, detail=str(e))