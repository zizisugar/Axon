import json
import os # 匯入 os 模組來讀取環境變數
from pathlib import Path
from dotenv import load_dotenv # 從 dotenv 函式庫匯入 load_dotenv
from neo4j import GraphDatabase

# --- 讀取 .env 檔案 ---
# 這行程式碼會自動尋找專案根目錄的 .env 檔案，並將其內容載入到環境變數中
load_dotenv()

# --- 從環境變數讀取 Neo4j 連線設定 ---
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER") # 從環境變數讀取使用者名稱
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") # 從環境變數讀取密碼

# 增加一個檢查，確保環境變數有被正確載入
if not NEO4J_USER or not NEO4J_PASSWORD:
    raise ValueError("錯誤: 請確認 .env 檔案中已正確設定 NEO4J_USER 和 NEO4J_PASSWORD")


class DbtManifestParser:
    def __init__(self, manifest_path):
        """
        初始化解析器，讀取 manifest 檔案。
        """
        print(f"正在讀取 manifest 檔案: {manifest_path}")
        if not manifest_path.exists():
            raise FileNotFoundError(f"錯誤: manifest.json 找不到！路徑: {manifest_path}")
        
        with open(manifest_path) as f:
            self.manifest_data = json.load(f)
        
        print("Manifest 檔案解析成功。")
        
        # 使用從環境變數讀取到的設定來初始化 Neo4j 驅動
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        """關閉 Neo4j 連線。"""
        self.driver.close()

    def clear_database(self):
        """清空資料庫，確保每次執行都是從乾淨的狀態開始。"""
        print("正在清空 Neo4j 資料庫...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("資料庫已清空。")

    def load_nodes_to_neo4j(self):
        """將所有 dbt 節點載入到 Neo4j。"""
        print("開始載入 dbt 節點至 Neo4j...")
        nodes = self.manifest_data["nodes"]
        with self.driver.session() as session:
            for unique_id, node_info in nodes.items():
                resource_type = node_info.get("resource_type", "unknown")
                name = node_info.get("name", "unknown")
                
                session.run("""
                    MERGE (n:DbtNode {unique_id: $unique_id})
                    SET n.name = $name, n.resource_type = $resource_type
                """, unique_id=unique_id, name=name, resource_type=resource_type)
        print(f"成功載入 {len(nodes)} 個節點。")

    def load_relationships_to_neo4j(self):
        """根據 depends_on 建立節點之間的關係。"""
        print("開始建立節點間的血緣關係...")
        nodes = self.manifest_data["nodes"]
        relationship_count = 0
        with self.driver.session() as session:
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


def main():
    """主函數，執行完整流程。"""
    manifest_path = Path.cwd() / "workspace" / "jaffle_shop" / "target" / "manifest.json"
    
    parser = DbtManifestParser(manifest_path)
    
    try:
        parser.clear_database()
        parser.load_nodes_to_neo4j()
        parser.load_relationships_to_neo4j()
        print("\n資料載入完成！")
    finally:
        parser.close()
        print("已關閉 Neo4j 連線。")


if __name__ == "__main__":
    main()