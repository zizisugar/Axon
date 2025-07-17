# 步驟 1: 選擇一個官方的 Python 作為我們的基礎環境
# 我們選擇一個包含 Python 3.9 的輕量級版本 (slim)
FROM python:3.9-slim

# 步驟 2: 設定容器內的工作目錄
# 之後的所有指令都會在這個目錄下執行
WORKDIR /app

# 步驟 3: 將我們的依賴清單檔案複製到容器中
# 注意：我們先只複製這個檔案，而不是整個專案
COPY requirements.txt .

# 步驟 4: 在容器內安裝所有依賴套件
# --no-cache-dir 是一個好習慣，可以讓映像檔體積小一些
RUN pip install --no-cache-dir -r requirements.txt

# 步驟 5: 將我們整個應用程式的程式碼複製到容器中
# 將本地的 app 資料夾，複製到容器內的 /app/app 資料夾
COPY ./app .

# 步驟 6: 指定容器啟動時要執行的指令
# 這會告訴容器，當它被啟動時，要去執行 uvicorn
# 0.0.0.0 代表監聽所有網路介面的請求
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]