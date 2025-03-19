from Data_Base.Data_Base import DataBase
from Bot_user.main_bot import get_users_id

db = DataBase('./main.db')

db.create_user_lists_table()
db.create_status_table()
db.create_users_table()
db.insert_new_note_status(864146808, "admin")
get_users_id(["@Yuliamolodtsova03"])
db.get_table("users")