import os
from dotenv import load_dotenv

load_dotenv()

GOLDEN_KEY = os.getenv("GOLDEN_KEY")
MY_ID_TELEGRAM = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")