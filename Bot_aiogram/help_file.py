# import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import Bot
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
