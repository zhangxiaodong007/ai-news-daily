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

# 每个源抓取数量
ITEMS_PER_SOURCE = 15

# RSS 源
RSS_SOURCES = [
    "http://arxiv.org/rss/cs.LG",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.jiqizhixin.com/?feed=rss2",
]

def clean_html(text):
    """清理HTML标签"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)
    return text.strip()

def fetch_rss_items(url, limit=15):
    """抓取 RSS 源"""
    try:
        import feedparser
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            published = ""
            if hasattr(entry, 'published'):
                published = entry.published[:10]
            elif hasattr(entry, 'updated'):
                published = entry.updated[:10]
            
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            
            items.append({
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": summary[:500] if summary else "无摘要",
                "published": published,
                "source": feed.feed.get("title", url)
            })
        return items
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def generate_html(news_items):
    """生成 HTML 邮件内容"""
    sources = {}
    for item in news_items:
        src = item.get("source", "Unknown")
        if src not in sources:
            sources[src] = []
        sources[src].append(item)
    
    esc = html_module.escape
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; background: #f5f5f5; }}
        .container {{ max-width: 700px; margin: 0 auto; background: #fff; }}
        .header {{ background: #1a1a2e; color: #fff; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .source-section {{ padding: 20px; border-bottom: 1px solid #eee; }}
        .item {{ padding: 12px 0; border-bottom: 1px solid #f0f0f0; }}
        .item-title {{ font-size: 15px; font-weight: 600; }}
        .item-title a {{ color: #1a1a2e; text-decoration: none; }}
        .item-meta {{ font-size: 12px; color: #999; margin-top: 4px; }}
        .item-summary {{ font-size: 13px; color: #666; margin-top: 6px; line-height: 1.5; }}
        .footer {{ padding: 20px; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI 动态简报</h1>
            <p>{datetime.now().strftime('%Y年%m月%d日')} · 共 {len(news_items)} 条</p>
        </div>
"""
    
    for source_name, items in sources.items():
        html += f'<div class="source-section"><h3>{esc(str(source_name))}</h3>'
        for item in items:
            meta = f" · {item['published']}" if item.get('published') else ""
            html += f"""
        <div class="item">
            <div class="item-title"><a href="{esc(item['link'])}">{esc(item['title'])}</a></div>
            <div class="item-meta">{esc(item['source'])}{esc(meta)}</div>
            <div class="item-summary">{esc(item['summary'])}</div>
        </div>
"""
        html += '</div>'
    
    html += """
        <div class="footer">
            <p>由 GitHub Actions 自动生成</p>
        </div>
    </div>
</body>
</html>
"""
    return html

def send_email(html_content):
    """发送邮件"""
    if not all([SMTP_USER, SMTP_PASSWORD, TO_EMAIL]):
        print("Missing email config, skipping send")
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
        print(f"Fetching: {source}")
        items = fetch_rss_items(source, limit=ITEMS_PER_SOURCE)
        print(f"  -> Got {len(items)} items")
        all_news.extend(items)
    
    print(f"Total: {len(all_news)} items")
    
    html = generate_html(all_news)
    
    with open("ai_news.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML saved")
    
    send_email(html)
    print("Done!")

if __name__ == "__main__":
    main()
