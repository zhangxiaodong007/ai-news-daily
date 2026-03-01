#!/usr/bin/env python3
"""
微信公众号文章发布脚本
"""

import os
import smtplib
import re
import json
import time
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ========== 配置 ==========
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# 微信公众号配置
WX_APPID = os.getenv("WX_APPID", "")
WX_APPSECRET = os.getenv("WX_APPSECRET", "")
WX_PUBLISH = os.getenv("WX_PUBLISH", "false").lower() == "true"

ITEMS_PER_SOURCE = 15

RSS_SOURCES = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.bensbites.com/feed",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.the-decoder.com/feed/",
    "https://www.zdnet.com/news/rss.xml",
]

SOURCE_WEIGHTS = {
    "techcrunch.com": 5,
    "bensbites.com": 4,
    "venturebeat.com": 4,
    "the-decoder.com": 4,
    "zdnet.com": 3,
}

BOOST_KEYWORDS = [
    "openai", "gpt", "anthropic", "claude", "gemini", "chatgpt",
    "breakthrough", "launch", "release", "announce",
    "model", "research", "investment", "funding",
]

TOKEN_FILE = "wechat_token.json"

def get_access_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            if time.time() - data.get("time", 0) < 7200 - 300:
                print(f"Using cached token: {data.get('token', '')[:10]}...")
                return data.get("token")
    
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WX_APPID}&secret={WX_APPSECRET}"
    try:
        resp = requests.get(url, timeout=10)
        result = resp.json()
        if "access_token" in result:
            token = result["access_token"]
            with open(TOKEN_FILE, "w") as f:
                json.dump({"token": token, "time": time.time()}, f)
            print(f"Got new token: {token[:10]}...")
            return token
        else:
            print(f"Failed to get token: {result}")
            return None
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def create_draft(title, content, author="AI News"):
    token = get_access_token()
    if not token:
        return None
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    
    data = {
        "articles": [{
            "title": title,
            "author": author,
            "content": content,
            "content_source_url": "",
            "digest": content[:120],
            "show_cover_pic": 1,
        }]
    }
    
    try:
        resp = requests.post(url, json=data, timeout=30)
        result = resp.json()
        if result.get("errcode") == 0:
            print(f"Draft created: {result.get('media_id')}")
            return result.get("media_id")
        else:
            print(f"Failed to create draft: {result}")
            return None
    except Exception as e:
        print(f"Error creating draft: {e}")
        return None

def publish_draft(media_id):
    token = get_access_token()
    if not token:
        return False
    
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish?access_token={token}"
    data = {"media_id": media_id, "appmsg_id": ""}
    
    try:
        resp = requests.post(url, json=data, timeout=30)
        result = resp.json()
        if result.get("errcode") == 0:
            print(f"Published! publish_id: {result.get('publish_id')}")
            return True
        else:
            print(f"Failed to publish: {result}")
            return False
    except Exception as e:
        print(f"Error publishing: {e}")
        return False

def get_importance(title, source_url):
    score = 3
    for domain, weight in SOURCE_WEIGHTS.items():
        if domain in source_url:
            score = weight
            break
    title_lower = title.lower()
    for kw in BOOST_KEYWORDS:
        if kw.lower() in title_lower:
            score += 1
    score = max(1, min(10, score))
    
    if score >= 7:
        return "[热门]"
    elif score >= 5:
        return "[重要]"
    elif score >= 3:
        return "[一般]"
    else:
        return ""

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def fetch_rss_items(url, limit=15):
    try:
        import feedparser
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            published = ""
            if hasattr(entry, 'published'):
                published = entry.published[:10]
            
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            title = entry.get("title", "Untitled")
            link = entry.get("link", "")
            importance = get_importance(title, link)
            
            score = sum(1 for kw in BOOST_KEYWORDS if kw.lower() in title.lower())
            score += SOURCE_WEIGHTS.get([d for d in SOURCE_WEIGHTS if d in link][0], 3)
            
            items.append({
                "title": title,
                "link": link,
                "summary": summary[:500] if summary else "无摘要",
                "published": published,
                "source": feed.feed.get("title", url),
                "importance": importance,
                "score": score
            })
        return items
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def generate_wechat_html(news_items):
    sources = {}
    for item in news_items:
        src = item.get("source", "Unknown")
        if src not in sources:
            sources[src] = []
        sources[src].append(item)
    
    news_items_sorted = sorted(news_items, key=lambda x: x.get("score", 0), reverse=True)
    top_items = [i for i in news_items_sorted if i.get("score", 0) >= 6]
    
    html = f"""
<p style="text-align: center;"><strong><span style="font-size: 18px;">🤖 AI 动态简报</span></strong></p>
<p style="text-align: center; color: #888;">{datetime.now().strftime('%Y年%m月%d日')} · 共 {len(news_items)} 条 · {len(sources)} 个来源</p>
<hr/>
"""
    
    if top_items:
        html += f"<p style='color: #e74c3c;'><strong>🔥 重要新闻</strong></p>"
        for item in top_items[:10]:
            meta = f" [{item['published']}]" if item.get('published') else ""
            imp = item.get("importance", "")
            html += f"""
<p><strong><a href="{item['link']}">{item['title']}</a></strong> {imp}</p>
<p style="color: #888; font-size: 12px;">{item['source']}{meta}</p>
<p>{item['summary']}</p>
<hr/>
"""
    
    for source_name, items in sources.items():
        html += f"<p><strong>{source_name}</strong></p>"
        for item in items:
            meta = f" [{item['published']}]" if item.get('published') else ""
            imp = item.get("importance", "")
            html += f"""
<p><strong><a href="{item['link']}">{item['title']}</a></strong> {imp}</p>
<p style="color: #888; font-size: 12px;">{item['source']}{meta}</p>
<p>{item['summary']}</p>
"""
    
    html += f"""
<hr/>
<p style="text-align: center; color: #888; font-size: 12px;">由 GitHub Actions 自动生成</p>
"""
    return html

def send_email(html_content, news_items):
    if not all([SMTP_USER, SMTP_PASSWORD, TO_EMAIL]):
        print("Missing email config")
        return False
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"AI 动态简报 {datetime.now().strftime('%Y年%m月%d日')} - 共{len(news_items)}条"
    msg['From'] = SMTP_USER
    msg['To'] = TO_EMAIL
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {TO_EMAIL}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    print("Fetching AI news...")
    all_news = []
    
    for source in RSS_SOURCES:
        items = fetch_rss_items(source, limit=ITEMS_PER_SOURCE)
        print(f"{source}: {len(items)} items")
        all_news.extend(items)
    
    print(f"Total: {len(all_news)} items")
    
    wechat_html = generate_wechat_html(all_news)
    
    with open("ai_news.html", "w", encoding="utf-8") as f:
        f.write(wechat_html)
    
    send_email(wechat_html, all_news)
    
    if WX_PUBLISH and WX_APPID and WX_APPSECRET:
        title = f"AI 动态简报 {datetime.now().strftime('%Y年%m月%d日')}"
        media_id = create_draft(title, wechat_html)
        if media_id:
            publish_draft(media_id)
    
    print("Done!")

if __name__ == "__main__":
    main()
