import requests
import json
import schedule
import time
from datetime import datetime

TELEGRAM_TOKEN = "8713109503:AAFhnMxJ_bWc7Xblcnhlkku9vx6yBojPSMI"
CHAT_ID = "183949961"
NEWS_API_KEY = "1d32e5787bba4e3a8f5d195bcd0f40d4"

def get_markets():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Origin": "https://polymarket.com",
        "Referer": "https://polymarket.com/"
    })
    response = session.get(
        "https://gamma-api.polymarket.com/markets",
        params={"active": "true", "limit": 50, "order": "volume24hr", "ascending": "false"},
        timeout=15
    )
    return response.json()

def get_news(query):
    response = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 3
        },
        timeout=10
    )
    data = response.json()
    articles = data.get("articles", [])
    if not articles:
        return "Новин не знайдено"
    news_text = ""
    for a in articles[:2]:
        title = a.get("title", "")[:80]
        news_text += f"• {title}\n"
    return news_text

def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    )

def analyze_and_send():
    markets = get_markets()
    message = f"🎯 <b>Топ ставки + Новини</b>\n📅 {datetime.now().strftime('%d.%m %H:%M')}\n\n"
    count = 0

    for m in markets:
        liquidity = float(m.get('liquidity') or 0)
        question = m.get('question', '')[:65]
        end_date = m.get('endDate', '')[:10]

        if liquidity < 5000:
            continue

        try:
            outcomes = m.get('outcomePrices', '[0.5,0.5]')
            prices = json.loads(outcomes) if isinstance(outcomes, str) else outcomes
            yes_price = float(prices[0]) if prices else 0.5
        except:
            yes_price = 0.5

        if yes_price < 0.05 or yes_price > 0.95:
            continue

        profit = round((1 / yes_price - 1) * 100, 1)

        if yes_price < 0.5:
            emoji = "🔴"
        elif yes_price < 0.75:
            emoji = "🟡"
        else:
            emoji = "🟢"

        # Шукаємо новини по ключових словах ринку
        keywords = question[:30]
        news = get_news(keywords)

        message += f"{emoji} <b>{question}</b>\n"
        message += f"💰 YES: {round(yes_price*100)}¢ | +{profit}%\n"
        message += f"💧 ${liquidity:,.0f} | 📅 {end_date}\n"
        message += f"📰 {news}\n"
        count += 1

        if count >= 5:
            break

    send_telegram(message)
    print(f"Надіслано {count} ринків з новинами!")

def check_status():
    send_telegram(f"✅ Бот живий! {datetime.now().strftime('%d.%m %H:%M')}")

schedule.every(6).hours.do(analyze_and_send)
schedule.every().day.at("09:00").do(check_status)

send_telegram("🤖 Бот з новинами запущено!")
analyze_and_send()

while True:
    schedule.run_pending()
    time.sleep(60)