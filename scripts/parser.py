import json
from pathlib import Path

def main():
    """
    主函數，執行解析 manifest.json 的主要邏輯。
    """
    # 建立 manifest.json 檔案的路徑
    # Path.cwd() 會取得目前的工作目錄 (也就是專案根目錄)
    manifest_path = Path.cwd() / "workspace" / "jaffle_shop" / "target" / "manifest.json"

    print(f"正在讀取 manifest 檔案: {manifest_path}")

    # 檢查檔案是否存在
    if not manifest_path.exists():
        print("錯誤: manifest.json 找不到！請先在 jaffle_shop 目錄執行 'dbt compile'。")
        return

    # 讀取並解析 JSON 檔案
    with open(manifest_path) as f:
        manifest_data = json.load(f)

    # 取得所有的 "nodes" (節點)
    # dbt 中的 node 可以是 model, seed, test, snapshot 等
    all_nodes = manifest_data["nodes"]
    
    print(f"\n成功解析! 共找到 {len(all_nodes)} 個節點。")
    print("-----------------------------------------")
    print("以下是所有 'model' 類型的節點:")
    
    # 遍歷所有節點，只印出 resource_type 為 'model' 的節點
    for unique_id, node_info in all_nodes.items():
        if node_info["resource_type"] == "model":
            # unique_id 是 dbt 為每個資源產生的唯一標識符
            print(f"- {unique_id}")

if __name__ == "__main__":
    main()
