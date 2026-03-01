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

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

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
    "模型", "发布", "融资", "突破",
]

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
        return "[🔥热门]"
    elif score >= 5:
        return "[⭐重要]"
    elif score >= 3:
        return "[一般]"
    else:
        return ""

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
            title = entry.get("title", "Untitled")
            link = entry.get("link", "")
            importance = get_importance(title, link)
            
            # 计算得分
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

def generate_html(news_items):
    esc = html_module.escape
    
    sources = {}
    for item in news_items:
        src = item.get("source", "Unknown")
        if src not in sources:
            sources[src] = []
        sources[src].append(item)
    
    news_items_sorted = sorted(news_items, key=lambda x: x.get("score", 0), reverse=True)
    top_items = [i for i in news_items_sorted if i.get("score", 0) >= 6]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; background: #f5f5f5; }}
        .container {{ max-width: 700px; margin: 0 auto; background: #fff; }}
        .header {{ background: #1a1a2e; color: #fff; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header .date {{ margin-top: 8px; color: #ccc; }}
        .header .stats {{ margin-top: 8px; font-size: 12px; color: #999; }}
        .source-section {{ padding: 15px 20px; border-bottom: 1px solid #eee; }}
        .source-title {{ font-size: 15px; font-weight: 600; color: #333; margin-bottom: 12px; }}
        .item {{ padding: 12px 0; border-bottom: 1px solid #f0f0f0; }}
        .item:last-child {{ border-bottom: none; }}
        .item-title {{ font-size: 14px; font-weight: 600; line-height: 1.4; }}
        .item-title a {{ color: #1a1a2e; text-decoration: none; }}
        .imp-hot {{ color: #ef4444; font-weight: bold; }}
        .imp-star {{ color: #f59e0b; font-weight: bold; }}
        .item-meta {{ margin-top: 4px; font-size: 12px; color: #999; }}
        .item-summary {{ margin-top: 6px; font-size: 13px; color: #666; line-height: 1.5; }}
        .footer {{ padding: 20px; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI 动态简报</h1>
            <div class="date">{datetime.now().strftime('%Y年%m月%d日')}</div>
            <div class="stats">共 {len(news_items)} 条 · {len(sources)} 个来源</div>
        </div>
"""
    
    if top_items:
        html += '<div class="source-section"><div class="source-title">🔥 重要新闻</div>'
        for item in top_items[:10]:
            meta = f" · {item['published']}" if item.get('published') else ""
            imp = item.get("importance", "")
            imp_class = "imp-hot" if "热门" in imp else "imp-star"
            html += f'<div class="item"><div class="item-title"><a href="{esc(item["link"])}">{esc(item["title"])}</a> <span class="{imp_class}">{esc(imp)}</span></div><div class="item-meta">{esc(item["source"])}{esc(meta)}</div><div class="item-summary">{esc(item["summary"])}</div></div>'
        html += '</div>'
    
    for source_name, items in sources.items():
        html += f'<div class="source-section"><div class="source-title">{esc(str(source_name))}</div>'
        for item in items:
            meta = f" · {item['published']}" if item.get('published') else ""
            imp = item.get("importance", "")
            html += f'<div class="item"><div class="item-title"><a href="{esc(item["link"])}">{esc(item["title"])}</a> <span>{esc(imp)}</span></div><div class="item-meta">{esc(item["source"])}{esc(meta)}</div><div class="item-summary">{esc(item["summary"])}</div></div>'
        html += '</div>'
    
    html += '<div class="footer"><p>由 GitHub Actions 自动生成</p></div></div></body></html>'
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
