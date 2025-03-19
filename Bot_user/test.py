import time
from Data_Base.Data_Base import DataBase
from telethon import TelegramClient, events

api_id = '22559179'
api_hash = 'f799f7e36376e16bd657e243888b7ffa'
db_name = '../main.db'
admins = [864146808]

client = TelegramClient('anon', api_id, api_hash)

async def main():
    print("Клиент подключается...")
    await client.start()
    if client.is_connected():
        print("Клиент успешно подключен.")
    else:
        print("Клиент не смог подключиться.")

def end_point(db, user_id):
    db.set_standart(user_id)

@client.on(events.NewMessage())
async def handler(event):
    print(f"Новое сообщение от {event.sender_id}: {event.message.message}")

    user_id = event.sender_id
    message = event.message.message

    try:
        db = DataBase(db_name)
        state = db.get_state(user_id)[0]
        status = db.get_status(user_id)[0]

        print(f"Состояние: {state}, Статус: {status}")

        if not state:
            db.insert_new_note_status(user_id, "empty", "user")
            state = "empty"
            status = "user"

        if state == "empty" and status == "admin":
            if message == 'Отправь кураторам':
                list_users = db.get_unique_elements('users_mail', 'ФИО')
                list_users_str = "\n".join(list_users)
                await event.respond(f'Это все люди, которым мне нужно написать? \n{list_users_str}')
                db.edit_state(user_id, "yes_no_empty")

        if state == "message" and status == "admin":
            list_users = db.get_unique_elements('users_mail', 'ФИО')
            list_users_str = "\n".join(list_users)
            await event.respond(f'{message}\nДля людей из списка:\n{list_users_str}\n\nВсе верно?')
            db.edit_state(user_id, message)
            db.edit_state(user_id, f"yes_no_message")

        if state in ['yes_no_empty', "yes_no_message", "yes_no_edit"] and status == "admin":
            message = str.lower(message)
            if message == 'да':
                if state == "yes_no_empty":
                    await event.respond('Напишите мне текст сообщения для отправки, пожалуйста.')
                    db.edit_state(user_id, "message")
                elif state == "yes_no_message":
                    message_text = db.get_data(user_id)
                    list_users = db.get_unique_elements('users_mail', 'ФИО')
                    for user in list_users:
                        try:
                            await client.send_message(user, message_text)
                            time.sleep(2)
                        except Exception as e:
                            await event.respond(f"Ошибка отправки сообщения пользователю {user}: {e}")
                    await event.respond('Рассылка завершена.')
                    end_point(user_id)
            elif message == 'нет':
                if state == "yes_no_empty":
                    await event.respond(f'Вы хотите изменить имеющийся список '
                                        f'или создать временный новый только для этой рассылки?\n\n'
                                        f'Для выбора варианта ответа введите "Постоянный" или "Временный"')
                    db.edit_state(user_id, "yes_no_edit")
                elif state == "yes_no_message":
                    await event.respond('Исправьте ошибки и неточности и напишите мне текст сообщения для отправки повторно.')
                    db.edit_state(user_id, ",essage")
            elif message == 'постоянный':
                pass
            elif message == "временный":
                pass
    except Exception as e:
        print(f"Ошибка при обработке: {e}")

client.loop.run_until_complete(main())
client.run_until_disconnected()
