from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)


@app.route("/movie")
def movie():
    """爬取開眼電影網近期上映電影，直接顯示在網頁上"""
    
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url, verify=False)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:]

    # 開始產生 HTML 結果
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>近期上映電影</title>
        <style>
            body {{
                font-family: 'Microsoft JhengHei', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px;
                margin: 0;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            h1 {{
                color: white;
                text-align: center;
                margin-bottom: 10px;
            }}
            .update-info {{
                color: white;
                text-align: center;
                margin-bottom: 30px;
                opacity: 0.9;
            }}
            .movie-card {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                display: flex;
                gap: 20px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            .movie-pic img {{
                width: 120px;
                border-radius: 10px;
            }}
            .movie-info {{
                flex: 1;
            }}
            .movie-title {{
                color: #667eea;
                margin-bottom: 10px;
            }}
            .movie-detail {{
                color: #555;
                margin: 8px 0;
            }}
            .movie-link a {{
                color: #ff6b6b;
                text-decoration: none;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 10px;
                padding: 10px 20px;
                background: white;
                color: #667eea;
                text-decoration: none;
                border-radius: 50px;
            }}
            .footer {{
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 近期上映電影</h1>
            <div class="update-info">📅 資料更新時間：{lastUpdate}</div>
    """

    for item in result:
        # 海報圖片
        img_tag = item.find("img")
        picture = img_tag.get("src") if img_tag else ""
        
        # 電影名稱
        title_tag = item.find("div", class_="filmtitle")
        title = title_tag.text if title_tag else "未知"
        
        # 電影介紹頁
        a_tag = title_tag.find("a") if title_tag else None
        hyperlink = "http://www.atmovies.com.tw" + a_tag.get("href") if a_tag else ""
        
        # 上映日期與片長
        runtime_tag = item.find("div", class_="runtime")
        if runtime_tag:
            show = runtime_tag.text.replace("上映日期：", "").replace("片長：", "").replace("分", "")
            showDate = show[0:10] if len(show) >= 10 else "未知"
            showLength = show[13:] if len(show) > 13 else "未知"
        else:
            showDate = "未知"
            showLength = "未知"

        html += f"""
            <div class="movie-card">
                <div class="movie-pic">
                    <img src="{picture}" alt="{title}">
                </div>
                <div class="movie-info">
                    <h2 class="movie-title">🎬 {title}</h2>
                    <p class="movie-detail">📅 上映日期：{showDate}</p>
                    <p class="movie-detail">⏱️ 片長：{showLength} 分鐘</p>
                    <p class="movie-link">🔗 <a href="{hyperlink}" target="_blank">點我看詳細介紹</a></p>
                </div>
            </div>
        """

    html += """
            <div class="footer">
                <a href="/" class="back-link">🏠 回首頁</a>
                <a href="/search" class="back-link">🔍 搜尋電影</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


@app.route("/search")
def search():
    """即時搜尋電影（不依賴資料庫）"""
    
    keyword = request.args.get("keyword", "")
    
    if not keyword:
        return """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>搜尋電影</title></head>
        <body style="text-align:center; padding:50px;">
            <h1>🔍 請輸入關鍵字</h1>
            <form method="get" action="/search">
                <input type="text" name="keyword" placeholder="例如：超" style="padding:10px;width:200px;">
                <button type="submit" style="padding:10px 20px;">搜尋</button>
            </form>
            <br><a href="/">回首頁</a>
        </body>
        </html>
        """
    
    # 即時爬蟲並過濾
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url, verify=False)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>搜尋結果：{keyword}</title>
    <style>
        body {{ font-family: Arial; background: #f0f0f0; padding: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .result {{ background: white; border-radius: 10px; padding: 15px; margin-bottom: 15px; }}
        h1 {{ color: #667eea; }}
        a {{ color: #667eea; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 搜尋「{keyword}」的結果</h1>
    """
    
    found = False
    for item in result:
        title_tag = item.find("div", class_="filmtitle")
        title = title_tag.text if title_tag else ""
        
        if keyword in title:
            found = True
            a_tag = title_tag.find("a") if title_tag else None
            hyperlink = "http://www.atmovies.com.tw" + a_tag.get("href") if a_tag else ""
            
            runtime_tag = item.find("div", class_="runtime")
            if runtime_tag:
                show = runtime_tag.text.replace("上映日期：", "").replace("片長：", "").replace("分", "")
                showDate = show[0:10] if len(show) >= 10 else "未知"
                showLength = show[13:] if len(show) > 13 else "未知"
            else:
                showDate = "未知"
                showLength = "未知"
            
            html += f"""
            <div class="result">
                <h3>🎬 {title}</h3>
                <p>📅 上映日期：{showDate}</p>
                <p>⏱️ 片長：{showLength} 分鐘</p>
                <p>🔗 <a href="{hyperlink}" target="_blank">詳細介紹</a></p>
            </div>
            """
    
    if not found:
        html += f"<p>❌ 找不到包含「{keyword}」的電影</p>"
    
    html += '<br><a href="/">回首頁</a> | <a href="/search">重新搜尋</a>'
    html += "</div></body></html>"
    
    return html


@app.route("/")
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


app.debug = True
