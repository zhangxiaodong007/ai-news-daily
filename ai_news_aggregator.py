#!/usr/bin/env python3
"""
AI News Aggregator - 每天自动抓取AI新闻并发送到邮箱
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import urllib.request
import json

# ========== 配置 ==========
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# RSS 源（可自行增减）
# 注意：Ben's Bites 和 The Rundown AI 是 Newsletter 无公开 RSS
RSS_SOURCES = [
    # 学术
    "http://arxiv.org/rss/cs.LG",
    
    # 英文科技媒体
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai/index.xml",
    "https://wired.com/feed/tag/ai/rss",
    
    # Hacker News
    "https://hnrss.org/newest?q=ai",
    "https://hnrss.org/newest?q=machine+learning",
    
    # 中文
    "https://www.jiqizhixin.com/?feed=rss2",
    "https://www.36kr.com/information/AI/",
]
RSS_SOURCES = [
    "http://arxiv.org/rss/cs.LG",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.jiqizhixin.com/?feed=rss2",
]

def fetch_rss_items(url, limit=5):
    """抓取 RSS 源"""
    try:
        import feedparser
        feed = feedparser.parse(url)
        return [
            {
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", entry.get("description", ""))[:200],
                "source": feed.feed.get("title", url)
            }
            for entry in feed.entries[:limit]
        ]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def generate_html(news_items):
    """生成 HTML 邮件内容"""
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
            .item {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
            .title {{ font-size: 16px; font-weight: 600; color: #1a1a2e; }}
            .summary {{ color: #666; font-size: 14px; margin-top: 5px; }}
            .source {{ color: #999; font-size: 12px; margin-top: 5px; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI 动态简报</h1>
            <p>{datetime.now().strftime('%Y年%m月%d日')}</p>
        </div>
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    """
    
    for item in news_items:
        html += f"""
            <div class="item">
                <div class="title">{item['title']}</div>
                <div class="summary">{item['summary']}...</div>
                <div class="source">📌 {item['source']}</div>
            </div>
        """
    
    html += f"""
        </div>
        <div class="footer">
            <p>由 GitHub Actions 自动生成</p>
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
    msg['Subject'] = f"🤖 AI 动态简报 - {datetime.now().strftime('%Y年%m月%d日')}"
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
        items = fetch_rss_items(source)
        all_news.extend(items)
    
    # 按来源分组输出
    print(f"Got {len(all_news)} news items")
    
    html = generate_html(all_news)
    
    # 本地测试输出 HTML
    with open("ai_news.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML saved to ai_news.html")
    
    send_email(html)
    print("Done!")

if __name__ == "__main__":
    main()
