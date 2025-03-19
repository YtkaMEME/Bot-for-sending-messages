import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, FSInputFile, \
    InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import help_file
from Bot_user.main_bot import get_users_id
from Data_Base.Data_Base import DataBase
from config import DB_PATH

router = Router()
db_name = DB_PATH
bot = help_file.bot
class MainState(StatesGroup):
    status = State()
    empty = State()
    message = State()
    yes_no_empty = State()
    message_yes_no = State()
    yes_no_edit = State()
    data = State()
    create_list_users = State()
    create_list_users_yes_no = State()
    create_list_users_again = State()
    empty_yes_no = State()
    edit_mode_menu_yes_no = State()
    edit_mode_user_digit = State()
    edit_mode_user_yes_no = State()
    edit_mode_number_of_user_delete = State()
    edit_mode_add_user = State()
    edit_mode_add_user_yes_no = State()
    edit_mode_delete_list = State()
    edit_mode_delete_list_yes_no = State()
    admin_management = State()
    admin_username_input = State()
    admin_confirmation = State()

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def get_keyboard(message="Выберите вариант ответа", answer_yes="Да", answer_no="Нет", answer_3=None, inline=False):
    kb = []
    if answer_yes and answer_no:
        if inline:
            kb.append([
                InlineKeyboardButton(text=f"{answer_yes}", callback_data=f"{answer_yes}"),
                InlineKeyboardButton(text=f"{answer_no}", callback_data=f"{answer_no}")
            ])
        else:
            kb.append([
                KeyboardButton(text=f"{answer_yes}"),
                KeyboardButton(text=f"{answer_no}")
            ])
    elif answer_yes:
        if inline:
            kb.append([InlineKeyboardButton(text=f"{answer_yes}", callback_data=f"{answer_yes}")])
        else:
            kb.append([KeyboardButton(text=f"{answer_yes}")])
    elif answer_no:
        if inline:
            kb.append([InlineKeyboardButton(text=f"{answer_no}", callback_data=f"{answer_no}")])
        else:
            kb.append([KeyboardButton(text=f"{answer_no}")])

    if inline:
        keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder=f"{message}",
        )

    return keyboard

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправь Кураторам")],
            [KeyboardButton(text="Режим редактирования")],
            [KeyboardButton(text="Управление администраторами")],
            [KeyboardButton(text="Отменить все действия")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
    return keyboard

async def get_status(state, message, first_start=False):
    user_data = await state.get_data()
    if "status" not in user_data or first_start:
        db = DataBase(db_name)
        status_data = db.get_status(message.from_user.id)
        
        # Если первый старт и пользователь не существует, создаем его
        if status_data is None:

            db.update_status(message.from_user.id, "user")
            status_data = db.get_status(message.from_user.id)
            
        (status_data, ) = status_data
        await state.update_data(status=status_data)
        return status_data

    return user_data["status"]

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    status = await get_status(state, message, first_start=True)
    if status != "admin":
        await message.answer(f'Здравствуйте! \U0001F600\nДанный бот создан для рассылки сообщений с полезной информацией от службы Мониторинга ЦА.')
        return
    await message.answer("Приветствую! \U0001F638")
    await message.answer(f"Если Вы видите это сообщение, значит Вы сотрудник службы Мониторинга ЦА! \U0001F600\nДля начала работы отправьте соответствующую команду или воспользуйтесь меню ниже.", reply_markup=get_main_keyboard())

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, end_point=False):
    await state.clear()
    await state.set_state(MainState.empty)
    if not end_point:
        await message.answer("Операция отменена успешно", reply_markup=get_main_keyboard())
    else:
        await message.answer("Операция завершена успешно", reply_markup=get_main_keyboard())

@router.message(F.text == "Отправь Кураторам")
async def button_send_to_curators(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(f'У Вас нет прав для доступа к данной команде.')
        return

    db = DataBase(db_name)
    lists = db.get_user_lists(user_id=message.from_user.id)
    if not lists:
        await handle_no_lists(message, state)
        return
    lists_str = ''
    lists_users_data = []
    for list_users in lists:
        list_users_str = list_users[2].split(',')
        users = db.get_users(list_users_str)
        lists_users_data.append(users)
        lists_str += f'\nСписок #{list_users[0]}:\n'
        lists_str += format_user_list(users)

    await message.answer(
        f'Вы можете выбрать один из существующих списков для рассылки, написав его порядковый номер, '
        f'или перейти в режим редактирования и создания списков, нажав на кнопку "Режим редактирования".\n\n'
        f'Существующие списки пользователей:\n'
        f'{lists_str}', reply_markup=get_keyboard(answer_yes="Режим редактирования", answer_no=""))
    await state.update_data(data_users_lists=lists_users_data)
    await state.set_state(MainState.empty_yes_no)

@router.message(F.text == "Режим редактирования")
async def button_edit_mode(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(f'У Вас нет прав для доступа к данной команде.')
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать новый список", callback_data="Создать новый список")],
        [InlineKeyboardButton(text="Редактировать существующий", callback_data="Отредактировать старый")],
        [InlineKeyboardButton(text="Удалить список", callback_data="Удалить список полностью")]
    ])
    await message.answer(f"Выберите действие:\n"
                        f"- Создать новый список\n"
                        f"- Редактировать существующий\n"
                        f"- Удалить список",
                        reply_markup=kb)
    await state.set_state(MainState.edit_mode_menu_yes_no)

@router.message(F.text == "Отменить все действия")
async def button_cancel(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(f'У Вас нет прав для доступа к данной команде.')
        return
    await cmd_cancel(message, state)

@router.message(F.text == "Управление администраторами")
async def button_admin_management(message: Message, state: FSMContext):
    """Обработчик кнопки управления администраторами"""
    # Просто вызываем функцию обработки команды add_admin
    await cmd_add_admin(message, state)

def format_user_list(users):
    """Форматирует список пользователей с красивым отображением"""
    lists_str = ''
    for i, user in enumerate(users, 1):
        username = user[2]
        if username and not username.startswith('@'):
            username = '@' + username
        lists_str += f"    {i}. {user[1]} {username}\n"
    return lists_str

def format_lists_of_users(lists):
    """Форматирует список списков пользователей с красивым отображением"""
    lists_str = ''
    for i, list_users in enumerate(lists, 1):
        lists_str += f"\nСписок #{i}:\n"
        lists_str += format_user_list(list_users)
    return lists_str

async def send_user_list_message(message, lists_str):
    await message.answer(
        f'Выберите один из существующих списков, написав его порядковый номер.\n\n'
        f'Существующие списки пользователей:\n'
        f'{lists_str}')

async def handle_no_lists(message, state):
    await message.answer(f'У вас нет созданных списков для рассылок.\n')
    await message.answer(f'Пожалуйста, отправьте мне список в следующем формате:\n'
                         f'Антон Чехов @anton_cheh\n'
                         f'Михаил Лермонтов @mishaL\n'
                         f'Рэйчел Грин @grin_rai\n'
                         f'и т.д.')
    await state.set_state(MainState.create_list_users)

@router.message(Command("ОтправьКураторам"))
@router.message(MainState.empty_yes_no)
async def start_sending(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(f'Вас нет в списке пользователей, имеющих доступ к данной команде')
        return

    current_state = await state.get_state()

    db = DataBase(db_name)

    if message.text == "/ОтправьКураторам":
        lists = db.get_user_lists(user_id=message.from_user.id)
        if not lists:
            await handle_no_lists(message, state)
            return
        lists_str = ''
        lists_users_data = []
        for list_users in lists:
            list_users_str = list_users[2].split(',')
            users = db.get_users(list_users_str)
            lists_users_data.append(users)
            lists_str += f'\nСписок #{list_users[0]}:\n'
            lists_str += format_user_list(users)

        await message.answer(
            f'Вы можете выбрать один из существующих списков для рассылки, написав порядковый номер списка, '
            f'или можете перейти в режим редактирования и создания списков, нажав на кнопку "Режим редактирования"\n\n'
            f'Существующие списки пользователей:\n'
            f'{lists_str}', reply_markup=get_keyboard(answer_yes="Режим редактирования", answer_no=""))
        await state.update_data(data_users_lists=lists_users_data)
        await state.set_state(MainState.empty_yes_no)
        return
    elif current_state == MainState.empty_yes_no:
        message_from_user = message.text.lower()
        if message_from_user.isdigit():
            data = await state.get_data()
            lists = data['data_users_lists']
            if int(message_from_user) > len(lists) or int(message_from_user) < 1:
                await message.answer(f"Вы ввели число, которое не соответствует не одному номеру из списка. Повторите ввод еще раз.")
                return
            await state.update_data(list_users_send=lists[int(message_from_user)-1])
            await message.answer(f"Отправьте мне текст сообщения для рассылки пожалуйста")
            await state.set_state(MainState.message)
            return
        elif message_from_user == 'режим редактирования':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Создать новый список", callback_data="Создать новый список")],
                [InlineKeyboardButton(text="Отредактировать старый", callback_data="Отредактировать старый")],
                [InlineKeyboardButton(text="Удалить список полностью", callback_data="Удалить список полностью")]
            ])
            await message.answer(f"Что вы хотите?\n"
                                 f"Создать новый список?\n"
                                 f"Отредактировать старый?\n"
                                 f"или\n"
                                 f"Удалить список полностью?",
                                 reply_markup=kb)
            await state.set_state(MainState.edit_mode_menu_yes_no)
            return
        else:
            await message.answer(f'К сожалению я вас совсем не понял, отправьте сообщение повторно')
            return

@router.callback_query(MainState.edit_mode_menu_yes_no)
@router.callback_query(MainState.edit_mode_user_yes_no)
async def edit_mode_menu(callback_query: CallbackQuery, state: FSMContext, message: Message = None):
    db = DataBase(db_name)
    current_state = await state.get_state()
    if current_state == MainState.edit_mode_menu_yes_no:
        message_from_user = callback_query.data.lower()
        if message_from_user == 'создать новый список':
            await callback_query.message.answer(f'Отправьте мне список в следующем формате:\n'
                                 f'Антон Чехов @anton_cheh\n'
                                 f'Михаил Лермонтов @mishaL\n'
                                 f'Рэйчел Грин @grin_rai\n'
                                 f'и т.д.')
            await state.set_state(MainState.create_list_users)
            return
        elif message_from_user == 'отредактировать старый':
            lists = db.get_user_lists(user_id=callback_query.from_user.id)
            if not lists:
                await handle_no_lists(callback_query.message, state)
                return
            lists_str = ''
            lists_users_data = []
            for list_users in lists:
                list_users_str = list_users[2].split(',')
                users = db.get_users(list_users_str)
                lists_users_data.append(users)
                lists_str += f'\nСписок #{list_users[0]}:\n'
                lists_str += format_user_list(users)
            await send_user_list_message(callback_query.message, lists_str)
            await state.update_data(data_users_lists=lists_users_data)
            await state.set_state(MainState.edit_mode_user_digit)
            return
        elif message_from_user == 'удалить список полностью':
            lists = db.get_user_lists(user_id=callback_query.from_user.id)
            if not lists:
                await handle_no_lists(callback_query.message, state)
                return
            lists_str = ''
            lists_users_data = []
            for list_users in lists:
                list_users_str = list_users[2].split(',')
                users = db.get_users(list_users_str)
                lists_users_data.append(users)
                lists_str += f'\nСписок #{list_users[0]}:\n'
                lists_str += format_user_list(users)
            await send_user_list_message(callback_query.message, lists_str)
            await state.update_data(data_users_lists=lists_users_data)
            await state.set_state(MainState.edit_mode_delete_list)
            return
    elif current_state == MainState.edit_mode_user_yes_no:
        message_from_user = callback_query.data.lower()
        if message_from_user == 'удалить':
            data = await state.get_data()
            users = data['list_users_send']
            users = users[1]
            lists_str = format_user_list(users)

            await callback_query.message.answer(
                f'Выберите пользователя, которого хотите удалить, введя его порядковый номер:\n'
                f'{lists_str}')
            await state.set_state(MainState.edit_mode_number_of_user_delete)
            return
        elif message_from_user == 'добавить':
            await callback_query.message.answer(f'Отправьте данные пользователя, которого Вы хотите добавить в список.'
                                                f'\nПример: Антон Чехов @anton_cheh')
            await state.set_state(MainState.edit_mode_add_user)
            return
        else:
            await callback_query.message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, повторите.')
            return

@router.message(Command("РежимРедактирования"))
@router.message(MainState.edit_mode_user_digit)
@router.message(MainState.edit_mode_number_of_user_delete)
@router.message(MainState.edit_mode_add_user)
@router.message(MainState.edit_mode_add_user_yes_no)
@router.message(MainState.edit_mode_delete_list)
@router.message(MainState.edit_mode_delete_list_yes_no)
async def edit_mode(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(f'Вас нет в списке пользователей, имеющих доступ к данной команде')
        return
    current_state = await state.get_state()
    db = DataBase(db_name)

    if message.text == "/РежимРедактирования":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать новый список", callback_data="Создать новый список")],
            [InlineKeyboardButton(text="Отредактировать старый", callback_data="Отредактировать старый")],
            [InlineKeyboardButton(text="Удалить список полностью", callback_data="Удалить список полностью")]
        ])
        await message.answer(f"Что вы хотите?\n"
                             f"Создать новый список?\n"
                             f"Отредактировать старый?\n"
                             f"или\n"
                             f"Удалить список полностью?",
                             reply_markup=kb)
        await state.set_state(MainState.edit_mode_menu_yes_no)
        return
    elif current_state == MainState.edit_mode_user_digit:
        message_from_user = message.text.lower()
        if message_from_user.isdigit():
            data = await state.get_data()
            lists = data['data_users_lists']
            if int(message_from_user) > len(lists) or int(message_from_user) < 1:
                await message.answer(
                    f"Вы ввели число, которое не соответствует ни одному номеру из списка. Пожалуйста, повторите ввод.")
                return
            await state.update_data(list_users_send=[int(message_from_user), lists[int(message_from_user) - 1]])
            await message.answer(f"Что Вы хотите сделать с данным списком?\n"
                                 f"- Удалить пользователя\n"
                                 f"- Добавить нового пользователя",
                                 reply_markup=get_keyboard(answer_yes="Удалить",
                                                           answer_no="Добавить", inline=True)
                                 )
            await state.set_state(MainState.edit_mode_user_yes_no)
            return
        else:
            await message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, введите номер списка.')
            return
    elif current_state == MainState.edit_mode_number_of_user_delete:
        id_admin = message.from_user.id
        message_from_user = message.text.lower()
        if message_from_user.isdigit():
            data = await state.get_data()
            users = data['list_users_send']
            if int(message_from_user) > len(users) or int(message_from_user) < 1:
                await message.answer(
                    f"Вы ввели число, которое не соответствует ни одному номеру из списка. Пожалуйста, повторите ввод.")
                return
            new_user_in_list = users[1][int(message_from_user) - 1]
            db.edit_note_user_lists(id_admin, new_user_in_list, users[0])
            await message.answer('Пользователь успешно удален. Список обновлен!', reply_markup=get_main_keyboard())
        else:
            await message.answer('Вы ввели не число. Пожалуйста, введите порядковый номер пользователя.')
            return
    elif current_state == MainState.edit_mode_add_user:
        message_from_user = message.text
        try:
            parts = message_from_user.split('@')
            if len(parts) < 2 or len(parts[0]) < 2:
                raise ValueError("Некорректный формат ввода")
            user_name = parts[0].strip()
            user_teg = parts[1].strip()
            
            # Добавляем @ к тегу пользователя
            if not user_teg.startswith('@'):
                user_teg = '@' + user_teg
            else:
                # Если @ уже был в исходной строке, он попал в parts[1]
                user_teg = '@' + user_teg
                
            user_str = f'{user_name} {user_teg}\n'
        except Exception as e:
            await message.reply("Некорректный формат ввода. Пожалуйста, проверьте и попробуйте снова.")
            return
        await message.answer(f'{user_str}\nВы хотите добавить данного пользователя?', reply_markup=get_keyboard())
        await state.update_data(new_useer=[user_name, user_teg])
        await state.set_state(MainState.edit_mode_add_user_yes_no)
        return
    elif current_state == MainState.edit_mode_add_user_yes_no:
        message_from_user = message.text.lower()
        if message_from_user == 'да':
            db = DataBase(db_name)
            data = await state.get_data()
            user = data['new_useer']
            list_users = data['list_users_send']
            id_admin = message.from_user.id
            try:
                # Убираем @ для поиска через API
                search_username = user[1]
                if search_username.startswith('@'):
                    search_username = search_username[1:]
                id_user = await get_users_id([search_username])
            except Exception as e:
                await message.answer(f'Имя пользователя указано некорректно или такой пользователь не существует.'
                                     f'\nПожалуйста, повторите ввод.', reply_markup=ReplyKeyboardRemove())
                await message.answer(f'Отправьте данные пользователя, которого Вы хотите добавить в список.'
                                     f'\nПример: Антон Чехов @anton_cheh', reply_markup=ReplyKeyboardRemove())
                await state.set_state(MainState.edit_mode_add_user)
                return

            if id_user[0] is None:
                await message.answer(f'Имя пользователя указано некорректно или такой пользователь не существует.'
                                     f'\nПожалуйста, повторите ввод.', reply_markup=ReplyKeyboardRemove())
                await message.answer(f'Отправьте данные пользователя, которого Вы хотите добавить в список.'
                                     f'\nПример: Антон Чехов @anton_cheh', reply_markup=ReplyKeyboardRemove())
                await state.set_state(MainState.edit_mode_add_user)
                return
            for userfromlist in list_users[1]:
                if id_user[0] == userfromlist[0]:
                    await message.answer('Данный пользователь уже есть в списке. '
                                   'Пожалуйста, введите данные другого пользователя.'
                                    f'\nПример: Антон Чехов @anton_cheh', reply_markup=ReplyKeyboardRemove() )
                    await state.set_state(MainState.edit_mode_add_user)
                    return
                    
            # Убеждаемся, что тег включает @
            save_username = user[1]
            if not save_username.startswith('@'):
                save_username = '@' + save_username
                
            db.insert_new_user(id_user[0], user[0], save_username)
            db.edit_note_user_lists(id_admin, id_user, list_users[0])
            await message.answer('Пользователь успешно добавлен! Список обновлен.', reply_markup=get_main_keyboard())
        elif message_from_user == 'нет':
            await message.answer(f'Отправьте данные пользователя, которого Вы хотите добавить в список.'
                                                f'\nПример: Антон Чехов @anton_cheh', reply_markup=ReplyKeyboardRemove())
            await state.set_state(MainState.edit_mode_add_user)
            return
        else:
            await message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, ответьте "Да" или "Нет".')
            return
    elif current_state == MainState.edit_mode_delete_list:
        message_from_user = message.text.lower()
        if message_from_user.isdigit():
            data = await state.get_data()
            lists = data['data_users_lists']
            if int(message_from_user) > len(lists) or int(message_from_user) < 1:
                await message.answer(
                    f"Вы ввели число, которое не соответствует ни одному номеру из списка. Пожалуйста, повторите ввод.")
                return
            users = [int(message_from_user), lists[int(message_from_user) - 1]]
            await state.update_data(list_users_send=users)
            lists_str = format_user_list(users[1])
            await message.answer(f'Вы уверены, что хотите удалить данный список пользователей?\n\n'
                               f"{lists_str}", 
                               reply_markup=get_keyboard())
            await state.set_state(MainState.edit_mode_delete_list_yes_no)
            return
    elif current_state == MainState.edit_mode_delete_list_yes_no:
        message_from_user = message.text.lower()
        if message_from_user == 'да':
            message_from_user = message.text.lower()
            db = DataBase(db_name)
            data = await state.get_data()
            current_list = data['list_users_send']
            id_admin = message.from_user.id
            db.delete_user_list(id_admin, current_list[0])
            await message.answer(f'Список пользователей №{current_list[0]} успешно удален!', reply_markup=get_main_keyboard())
        elif message_from_user == 'нет':
            lists = db.get_user_lists(user_id=message.from_user.id)
            lists_str = ''
            lists_users_data = []
            for list_users in lists:
                list_users_str = list_users[2].split(',')
                users = db.get_users(list_users_str)
                lists_users_data.append(users)
                lists_str += f'\nСписок #{list_users[0]}:\n'
                lists_str += format_user_list(users)
            await send_user_list_message(message, lists_str)
            await state.update_data(data_users_lists=lists_users_data)
            await state.set_state(MainState.edit_mode_delete_list)
            return
        else:
            await message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, ответьте "Да" или "Нет".')
            return

@router.message(MainState.create_list_users)
@router.message(MainState.create_list_users_yes_no)
@router.message(MainState.create_list_users_again)
async def create_list_users(message: Message, state: FSMContext):

    status = await get_status(state, message)

    if status != "admin":
        await message.answer(f'У Вас нет прав для доступа к данной команде.')
        return

    current_state = await state.get_state()
    if current_state == MainState.create_list_users:
        message_from_user = message.text
        try:
            message_rows = message_from_user.split('\n')
            users = []
            users_str = ''
            for message_row in message_rows:
                parts = message_row.split('@')
                if len(parts) < 2:
                    raise ValueError("Некорректный формат ввода")
                user_name = parts[0].strip()
                user_teg = parts[1].strip()
                # Добавляем @ к тегу, если его нет
                if not user_teg.startswith('@'):
                    user_teg = '@' + user_teg
                else:
                    # Если @ уже был в исходной строке, он попал в parts[1]
                    user_teg = '@' + user_teg
                users.append((user_name, user_teg))
                users_str += f'{user_name} {user_teg}\n'
        except Exception as e:
            await message.reply("Некорректный формат ввода. Пожалуйста, проверьте и попробуйте снова.")
            return

        await message.answer(f'{users_str}\nДанный список пользователей корректен?', reply_markup = get_keyboard() )
        await state.update_data(list_users=users)
        await state.set_state(MainState.create_list_users_yes_no)
        return
    elif current_state == MainState.create_list_users_yes_no:
        message_from_user = message.text.lower()

        if message_from_user == 'да':
            db = DataBase(db_name)
            data = await state.get_data()
            users_list = data['list_users']
            tegs = []
            for user in users_list:
                name, teg = user
                # Убираем @ для поиска пользователя в Telegram API
                if teg.startswith('@'):
                    teg = teg[1:]
                tegs.append(teg)
            try:
                ids = await get_users_id(tegs)
            except Exception as e:
                await message.answer(f'Один или несколько пользователей указаны некорректно или не существуют.'
                                     f'\nПожалуйста, проверьте и отправьте список снова.', reply_markup=ReplyKeyboardRemove())
                await message.answer(f'Отправьте мне список в следующем формате:\n'
                                     f'Антон Чехов @anton_cheh\n'
                                     f'Михаил Лермонтов @mishaL\n'
                                     f'Рэйчел Грин @grin_rai\n'
                                     f'и т.д.', reply_markup=ReplyKeyboardRemove())
                await state.set_state(MainState.create_list_users)
                return
            for index in range(len(users_list)):
                name, teg = users_list[index]
                user_id = ids[index]
                if user_id is None:
                    # Убеждаемся, что тег отображается с @
                    display_teg = teg
                    if not display_teg.startswith('@'):
                        display_teg = '@' + display_teg
                    await message.answer(f'Пользователь с именем {display_teg} не существует.'
                                         f'\nПожалуйста, проверьте и отправьте список снова.', reply_markup=ReplyKeyboardRemove())
                    await message.answer(f'Отправьте мне список в следующем формате:\n'
                                         f'Антон Чехов @anton_cheh\n'
                                         f'Михаил Лермонтов @mishaL\n'
                                         f'Рэйчел Грин @grin_rai\n'
                                         f'и т.д.', reply_markup=ReplyKeyboardRemove())

                    await state.set_state(MainState.create_list_users)
                    return

                # Обеспечиваем, что в базу данных сохраняется тег с @
                save_teg = teg
                if not save_teg.startswith('@'):
                    save_teg = '@' + save_teg
                
                if not db.get_users(user_id, colum="user_id"):
                    db.insert_new_user(user_id, name, save_teg)
            db.insert_new_note_user_lists(message.from_user.id, ",".join(map(str,ids)))
            await message.answer(f'Список пользователей успешно создан!', reply_markup=ReplyKeyboardRemove())
            await message.answer(f'Хотите создать еще один список пользователей для рассылки?', reply_markup=get_keyboard())
            await state.set_state(MainState.create_list_users_again)
            return
        elif message_from_user == 'нет':
            await message.answer(f'Отправьте мне список в следующем формате:\n'
                                 f'Антон Чехов @anton_cheh\n'
                                 f'Михаил Лермонтов @mishaL\n'
                                 f'Рэйчел Грин @grin_rai\n'
                                 f'и т.д.', reply_markup=ReplyKeyboardRemove())

            await state.set_state(MainState.create_list_users)
            return
        else:
            await message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, ответьте "Да" или "Нет".')
            return

    elif current_state == MainState.create_list_users_again:
        message_from_user = message.text.lower()
        if message_from_user == 'да':
            await message.answer(f'Отправьте мне список в следующем формате:\n'
                                 f'Антон Чехов @anton_cheh\n'
                                 f'Михаил Лермонтов @mishaL\n'
                                 f'Рэйчел Грин @grin_rai\n'
                                 f'и т.д.', reply_markup=ReplyKeyboardRemove())
            await state.set_state(MainState.create_list_users)
            return
        elif message_from_user == 'нет':
            await message.answer("Вы можете продолжить работу с ботом.", reply_markup=get_main_keyboard())
            await state.clear()
            return
        else:
            await message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, ответьте "Да" или "Нет".')
            return

@router.message(MainState.message_yes_no)
@router.message(MainState.message)
async def message_for_send(message: Message, state: FSMContext):
    status = await get_status(state, message)

    if status != "admin":
        await message.answer(f'У Вас нет прав для доступа к данной команде.')
        return

    current_state = await state.get_state()

    if current_state == MainState.message:
        message_from_user = message.text
        user_data = await state.get_data()
        list_users = user_data['list_users_send']
        list_users_str = format_user_list(list_users)

        await message.answer(f"Вы хотите отправить следующее сообщение:\n\n"
                           f"{message_from_user}\n\n"
                           f"Следующим пользователям:\n\n"
                           f"{list_users_str}\n"
                           f"Всё верно?", reply_markup=get_keyboard())

        await state.update_data(message_send=message_from_user)
        await state.set_state(MainState.message_yes_no)
        return
    elif current_state == MainState.message_yes_no:
        message_from_user = message.text.lower()
        if message_from_user == "да":
            user_data = await state.get_data()
            list_users = user_data['list_users_send']
            message_to_send = user_data['message_send']

            for user in list_users:
                chat_id = user[1]
                try:
                    await bot.send_message(chat_id=chat_id, text=message_to_send)
                except Exception as e:
                    error_message = f"Произошла ошибка при отправке сообщения: {e}"
                    try:
                        await message.answer(error_message)
                    except Exception:
                        print(f"Ошибка при отправке сообщения об ошибке пользователю {chat_id}: {e}")

            await message.answer("Сообщение успешно отправлено всем пользователям из списка.", reply_markup=get_main_keyboard())
            await cmd_cancel(message, state, True)
            return
        elif message_from_user == "нет":
            await message.answer(f"Пожалуйста, отправьте новый текст сообщения для рассылки.")
            await state.set_state(MainState.message)
            return
        else:
            await message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, ответьте "Да" или "Нет".')
            return

@router.message(Command("add_admin"))
async def cmd_add_admin(message: Message, state: FSMContext):
    """Обработчик команды для добавления/удаления администраторов"""
    status = await get_status(state, message)
    if status != "admin":
        await message.answer("У Вас нет прав для управления администраторами.")
        return
    
    await message.answer("Выберите действие:", 
                        reply_markup=get_keyboard(
                            answer_yes="Добавить администратора", 
                            answer_no="Удалить администратора"))
    await state.set_state(MainState.admin_management)

@router.message(MainState.admin_management)
async def process_admin_action(message: Message, state: FSMContext):
    """Обработка выбора действия с администраторами"""
    action = message.text.lower()
    
    if action not in ["добавить администратора", "удалить администратора"]:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")
        return
    
    await state.update_data(admin_action=action)
    
    if action == "добавить администратора":
        await message.answer("Введите @username пользователя, которого нужно сделать администратором:", 
                           reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Введите @username пользователя, у которого нужно удалить права администратора:", 
                           reply_markup=ReplyKeyboardRemove())
    
    await state.set_state(MainState.admin_username_input)

@router.message(MainState.admin_username_input)
async def process_admin_username(message: Message, state: FSMContext):
    """Обработка ввода имени пользователя"""
    username = message.text.strip()
    
    # Если пользователь не ввел @ в начале
    if not username.startswith('@'):
        username = '@' + username
    
    # Сохраняем имя пользователя
    await state.update_data(admin_username=username)
    
    # Получаем информацию о выбранном действии
    user_data = await state.get_data()
    action = user_data.get('admin_action')
    
    # Получаем ID пользователя по username (без @)
    try:
        search_username = username[1:] if username.startswith('@') else username
        user_ids = await get_users_id([search_username])  # Удаляем @ для поиска
        user_id = user_ids[0]
        
        if user_id is None:
            await message.answer(f"Пользователь {username} не найден. Проверьте правильность ввода и попробуйте снова.")
            return
        
        await state.update_data(admin_id=user_id)
        
        db = DataBase(db_name)
        current_status = db.get_status(user_id)
        
        if action == "добавить администратора":
            if current_status and current_status[0] == "admin":
                await message.answer(f"Пользователь {username} уже является администратором.")
                await state.set_state(MainState.empty)
                await message.answer("Управление администраторами завершено.", reply_markup=get_main_keyboard())
                return
                
            await message.answer(f"Вы хотите назначить пользователя {username} администратором?", 
                               reply_markup=get_keyboard())
        else:
            if not current_status or current_status[0] != "admin":
                await message.answer(f"Пользователь {username} не является администратором.")
                await state.set_state(MainState.empty)
                await message.answer("Управление администраторами завершено.", reply_markup=get_main_keyboard())
                return
                
            await message.answer(f"Вы действительно хотите удалить права администратора у пользователя {username}?", 
                               reply_markup=get_keyboard())
        
        await state.set_state(MainState.admin_confirmation)
        
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}. Пожалуйста, попробуйте позже.")
        await state.set_state(MainState.empty)
        await message.answer("Операция отменена.", reply_markup=get_main_keyboard())

@router.message(MainState.admin_confirmation)
async def confirm_admin_action(message: Message, state: FSMContext):
    """Подтверждение действия с администратором"""
    confirmation = message.text.lower()
    
    if confirmation not in ["да", "нет"]:
        await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'.")
        return
    
    if confirmation == "нет":
        await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
        await state.set_state(MainState.empty)
        return
    
    # Получаем сохраненные данные
    user_data = await state.get_data()
    action = user_data.get('admin_action')
    user_id = user_data.get('admin_id')
    username = user_data.get('admin_username')
    
    db = DataBase(db_name)
    
    if action == "добавить администратора":
        # Используем update_status вместо insert_new_note_status для обновления статуса
        db.update_status(user_id, "admin")
        await message.answer(f"Пользователь {username} успешно назначен администратором.", 
                           reply_markup=get_main_keyboard())
    else:
        # Используем update_status для изменения статуса на "user"
        db.update_status(user_id, "user")
        await message.answer(f"Права администратора у пользователя {username} успешно удалены.", 
                           reply_markup=get_main_keyboard())
    
    await state.set_state(MainState.empty)
