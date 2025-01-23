# 導入所需套件
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import aiohttp
from aiohttp import ClientTimeout
import uvicorn
import json
from parsel import Selector

# 設定請求標頭，模擬瀏覽器行為
HEADERS = {"User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36 Edg/125.0.0.0"}

# 初始化 FastAPI 應用和模板引擎
app = FastAPI()
cookies = None  # 用於儲存登入後的 cookies
templates = Jinja2Templates(directory="templates")

# 首頁路由
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# 登入 API 路由
@app.post("/api/login/", response_class=JSONResponse)
async def login(request: Request):
    param = json.loads(await request.body())
    try:
        # 向中原大學系統發送登入請求
        async with aiohttp.request("GET", f"https://itouch.cycu.edu.tw/active_system/login/login2.jsp?UserNm={param.get('studentId')}&UserPasswd={param.get('password')}&returnType=json&returnPath=https://itouch.cycu.edu.tw/active_project/cycu2000h_11/survey/jsp/auth.getAuth.jsp?success=true&failPath=https://itouch.cycu.edu.tw/active_project/cycu2000h_11/survey/jsp/auth.getAuth.jsp?fail=true", headers=HEADERS, timeout=ClientTimeout(2)) as response:
            if response.status != 200:
                return {"success": False, "message": "登入失敗"}
            result = json.loads(await response.text())
            print(result)
            if result['login_YN'] == 'N':
                return {"success": False, "message": "帳號或密碼錯誤"}
            global cookies
            cookies = response.cookies
    except TimeoutError:
        return {"success": False, "message": "連線逾時"}
    return {"success": True, "message": "登入成功"}

# 儀表板頁面路由
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    gradeData = await fetch_data()
    if not gradeData:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"data": gradeData})

# 抓取成績資料
async def fetch_data():
    # 向中原大學成績查詢系統發送請求
    async with aiohttp.request("GET", "https://itouch.cycu.edu.tw/active_system/quary/s_grade.jsp", cookies=cookies, headers=HEADERS) as response:
        result = await response.text()
        if '超時' in result:
            return False
        selector = Selector(text=result)
        
        # 提取表格資料
        rows = selector.css('td table')
        
        # 初始化資料字典
        data = {}

        # 解析成績資料
        for row in rows[3:-1]:
            cells = row.css('div font').xpath('string(.)').getall()
            for i in range(20, len(cells), 7):
                if cells[i].isdigit():
                    data.setdefault(cells[i], []).append({
                        "department": cells[i+1].strip(),  # 開課系所
                        "category": cells[i+2].strip(),    # 課程類別
                        "course_name": cells[i+3].strip(), # 課程名稱
                        "compulsory_or_elective": cells[i+4].strip(),  # 必選修
                        "grade": cells[i+5].strip(),       # 成績
                        "credits": cells[i+6].strip(),     # 學分數
                    })
        
        return data
    
# 啟動伺服器的函式
def start_server(host: str, port: int):
    uvicorn.run('backend.app:app', host=host, port=port)

# 主程式進入點
if __name__ == "__main__":
    uvicorn.run('app:app', host='localhost', port=8000, reload=True, workers=8)