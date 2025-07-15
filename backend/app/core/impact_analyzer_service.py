from neo4j import GraphDatabase, Driver
from typing import List

class ImpactAnalyzerService:
    """
    一個專門用來執行下游衝擊分析的服務類別。
    """
    def __init__(self, driver: Driver):
        """
        同樣接收一個已經建立好的 Neo4j Driver 實例。
        """
        self.driver = driver

    def find_downstream_dependencies(self, start_node_id: str) -> List[str]:
        """
        找出指定節點的所有下游相依項目。
        回傳一個包含所有下游節點 unique_id 的列表。
        """
        print(f"正在分析 '{start_node_id}' 的下游衝擊...")
        
        downstream_nodes = []
        with self.driver.session() as session:
            # 核心的 Cypher 查詢語句
            # 箭頭方向 <-[:DEPENDS_ON*]- 代表從被依賴者(上游)找到依賴者(下游)
            result = session.run("""
                MATCH (start_node:DbtNode {unique_id: $start_node_id})<-[:DEPENDS_ON*]-(downstream_node:DbtNode)
                RETURN downstream_node.unique_id AS downstream_id
            """, start_node_id=start_node_id)
            
            for record in result:
                downstream_nodes.append(record["downstream_id"])
        
        print(f"分析完成，找到 {len(downstream_nodes)} 個下游相依項目。")
        return downstream_nodes