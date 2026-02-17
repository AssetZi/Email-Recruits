import requests

token = '8592057471:AAGm-rWWk2-QqM2FdZFebLBkIBgUFjQHbIo'
chatId = '8335386870'
def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, data={"chat_id": chatId, "text": text})
    r.raise_for_status()

# test:
send_telegram("hello from python")