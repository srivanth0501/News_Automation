import requests
from bs4 import BeautifulSoup
import feedparser
import random
import time
import json
import subprocess
from datetime import datetime
import logging

logging.basicConfig(
    filename="automation.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

def generate_mock_engagement():
    return {
        'likes': random.randint(50, 500),
        'shares': random.randint(10, 100),
        'comments': random.randint(5, 50)
    }


def fetch_cnbc_top_news(limit=5):
    url = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    feed = feedparser.parse(url)
    return [{
        'source': 'CNBC',
        'title': entry.title,
        'subhead': entry.get('summary', None),
        'url': entry.link,
        'engagement': generate_mock_engagement()
    } for entry in feed.entries[:limit]]


def fetch_yahoo_finance_news(limit=5):
    url = 'https://www.yahoo.com/news/rss'
    try:
        feed = feedparser.parse(url)
        return [{
            'source': 'Yahoo News',
            'title': entry.title,
            'subhead': entry.get('summary', None),
            'url': entry.link,
            'engagement': generate_mock_engagement()
        } for entry in feed.entries[:limit]]
    except Exception as e:
        logging.info(" Error fetching Yahoo Finance: {}".format(e))
        return []



def fetch_ft_news(limit=5):
    rss_url = "https://www.ft.com/rss/markets"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        xml = requests.get(rss_url, headers=headers).text
        feed = feedparser.parse(xml)
        results = []
        for entry in feed.entries[:limit]:
            results.append({
                'source': 'Financial Times',
                'title': entry.title,
                'subhead': entry.get('summary', None),
                'url': entry.link,
                'engagement': generate_mock_engagement()
            })
        if not results:
            logging.info(" No FT stories found")
        return results
    except Exception as e:
        logging.info(" Error fetching FT: {}".format(e))
        return []



def fetch_bloomberg_news(limit=5, max_retries=3, attempt=1):
    url = 'https://www.bloomberg.com/markets'
    headers = {'User-Agent': random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)"
    ])}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        links = soup.select('a[href^="/news/articles/"], a[data-tracking-name="Story Link"]')
        results = []
        seen_titles = set()

        for link in links:
            title = link.get_text(strip=True)
            href = link.get('href')
            if not title or not href or title in seen_titles:
                continue
            full_url = 'https://www.bloomberg.com' + href if href.startswith('/') else href
            results.append({
                'source': 'Bloomberg',
                'title': title,
                'subhead': None,
                'url': full_url,
                'engagement': generate_mock_engagement()
            })
            seen_titles.add(title)
            if len(results) >= limit:
                break

        if not results and attempt < max_retries:
            logging.info(" Bloomberg retrying (Attempt {})".format(attempt))
            time.sleep(5)
            return fetch_bloomberg_news(limit, max_retries, attempt + 1)
        return results
    except Exception as e:
        logging.info(" Error fetching Bloomberg: {}".format(e))
        return []


def compute_engagement_score(story):
    e = story['engagement']
    return e['likes'] * 1.0 + e['shares'] * 1.5 + e['comments'] * 2.0


def get_top_engaging_stories_per_source(all_stories):
    best_by_source = {}
    for story in all_stories:
        source = story['source']
        score = compute_engagement_score(story)
        if source not in best_by_source or compute_engagement_score(best_by_source[source]) < score:
            best_by_source[source] = story
    return list(best_by_source.values())

def get_crm_schedule_slot():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour = now.hour
    if hour < 10:
        return f"{today} 08:30"
    elif hour < 14:
        return f"{today} 12:30"
    else:
        return f"{today} 17:30"


def safe_fetch(func, label):
    try:
        return func()
    except Exception as e:
        logging.info(f" Error in {label}: {e}")
        return []


if __name__ == "__main__":
    logging.info("Starting fetch at {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))

    all_news = []
    all_news.extend(safe_fetch(fetch_cnbc_top_news, "CNBC"))
    all_news.extend(safe_fetch(fetch_yahoo_finance_news, "Yahoo"))
    all_news.extend(safe_fetch(fetch_ft_news, "Financial Times"))
    all_news.extend(safe_fetch(fetch_bloomberg_news, "Bloomberg"))

    crm_time = get_crm_schedule_slot()

    try:
        with open("recent_stories.json", "w", encoding='utf-8') as f:
            json.dump(all_news, f, indent=2, ensure_ascii=False)
        logging.info(" Saved recent_stories.json")
    except Exception as e:
        logging.info(" Failed to save recent_stories.json:", e)
    top_items = get_top_engaging_stories_per_source(all_news)
    for story in top_items:
        story['scheduled_time'] = crm_time

    try:
        with open("top_stories.json", "w", encoding='utf-8') as f:
            json.dump(top_items, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved top_stories.json with CRM slot: {crm_time}")
    except Exception as e:
        logging.info(" Failed to save top_stories.json:", e)
        exit()

    try:
        logging.info(" Running rewrite.py...")
        subprocess.run(["python", "rewrite.py"], check=True)
        logging.info(" rewrite.py executed successfully")
    except Exception as e:
        logging.info(f"Failed to run rewrite.py: {e}")

