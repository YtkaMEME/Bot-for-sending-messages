import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import UsernameNotOccupiedError, RPCError

from config import API_ID, API_HASH, ADMIN_USERNAME, SESSION_PATH

async def get_users_id(usernames):
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        users_ids = []
        for username in usernames:
            try:
                user = await client(GetFullUserRequest(username))
                users_ids.append(user.full_user.id)
            except UsernameNotOccupiedError:
                print(f'Пользователь "{username}" не найден.')
                users_ids.append(None)
            except RPCError as e:
                print(f'Ошибка при получении данных пользователя {username}: {e}')
                users_ids.append(None)
        return users_ids
