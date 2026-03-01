#!/usr/bin/env python3
"""
AI News Aggregator - 每天自动抓取AI新闻并发送到邮箱
"""

import os
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import html as html_module

# ========== 配置 ==========
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

ITEMS_PER_SOURCE = 5

RSS_SOURCES = [
    "http://arxiv.org/rss/cs.LG",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.jiqizhixin.com/?feed=rss2",
]

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)
    return text.strip()

def fetch_rss_items(url, limit=5):
    try:
        import feedparser
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            published = ""
            if hasattr(entry, 'published'):
                published = entry.published[:10]
            
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            
            items.append({
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": summary[:200] if summary else "无摘要",
                "published": published,
                "source": feed.feed.get("title", url)
            })
        return items
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def generate_html(news_items):
    esc = html_module.escape
    
    html = f"""<html>
<head><meta charset="utf-8"></head>
<body>
<h1>AI 动态简报 {datetime.now().strftime('%Y年%m月%d日')}</h1>
<p>共 {len(news_items)} 条</p>
<hr>
"""
    
    for item in news_items:
        meta = f" [{item['published']}]" if item.get('published') else ""
        html += f"""
<p>
<strong><a href="{esc(item['link'])}">{esc(item['title'])}</a></strong><br>
<small>{esc(item['source'])}{esc(meta)}</small><br>
{esc(item['summary'])}
</p>
"""
    
    html += """
<hr>
<p><small>由 GitHub Actions 自动生成</small></p>
</body>
</html>
"""
    return html

def send_email(html_content):
    if not all([SMTP_USER, SMTP_PASSWORD, TO_EMAIL]):
        print("Missing email config")
        return False
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"AI 动态简报 {datetime.now().strftime('%Y年%m月%d日')}"
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
        all_news.extend(items)
    
    print(f"Total: {len(all_news)} items")
    
    html = generate_html(all_news)
    
    with open("ai_news.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    send_email(html)
    print("Done!")

if __name__ == "__main__":
    main()
