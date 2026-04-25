from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
import urllib3

# 關閉 SSL 警告（非必要，但可以讓訊息乾淨一點）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# 初始化 Firebase（避免重複初始化）
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)


@app.route("/movie")
def movie():
    """爬取開眼電影網近期上映電影，寫入 Firestore"""
    
    url = "http://www.atmovies.com.tw/movie/next/"
    
    # 發送請求（若遇到 SSL 錯誤可加上 verify=False）
    Data = requests.get(url, verify=False)
    Data.encoding = "utf-8"
    
    # 解析 HTML
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    
    # 取得網站最後更新時間
    lastUpdate = sp.find("div", class_="smaller09").text[5:]
    
    # 連線 Firestore
    db = firestore.client()
    
    # 逐一爬取每部電影
    for item in result:
        # 海報圖片網址
        picture = item.find("img").get("src").replace(" ", "")
        
        # 電影名稱
        title = item.find("div", class_="filmtitle").text
        
        # 電影 ID（用來當作 Firestore 的文件 ID）
        movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        
        # 電影介紹頁網址
        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
        
        # 上映日期與片長（原始字串處理）
        show = item.find("div", class_="runtime").text.replace("上映日期：", "")
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        
        showDate = show[0:10]      # 上映日期
        showLength = show[13:]     # 片長
        
        # 準備寫入的資料
        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate
        }
        
        # 寫入 Firestore
        doc_ref = db.collection("電影").document(movie_id)
        doc_ref.set(doc)
    
    # 回傳結果頁面
    return f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>爬蟲完成</title>
        <style>
            body {{
                font-family: 'Microsoft JhengHei', Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 500px;
                margin: 0 auto;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{ color: #667eea; }}
            p {{ color: #333; margin: 20px 0; }}
            a {{
                display: inline-block;
                margin: 10px;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 50px;
                transition: 0.3s;
            }}
            a:hover {{ background: #764ba2; transform: translateY(-2px); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ 爬蟲完成！</h1>
            <p>近期上映電影已爬蟲及存檔完畢</p>
            <p>📅 網站最近更新日期：{lastUpdate}</p>
            <br>
            <a href="/">🏠 回首頁</a>
            <a href="/search.html">🔍 查詢電影</a>
        </div>
    </body>
    </html>
    """


@app.route("/search")
def search():
    """查詢電影（支援關鍵字）"""
    
    keyword = request.args.get("keyword", "")
    
    if not keyword:
        return """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>錯誤</title></head>
        <body style="text-align:center; padding:50px;">
            <h1>❌ 請輸入查詢關鍵字</h1>
            <a href="/search.html">返回查詢頁面</a>
        </body>
        </html>
        """
    
    db = firestore.client()
    docs = db.collection("電影").get()
    
    # 開始產生結果頁面
    html = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>查詢結果</title>
        <style>
            body {
                font-family: 'Microsoft JhengHei', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px;
                margin: 0;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            .result-card {
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .result-card h3 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .result-card p {
                margin: 8px 0;
                color: #333;
            }
            .result-card a {
                color: #667eea;
                text-decoration: none;
            }
            .result-card a:hover {
                text-decoration: underline;
            }
            .no-result {
                background: white;
                border-radius: 15px;
                padding: 40px;
                text-align: center;
            }
            .back-link {
                display: inline-block;
                margin: 20px 10px;
                padding: 10px 20px;
                background: white;
                color: #667eea;
                text-decoration: none;
                border-radius: 50px;
                transition: 0.3s;
            }
            .back-link:hover {
                background: #f0f0f0;
                transform: translateY(-2px);
            }
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 查詢結果：「""" + keyword + """」</h1>
    """
    
    found = False
    for doc in docs:
        if keyword in doc.to_dict()["title"]:
            found = True
            html += f"""
            <div class="result-card">
                <h3>🎬 {doc.to_dict()['title']}</h3>
                <p>📖 影片介紹：<a href="{doc.to_dict()['hyperlink']}" target="_blank">點我觀看</a></p>
                <p>⏱️ 片長：{doc.to_dict()['showLength']} 分鐘</p>
                <p>📅 上映日期：{doc.to_dict()['showDate']}</p>
            </div>
            """
    
    if not found:
        html += f"""
            <div class="no-result">
                <h2>❌ 找不到相關電影</h2>
                <p>請嘗試其他關鍵字</p>
            </div>
        """
    
    html += """
            <div style="text-align:center;">
                <a href="/" class="back-link">🏠 回首頁</a>
                <a href="/search.html" class="back-link">🔍 重新查詢</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


# Vercel 需要這個
app.debug = True
