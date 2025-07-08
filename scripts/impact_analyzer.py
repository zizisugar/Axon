import sys
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# --- 讀取 .env 檔案並設定連線 ---
load_dotenv()
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_USER or not NEO4J_PASSWORD:
    raise ValueError("錯誤: 請確認 .env 檔案中已正確設定 NEO4J_USER 和 NEO4J_PASSWORD")

class ImpactAnalyzer:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def find_downstream_dependencies(self, start_node_id: str):
        """
        找出指定節點的所有下游相依項目。
        """
        print(f"正在分析 '{start_node_id}' 的下游衝擊...")
        
        downstream_nodes = []
        with self.driver.session() as session:
            # 這是核心的 Cypher 查詢語句
            # 注意箭頭方向 <-[:DEPENDS_ON*]- 是反過來的，代表從被依賴者(上游)找到依賴者(下游)
            result = session.run("""
                MATCH (start_node:DbtNode {unique_id: $start_node_id})<-[:DEPENDS_ON*]-(downstream_node:DbtNode)
                RETURN downstream_node.unique_id AS downstream_id
            """, start_node_id=start_node_id)
            
            for record in result:
                downstream_nodes.append(record["downstream_id"])
        
        return downstream_nodes

def main():
    # 從指令列參數讀取要分析的節點 ID
    # 例如： python scripts/impact_analyzer.py model.jaffle_shop.stg_customers
    if len(sys.argv) < 2:
        print("使用方式: python scripts/impact_analyzer.py <dbt_model_unique_id>")
        return

    start_node_id = sys.argv[1]
    
    analyzer = ImpactAnalyzer()
    try:
        dependencies = analyzer.find_downstream_dependencies(start_node_id)
        
        print("---")
        if dependencies:
            print(f"找到 {len(dependencies)} 個下游相依項目：")
            for dep in dependencies:
                print(f"- {dep}")
        else:
            print("找不到任何下游相依項目。")
        print("---")

    finally:
        analyzer.close()

if __name__ == "__main__":
    main()