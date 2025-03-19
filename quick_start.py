from Data_Base.Data_Base import DataBase
from Bot_user.main_bot import get_users_id
import asyncio

db = DataBase('./main.db')

# Добавляем нового администратора
db.insert_new_note_status(864146808, "admin")

# Получаем и добавляем пользователей
asyncio.run(get_users_id(["@Yuliamolodtsova03"]))
 
# Выводим содержимое таблицы пользователей
print(db.get_table("users"))