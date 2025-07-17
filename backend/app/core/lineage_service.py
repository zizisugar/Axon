import json
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from neo4j import Driver

# ===================================================================
# 步驟 1: 定義我們的「儲存介面」 (The "Contract")
# ===================================================================
class LineageStorageInterface(ABC):
    """
    定義了所有血緣儲存服務都必須遵守的「合約」。
    它規定了需要提供哪些方法，以及這些方法的輸入和輸出是什麼。
    """
    @abstractmethod
    def update_graph_from_manifest(self, manifest_path: str) -> Dict[str, Any]:
        """從 manifest.json 更新整個圖。"""
        pass

    @abstractmethod
    def get_full_graph(self) -> Dict[str, Any]:
        """獲取完整的圖數據以供前端視覺化。"""
        pass

    @abstractmethod
    def find_downstream_dependencies(self, start_node_id: str) -> List[str]:
        """根據指定的節點 ID 進行下游衝擊分析。"""
        pass

# ===================================================================
# 步驟 2: 建立針對 Neo4j 的「具體實作」 (The "Implementation")
# ===================================================================
class Neo4jLineageService(LineageStorageInterface):
    """
    這是 StorageInterface 的具體實作，專門負責與 Neo4j 資料庫溝通。
    它「簽署」了上面的合約，所以必須提供合約中定義的所有方法。
    """
    def __init__(self, driver: Driver):
        self.driver = driver

    def update_graph_from_manifest(self, manifest_path: str) -> Dict[str, Any]:
        path_obj = Path(manifest_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Manifest file not found at {manifest_path}")

        with open(path_obj) as f:
            manifest_data = json.load(f)
        
        nodes = manifest_data.get("nodes", {})
        
        with self.driver.session() as session:
            # 使用 transaction 來確保所有操作要麼全部成功，要麼全部失敗
            session.execute_write(self._clear_and_load_data, nodes)
        
        nodes_loaded = len(nodes)
        print(f"\n圖資料庫更新完成！共載入 {nodes_loaded} 個節點。")
        return {"status": "success", "nodes_loaded": nodes_loaded}

    def get_full_graph(self) -> Dict[str, Any]:
        print("正在從 Neo4j 查詢完整的血緣圖...")
        with self.driver.session() as session:
            nodes = self._get_all_nodes(session)
            edges = self._get_all_edges(session)
        
        print(f"查詢完成，找到 {len(nodes)} 個節點和 {len(edges)} 條關係。")
        return {"nodes": nodes, "edges": edges}

    def find_downstream_dependencies(self, start_node_id: str) -> List[str]:
        print(f"正在分析 '{start_node_id}' 的下游衝擊...")
        downstream_nodes = []
        with self.driver.session() as session:
            result = session.run("""
                MATCH (start_node:DbtNode {unique_id: $start_node_id})<-[:DEPENDS_ON*]-(downstream_node:DbtNode)
                RETURN downstream_node.unique_id AS downstream_id
            """, start_node_id=start_node_id)
            downstream_nodes = [record["downstream_id"] for record in result]
        
        print(f"分析完成，找到 {len(downstream_nodes)} 個下游相依項目。")
        return downstream_nodes

    # --- 以下是內部使用的私有輔助方法 ---

    @staticmethod
    def _clear_and_load_data(tx, nodes: dict):
        """一個 transaction function，整合了清空、載入節點和載入關係。"""
        # 1. 清空資料庫
        tx.run("MATCH (n) DETACH DELETE n")
        
        # 2. 載入所有節點
        for unique_id, node_info in nodes.items():
            resource_type = node_info.get("resource_type", "unknown")
            name = node_info.get("name", "unknown")
            tx.run("""
                MERGE (n:DbtNode {unique_id: $unique_id})
                SET n.name = $name, n.resource_type = $resource_type
            """, unique_id=unique_id, name=name, resource_type=resource_type)
            
        # 3. 載入所有關係
        for source_unique_id, node_info in nodes.items():
            dependencies = node_info.get("depends_on", {}).get("nodes", [])
            for target_unique_id in dependencies:
                tx.run("""
                    MATCH (source:DbtNode {unique_id: $source_id})
                    MATCH (target:DbtNode {unique_id: $target_id})
                    MERGE (source)-[:DEPENDS_ON]->(target)
                """, source_id=source_unique_id, target_id=target_unique_id)

    @staticmethod
    def _get_all_nodes(session) -> List[Dict[str, Any]]:
        nodes_data = []
        result = session.run("MATCH (n:DbtNode) RETURN n")
        for record in result:
            node = record["n"]
            nodes_data.append({
                "id": node.get("unique_id"),
                "data": {"label": node.get("name")},
                "type": node.get("resource_type"),
                "position": {"x": 0, "y": 0} # 給前端用的預設位置
            })
        return nodes_data

    @staticmethod
    def _get_all_edges(session) -> List[Dict[str, Any]]:
        edges_data = []
        result = session.run("MATCH (a:DbtNode)-[r:DEPENDS_ON]->(b:DbtNode) RETURN a.unique_id AS source, b.unique_id AS target")
        for record in result:
            edges_data.append({
                "id": f'{record["source"]}-to-{record["target"]}',
                "source": record["source"],
                "target": record["target"],
                "type": "default"
            })
        return edges_data
   
# === insert data into neo4j ===
# if __name__ == '__main__':
#     from dotenv import load_dotenv
#     import os
#     from pathlib import Path
#     from neo4j import GraphDatabase, Driver 

#     # 步驟 1: 建立一個更可靠的路徑來找到 .env 檔案
#     # 這會從目前檔案 (__file__) 的位置，一路往上找到專案的根目錄 (Axon)
#     current_dir = Path(__file__).parent
#     # 從 app/core/ -> app/ -> backend/ -> Axon/
#     project_root = current_dir.parent.parent.parent
#     dotenv_path = project_root / '.env'

#     print(f"正在從以下路徑讀取 .env 檔案: {dotenv_path}")
#     load_dotenv(dotenv_path=dotenv_path)

#     # 步驟 2: 讀取環境變數並增加除錯用的 print 敘述
#     NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
#     NEO4J_USER = os.getenv("NEO4J_USER")
#     NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

#     print(f"讀取到的 NEO4J_USER: {NEO4J_USER}")
#     print(f"讀取到的 NEO4J_PASSWORD: {'******' if NEO4J_PASSWORD else None}") # 不直接印出密碼

#     # 步驟 3: 增加明確的檢查
#     if not NEO4J_USER or not NEO4J_PASSWORD:
#         print("錯誤：無法從 .env 檔案讀取到 NEO4J_USER 或 NEO4J_PASSWORD。")
#         print("請確認您的 .env 檔案位於專案根目錄 (Axon/)，且內容正確。")
#     else:
#         driver = None # 先初始化
#         try:
#             # 手動建立 driver
#             driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

#             # 建立服務實例
#             service = Neo4jLineageService(driver)

#             # 指定 manifest.json 的路徑
#             manifest_file_path = project_root / "tests" / "data" / "manifest.json"
#             print(f"準備從以下路徑載入 manifest: {manifest_file_path}")

#             service.update_graph_from_manifest(str(manifest_file_path))

#             print("腳本執行完畢。")

#         except Exception as e:
#             print(f"執行過程中發生錯誤: {e}")
#         finally:
#             if driver:
#                 driver.close()
#                 print("Neo4j Driver 連線已關閉。")