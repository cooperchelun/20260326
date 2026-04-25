from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# 初始化 Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

@app.route("/")
def index():
    # 改為載入 index.html 封面檔案
    return render_template("index.html")

@app.route("/movie")
def movie():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:]

    db = firestore.client()

    for item in result:
        picture = item.find("img").get("src").replace(" ", "")
        title = item.find("div", class_="filmtitle").text
        movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")

        show = item.find("div", class_="runtime").text.replace("上映日期：", "")
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        showDate = show[0:10]
        showLength = show[13:]

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate
        }

        doc_ref = db.collection("電影").document(movie_id)
        doc_ref.set(doc)

    # 回傳結果頁面（簡單版）
    return f"""
    <html>
    <head><meta charset="UTF-8"><title>爬蟲完成</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>✅ 爬蟲完成！</h1>
        <p>近期上映電影已爬蟲及存檔完畢</p>
        <p>📅 網站最近更新日期：{lastUpdate}</p>
        <br>
        <a href="/">🏠 回首頁</a> | <a href="/searchQ">🔍 查詢電影</a>
    </body>
    </html>
    """

@app.route("/searchQ", methods=["POST", "GET"])
def searchQ():
    if request.method == "POST":
        keyword = request.form["MovieTitle"]
        db = firestore.client()
        docs = db.collection("電影").get()

        info = "<html><head><meta charset='UTF-8'><title>查詢結果</title></head><body>"
        info += "<h1>🔍 查詢結果</h1>"
        found = False
        for doc in docs:
            if keyword in doc.to_dict()["title"]:
                found = True
                info += f"<p><strong>🎬 片名：</strong>{doc.to_dict()['title']}<br>"
                info += f"<strong>📖 影片介紹：</strong><a href='{doc.to_dict()['hyperlink']}' target='_blank'>連結</a><br>"
                info += f"<strong>⏱️ 片長：</strong>{doc.to_dict()['showLength']} 分鐘<br>"
                info += f"<strong>📅 上映日期：</strong>{doc.to_dict()['showDate']}</p><hr>"
        if not found:
            info += "<p>❌ 找不到相關電影</p>"
        info += "<br><a href='/'>🏠 回首頁</a> | <a href='/searchQ'>🔍 重新查詢</a>"
        info += "</body></html>"
        return info
    else:
        return render_template("input.html")

if __name__ == "__main__":
    app.run(debug=True)
