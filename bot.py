import requests
import json
from datetime import datetime

TELEGRAM_TOKEN = "8713109503:AAFhnMxJ_bWc7Xblcnhlkku9vx6yBojPSMI"
CHAT_ID = "183949961"

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

def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    )

def analyze_and_send():
    markets = get_markets()
    message = "🎯 <b>Найкращі ставки Polymarket:</b>\n\n"
    count = 0

    for m in markets:
        liquidity = float(m.get('liquidity') or 0)
        volume = float(m.get('volume24hr') or 0)
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

        if yes_price < 0.03 or yes_price > 0.97:
            continue

        profit = round((1 / yes_price - 1) * 100, 1)

        if yes_price < 0.5:
            emoji = "🔴"
        elif yes_price < 0.75:
            emoji = "🟡"
        else:
            emoji = "🟢"

        message += f"{emoji} <b>{question}</b>\n"
        message += f"💰 YES: {round(yes_price*100)}¢ | +{profit}%\n"
        message += f"💧 ${liquidity:,.0f} | 📅 {end_date}\n\n"
        count += 1

        if count >= 8:
            break

    message += f"📡 Знайдено {count} ринків | {datetime.now().strftime('%H:%M')}"
    send_telegram(message)
    print(f"Надіслано {count} ринків!")

print("Бот запущено!")
analyze_and_send()
import schedule
import time

def check_status():
    send_telegram("✅ Бот живий! Наступний сигнал через 6 годин.")

schedule.every(6).hours.do(analyze_and_send)
schedule.every().day.at("09:00").do(check_status)

send_telegram("🤖 Бот запущено! Перший сигнал надходить зараз...")
analyze_and_send()

while True:
    schedule.run_pending()
    time.sleep(60)