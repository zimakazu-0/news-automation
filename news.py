import os
import json
import gspread
from google.oauth2.service_account import Credentials
import requests

# Copilot API（ニュース要約用）
COPILOT_API_KEY = os.getenv("COPILOT_API_KEY")

# Google Sheets 設定
SPREADSHEET_ID = "1xzkOLXbdw0ZdRZVXJME3Pyafqu2VI5wiEcwCYQ_kSZU"

# Google 認証
creds_json = os.getenv("GOOGLE_CREDENTIALS")
creds_dict = json.loads(creds_json)

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1


# ニュース取得（例として Bing News API を使用）
def fetch_news():
    url = "https://api.bing.microsoft.com/v7.0/news/search"
    headers = {"Ocp-Apim-Subscription-Key": COPILOT_API_KEY}
    params = {"q": "Japan news", "count": 10}

    res = requests.get(url, headers=headers, params=params)
    data = res.json()

    articles = []
    for item in data.get("value", []):
        articles.append({
            "title": item["name"],
            "url": item["url"],
            "description": item.get("description", "")
        })
    return articles


# Copilot API で要約
def summarize(text):
    url = "https://api.githubcopilot.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {COPILOT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "ニュース記事を短く要約してください。"},
            {"role": "user", "content": text}
        ]
    }

    res = requests.post(url, headers=headers, json=payload)
    result = res.json()
    return result["choices"][0]["message"]["content"]


# スプレッドシートに書き込み
def write_to_sheet(article):
    row = [
        "",  # 使用日（空欄）
        article["title"],
        article["summary"],
        article["url"],
        article["category"],
        ""  # メモ欄（空欄）
    ]
    sheet.append_row(row)


# カテゴリ推定（簡易版）
def guess_category(text):
    if "経済" in text or "株" in text:
        return "経済"
    if "政治" in text:
        return "政治"
    if "スポーツ" in text:
        return "スポーツ"
    return "その他"


def main():
    news_list = fetch_news()

    for article in news_list:
        summary = summarize(article["description"])
        category = guess_category(summary)

        article["summary"] = summary
        article["category"] = category

        write_to_sheet(article)


if __name__ == "__main__":
    main()
