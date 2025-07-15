import json
from pathlib import Path
from neo4j import GraphDatabase, Driver

class LineageService:
    """
    一個專門用來處理 dbt manifest 解析與載入至 Neo4j 的服務類別。
    """
    def __init__(self, driver: Driver):
        """
        初始化時接收一個已經建立好的 Neo4j Driver 實例。
        這種作法稱為「依賴注入 (Dependency Injection)」，讓程式碼更具彈性與可測試性。
        """
        self.driver = driver

    def _clear_database(self, session):
        """(私有方法) 清空資料庫，確保每次都是從乾淨的狀態開始。"""
        print("正在清空 Neo4j 資料庫...")
        session.run("MATCH (n) DETACH DELETE n")
        print("資料庫已清空。")

    def _load_nodes(self, session, nodes: dict):
        """(私有方法) 將所有 dbt 節點載入到 Neo4j。"""
        print("開始載入 dbt 節點至 Neo4j...")
        for unique_id, node_info in nodes.items():
            resource_type = node_info.get("resource_type", "unknown")
            name = node_info.get("name", "unknown")
            
            session.run("""
                MERGE (n:DbtNode {unique_id: $unique_id})
                SET n.name = $name, n.resource_type = $resource_type
            """, unique_id=unique_id, name=name, resource_type=resource_type)
        print(f"成功載入 {len(nodes)} 個節點。")

    def _load_relationships(self, session, nodes: dict):
        """(私有方法) 根據 depends_on 建立節點之間的關係。"""
        print("開始建立節點間的血緣關係...")
        relationship_count = 0
        for source_unique_id, node_info in nodes.items():
            dependencies = node_info.get("depends_on", {}).get("nodes", [])
            for target_unique_id in dependencies:
                session.run("""
                    MATCH (source:DbtNode {unique_id: $source_id})
                    MATCH (target:DbtNode {unique_id: $target_id})
                    MERGE (source)-[:DEPENDS_ON]->(target)
                """, source_id=source_unique_id, target_id=target_unique_id)
                relationship_count += 1
        print(f"成功建立 {relationship_count} 條血緣關係。")

    def update_graph_from_manifest(self, manifest_path: str) -> dict:
        """
        這是供外部 (API) 呼叫的主要方法。
        它接收一個 manifest 檔案路徑，然後執行完整的更新流程。
        """
        path_obj = Path(manifest_path)
        if not path_obj.exists():
            return {"status": "error", "message": f"Manifest file not found at {manifest_path}"}

        with open(path_obj) as f:
            manifest_data = json.load(f)
        
        nodes = manifest_data.get("nodes", {})
        nodes_count = len(nodes)
        
        with self.driver.session() as session:
            self._clear_database(session)
            self._load_nodes(session, nodes)
            self._load_relationships(session, nodes)
        
        print("\n圖資料庫更新完成！")
        return {"status": "success", "nodes_loaded": nodes_count}