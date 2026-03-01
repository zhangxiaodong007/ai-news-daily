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

# RSS 源 - 可靠的英文科技源
RSS_SOURCES = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.bensbites.com/feed",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.the-decoder.com/feed/",
    "https://www.zdnet.com/news/rss.xml",
]

# RSS 源 - 使用更可靠的来源
RSS_SOURCES = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai/index.xml",
    "https://wired.com/feed/tag/ai/rss",
    "https://www.bensbites.com/feed",
    "https://venturebeat.com/category/ai/feed/",
]

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)
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
    esc = html_module.escape
    
    # 按来源分组
    sources = {}
    for item in news_items:
        src = item.get("source", "Unknown")
        if src not in sources:
            sources[src] = []
        sources[src].append(item)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; background: #f5f5f5; }}
        .container {{ max-width: 700px; margin: 0 auto; background: #fff; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 30px 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
        .header .date {{ margin-top: 8px; opacity: 0.8; }}
        .header .stats {{ margin-top: 10px; font-size: 12px; opacity: 0.6; }}
        
        .source-section {{ padding: 20px; border-bottom: 1px solid #eee; }}
        .source-title {{ font-size: 16px; font-weight: 600; color: #1a1a2e; margin-bottom: 15px; display: flex; align-items: center; }}
        .source-title::before {{ content: ''; display: inline-block; width: 4px; height: 16px; background: #4f46e5; margin-right: 10px; border-radius: 2px; }}
        
        .item {{ padding: 15px 0; border-bottom: 1px solid #f0f0f0; }}
        .item:last-child {{ border-bottom: none; }}
        
        .item-title {{ font-size: 15px; font-weight: 600; line-height: 1.4; }}
        .item-title a {{ color: #1a1a2e; text-decoration: none; }}
        .item-title a:hover {{ color: #4f46e5; }}
        
        .item-meta {{ margin-top: 6px; font-size: 12px; color: #999; }}
        .item-summary {{ margin-top: 8px; font-size: 13px; color: #666; line-height: 1.6; }}
        
        .footer {{ background: #f9f9f9; padding: 20px; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI 动态简报</h1>
            <div class="date">{datetime.now().strftime('%Y年%m月%d日 %A')}</div>
            <div class="stats">共 {len(news_items)} 条资讯 · {len(sources)} 个来源</div>
        </div>
"""
    
    for source_name, items in sources.items():
        html += f'<div class="source-section"><div class="source-title">{esc(str(source_name))}</div>'
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
    
    html = generate_html(all_news)
    
    with open("ai_news.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    send_email(html, all_news)
    print("Done!")

if __name__ == "__main__":
    main()
