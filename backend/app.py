from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import aiohttp
from aiohttp import ClientTimeout
import uvicorn
import json
from parsel import Selector

HEADERS = {"User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36 Edg/125.0.0.0"}

app = FastAPI()
cookies = None
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/login/", response_class=JSONResponse)
async def login(request: Request):
    param = json.loads(await request.body())
    try:
        async with aiohttp.request("GET", f"https://itouch.cycu.edu.tw/active_system/login/login2.jsp?UserNm={param.get('studentId')}&UserPasswd={param.get('password')}&returnType=json&returnPath=https://itouch.cycu.edu.tw/active_project/cycu2000h_11/survey/jsp/auth.getAuth.jsp?success=true&failPath=https://itouch.cycu.edu.tw/active_project/cycu2000h_11/survey/jsp/auth.getAuth.jsp?fail=true", headers=HEADERS, timeout=ClientTimeout(2)) as response:
            if response.status != 200:
                return {"success": False, "message": "Login failed"}
            result = json.loads(await response.text())
            print(result)
            if result['login_YN'] == 'N':
                return {"success": False, "message": "Login failed"}
            global cookies
            cookies = response.cookies
    except TimeoutError:
        return {"success": False, "message": "Login failed"}
    return {"success": True, "message": "Login successful"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    gradeData = await fetch_data()
    if not gradeData:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"data": gradeData})

async def fetch_data():
    async with aiohttp.request("GET", "https://itouch.cycu.edu.tw/active_system/quary/s_grade.jsp", cookies=cookies, headers=HEADERS) as response:
        result = await response.text()
        if '超時' in result:
            return False
        selector = Selector(text=result)
        # 提取成績資料
        # 從表格中提取資料
        rows = selector.css('td table')
        
        # 初始化清理好的數據列表
        data = {}

        # 遍歷所有的表格行，提取數據
        for row in rows[3:-1]:
            cells = row.css('div font').xpath('string(.)').getall()
            for i in range(20, len(cells), 7):
                if cells[i].isdigit():
                    data.setdefault(cells[i], []).append({
                        "department": cells[i+1].strip(),
                        "category": cells[i+2].strip(),
                        "course_name": cells[i+3].strip(),
                        "compulsory_or_elective": cells[i+4].strip(),
                        "grade": cells[i+5].strip(),
                        "credits": cells[i+6].strip(),
                    })
        
        return data
    
def start_server(host: str, port: int):
    uvicorn.run('backend.app:app', host=host, port=port)

if __name__ == "__main__":
    uvicorn.run('app:app', host='localhost', port=8000, reload=True, workers=8)