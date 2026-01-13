# news_summary.py
import os
import feedparser
import requests
from notion_client import Client
from datetime import datetime

# -----------------------------
# 1. 환경 변수 불러오기
# -----------------------------
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_ID"]

# -----------------------------
# 2. RSS Feed 설정
# -----------------------------
RSS_FEEDS = {
    "IT/반도체": {
        "popular": [
            "https://www.zdnet.co.kr/news/rss.xml",  # 상단 2개를 인기 뉴스로 간주
        ],
        "latest": [
            "https://www.zdnet.co.kr/news/rss.xml",
            "https://www.etnews.com/rss/news.xml"
        ]
    },
    "경제": {
        "popular": [
            "https://www.hankyung.com/rss/"  # 상단 2개
        ],
        "latest": [
            "https://www.hankyung.com/rss/",
            "https://rss.mk.co.kr/rss/rss_edition.xml"
        ]
    },
    "정치": {
        "popular": [
            "https://www.yna.co.kr/rss/politics"
        ],
        "latest": [
            "https://www.yna.co.kr/rss/politics",
            "http://rss.chosun.com/rss/politics.xml"
        ]
    }
}

# -----------------------------
# 3. Notion 연결
# -----------------------------
notion = Client(auth=NOTION_TOKEN)

def add_to_notion(category, title, summary, link):
    notion.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties={
            "날짜": {"date": {"start": datetime.now().isoformat()}},
            "카테고리": {"select": {"name": category}},
            "제목": {"title": [{"text": {"content": title}}]},
            "핵심 내용": {"rich_text": [{"text": {"content": summary}}]},
            "링크": {"url": link}
        }
    )

# -----------------------------
# 4. 뉴스 수집
# -----------------------------
def get_news():
    all_news = []
    for category, feeds in RSS_FEEDS.items():
        # 인기 뉴스 2개
        popular_news = []
        for feed_url in feeds["popular"]:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                popular_news.append({
                    "category": category,
                    "title": entry.title,
                    "summary": entry.get("summary", "")[:200],
                    "link": entry.link,
                    "type": "인기"
                })

        # 최신 뉴스 3개
        latest_news = []
        for feed_url in feeds["latest"]:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                # 인기 뉴스와 중복 제거
                if entry.title in [n["title"] for n in popular_news]:
                    continue
                latest_news.append({
                    "category": category,
                    "title": entry.title,
                    "summary": entry.get("summary", "")[:200],
                    "link": entry.link,
                    "type": "최신"
                })
                count += 1
                if count >= 3:
                    break

        all_news.extend(popular_news + latest_news)
    return all_news

# -----------------------------
# 5. Discord 전송
# -----------------------------
def send_to_discord(news_list):
    if not news_list:
        return
    msg = f"📌 오늘 뉴스 ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    for n in news_list:
        msg += f"**[{n['category']} - {n['type']}]** {n['title']}\n- {n['summary']}\n- 링크: {n['link']}\n\n"
    requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})

# -----------------------------
# 6. 메인 실행
# -----------------------------
if __name__ == "__main__":
    news_to_send = get_news()
    send_to_discord(news_to_send)
    for n in news_to_send:
        add_to_notion(n['category'], n['title'], n['summary'], n['link'])
