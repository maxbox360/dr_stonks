import os
import datetime
import yfinance as yf
from atproto import Client, models
from PIL import Image
from dotenv import load_dotenv

# Configuration
DJIA_SYMBOL = "^DJI"
SP500_SYMBOL = "^GSPC"

IMAGE_DIR = "images"
STONKS_IMAGE = os.path.join(IMAGE_DIR, "stonks.png")
NOT_STONKS_IMAGE = os.path.join(IMAGE_DIR, "not_stonks.png")

def get_env(name):
    try:
        load_dotenv()
        secret = os.getenv(name)

        return secret

    except Exception as e:
        print(f"Error loading secrets: {e}")


def compress_image(image_path, max_size=970):
    img = Image.open(image_path)
    img = img.convert("RGB")  # Convert to RGB (removes transparency)

    quality = 85  # Start at 85% quality
    while True:
        img.save(image_path, "JPEG", quality=quality)
        if os.path.getsize(image_path) / 1024 <= max_size or quality <= 10:
            break
        quality -= 5  # Decrease quality in steps
    return image_path


# Get previous market close date
def get_previous_market_date():
    today = datetime.datetime.today()
    if today.weekday() == 0:
        delta = 3
    else:
        delta = 1
    previous_day = today - datetime.timedelta(days=delta)
    return previous_day.strftime("%Y-%m-%d")


# Fetch market data
def fetch_market_close(symbol):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="5d")
    if len(hist) < 2:
        print("Not enough data available.")
        return None, None

    today_close = hist["Close"].iloc[-1]
    prev_close = hist["Close"].iloc[-2]

    return today_close, prev_close


# Post to Bluesky
def post_to_bluesky(text, image_path):
    username = get_env("BLUESKY_USERNAME")
    password = get_env("BLUESKY_PASSWORD")

    client = Client()
    client.login(username, password)

    compressed_image = compress_image(image_path)

    with open(compressed_image, "rb") as img:
        image_blob = client.upload_blob(img.read())

    image_embed = models.AppBskyEmbedImages.Main(images=[
        models.AppBskyEmbedImages.Image(alt="Market Update", image=image_blob.blob)
    ])

    client.send_post(text=text, embed=image_embed)


# Main function
def main():
    for symbol, name in [(DJIA_SYMBOL, "Dow Jones"), (SP500_SYMBOL, "S&P 500")]:
        today_close, prev_close = fetch_market_close(symbol)
        if today_close is None or prev_close is None:
            continue

        change = today_close - prev_close
        percentage_change = (change / prev_close) * 100

        if change > 0:
            image = STONKS_IMAGE
            message = f"stonks\n\n{name} 📈: {today_close:.2f} (+{change:.2f}, {percentage_change:.2f}%)"
        else:
            image = NOT_STONKS_IMAGE
            message = f"not stonks\n\n{name} 📉: {today_close:.2f} ({change:.2f}, {percentage_change:.2f}%)"

        post_to_bluesky(message, image)


if __name__ == "__main__":
    main()
