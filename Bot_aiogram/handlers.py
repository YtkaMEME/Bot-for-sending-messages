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

MESSAGES = {
    'NO_RIGHTS': 'У Вас нет прав для доступа к данной команде.',
    'ENTER_LIST_FORMAT': ('Отправьте мне список в следующем формате:\n'
                         'Антон Чехов @anton_cheh\n'
                         'Михаил Лермонтов @mishaL\n'
                         'Рэйчел Грин @grin_rai\n'
                         'и т.д.'),
    'INVALID_NUMBER': 'Вы ввели число, которое не соответствует ни одному номеру из списка. Пожалуйста, повторите ввод.',
    'INVALID_FORMAT': 'Некорректный формат ввода. Пожалуйста, проверьте и попробуйте снова.',
    'YES_NO_REQUEST': 'К сожалению, я не понял Ваш запрос. Пожалуйста, ответьте "Да" или "Нет".',
    'ENTER_USER_DATA': 'Отправьте данные пользователя, которого Вы хотите добавить в список.\nПример: Антон Чехов @anton_cheh',
    'USER_EXISTS': 'Данный пользователь уже есть в списке. Пожалуйста, введите данные другого пользователя.',
    'CONTINUE_WORK': 'Вы можете продолжить работу с ботом.',
    'OPERATION_CANCELLED': 'Операция отменена успешно',
    'OPERATION_COMPLETED': 'Операция завершена успешно',
}

router = Router()
db_name = DB_PATH
bot = help_file.bot
class MainState(StatesGroup):
    delete_user_username = State()
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
    edit_mode_continue = State()

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Словарь для соответствия текущих состояний и предыдущих
STATE_TRANSITIONS = {
    # Главное меню
    MainState.empty_yes_no: MainState.empty,  # После выбора "Отправь Кураторам" -> Главное меню
    MainState.edit_mode_menu_yes_no: MainState.empty,  # После выбора "Режим редактирования" -> Главное меню
    MainState.admin_management: MainState.empty,  # После выбора "Управление администраторами" -> Главное меню
    
    # Создание списка пользователей
    MainState.create_list_users_yes_no: MainState.create_list_users,  # После ввода списка -> К вводу списка
    MainState.create_list_users_again: MainState.empty,  # После создания списка -> Главное меню
    
    # Редактирование списков
    MainState.edit_mode_user_digit: MainState.edit_mode_menu_yes_no,  # Выбор списка -> Меню редактирования
    MainState.edit_mode_user_yes_no: MainState.edit_mode_user_digit,  # Выбор действия -> Выбор списка
    MainState.edit_mode_number_of_user_delete: MainState.edit_mode_user_yes_no,  # Выбор пользователя -> Выбор действия
    MainState.edit_mode_add_user: MainState.edit_mode_user_yes_no,  # Ввод данных пользователя -> Выбор действия
    MainState.edit_mode_add_user_yes_no: MainState.edit_mode_add_user,  # Подтверждение -> Ввод данных пользователя
    MainState.edit_mode_delete_list: MainState.edit_mode_menu_yes_no,  # Выбор списка -> Меню редактирования
    MainState.edit_mode_delete_list_yes_no: MainState.edit_mode_delete_list,  # Подтверждение -> Выбор списка
    MainState.edit_mode_continue: MainState.edit_mode_user_yes_no,  # Продолжение редактирования -> Выбор действия
    
    # Отправка сообщений
    MainState.message: MainState.empty_yes_no,  # Ввод сообщения -> Выбор списка
    MainState.message_yes_no: MainState.message,  # Подтверждение -> Ввод сообщения
    
    # Управление администраторами
    MainState.admin_username_input: MainState.admin_management,  # Ввод имени -> Выбор действия
    MainState.admin_confirmation: MainState.admin_username_input,  # Подтверждение -> Ввод имени
}

def get_keyboard(message="Выберите вариант ответа", answer_yes="Да", answer_no="Нет", answer_3=None, inline=False, add_back=True):
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

    # Добавляем кнопку "Назад", если это не основная клавиатура
    if add_back and answer_yes != "Отправь Кураторам":
        if inline:
            kb.append([InlineKeyboardButton(text="Назад", callback_data="back_button")])
        else:
            kb.append([KeyboardButton(text="Назад")])

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
            [KeyboardButton(text="Получить список пользователей")],
            [KeyboardButton(text="Отменить все действия")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
    return keyboard

async def go_back(message: Message, state: FSMContext):
    """Функция для перехода на предыдущий шаг"""
    current_state = await state.get_state()
    
    # Получаем предыдущее состояние
    prev_state = STATE_TRANSITIONS.get(current_state)
    
    if not prev_state:
        # Если предыдущее состояние не определено, возвращаемся в главное меню
        await cmd_cancel(message, state)
        return
    
    # Сохраняем текущие данные
    data = await state.get_data()
    
    # Очищаем состояние и устанавливаем предыдущее
    await state.clear()
    await state.set_state(prev_state)
    
    # Восстанавливаем данные
    await state.update_data(**data)
    
    # Выводим соответствующие сообщения в зависимости от состояния
    if prev_state == MainState.empty:
        await message.answer("Возвращаемся в главное меню", reply_markup=get_main_keyboard())
    elif prev_state == MainState.edit_mode_menu_yes_no:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать новый список", callback_data="Создать новый список")],
            [InlineKeyboardButton(text="Редактировать существующий", callback_data="Отредактировать старый")],
            [InlineKeyboardButton(text="Удалить список полностью", callback_data="Удалить список полностью")],
            [InlineKeyboardButton(text="Назад", callback_data="back_button")]
        ])
        await message.answer("Возвращаемся к выбору действия в режиме редактирования", reply_markup=kb)
    elif prev_state == MainState.create_list_users:
        await message.answer(MESSAGES['ENTER_LIST_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
        await state.set_state(MainState.create_list_users)
    elif prev_state == MainState.empty_yes_no:
        db = DataBase(db_name)
        lists = db.get_user_lists(user_id=message.from_user.id)
        lists_str = ''
        lists_users_data = []
        for list_users in lists:
            list_users_str = list_users[2].split(',')
            users = db.get_users(list_users_str)
            lists_users_data.append(users)
            lists_str += f'\nСписок #{list_users[0]}:\n'
            lists_str += format_user_list(users)
        await message.answer(
            f'Возвращаемся к выбору списка. Выберите один из существующих списков для рассылки, *введя его номер*:\n\n'
            f'{lists_str}', reply_markup=get_keyboard(answer_yes="Режим редактирования", answer_no="", add_back=True))
        await state.update_data(data_users_lists=lists_users_data)
    else:
        await message.answer("Возвращаемся на предыдущий шаг", reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))

async def get_status(state, message, first_start=False, user_id=None):
    if not user_id:
        user_id = message.from_user.id

    user_data = await state.get_data()
    if "status" not in user_data or first_start:
        db = DataBase(db_name)
        status_data = db.get_status(user_id)
        
        # Если первый старт и пользователь не существует, создаем его
        if status_data is None:

            db.update_status(user_id, "user")
            status_data = db.get_status(user_id)
            
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
        await message.answer(MESSAGES['OPERATION_CANCELLED'], reply_markup=get_main_keyboard())
    else:
        await message.answer(MESSAGES['OPERATION_COMPLETED'], reply_markup=get_main_keyboard())

# Обработчик для кнопки "Назад"
@router.message(F.text == "Назад")
async def back_button_handler(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return
    
    await go_back(message, state)

@router.callback_query(F.data == "back_button")
async def process_back_button_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await go_back(callback_query.message, state)

def create_lists_mapping(lists):
    """Создает словарь для сопоставления порядковых номеров и ID списков"""
    return {i: list_item[0] for i, list_item in enumerate(lists, 1)}

async def send_user_list_message(message, lists_str, lists_mapping=None):
    await message.answer(
        f'Выберите один из существующих списков, <b>написав его номер</b>.\n\n'
        f'Существующие списки пользователей:\n'
        f'{lists_str}', reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True), parse_mode='html')

@router.message(F.text == "Получить список пользователей")
async def button_get_user_list(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return

    db = DataBase(db_name)
    users_list = db.get_active_users()
    if not users_list.empty:
        output = "Список пользователей:\n\n"
        for i, user in enumerate(users_list.to_dict('records'), 1):
            output += f"{i}. {user['username']} {user['full_name']}\n"
        await message.answer(output, parse_mode='HTML')
    else:
        await message.answer("Список пользователей пуст.")
    return

@router.message(F.text == "Отправь Кураторам")
async def button_send_to_curators(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return

    db = DataBase(db_name)
    lists = db.get_user_lists(user_id=message.from_user.id)
    if not lists:
        await handle_no_lists(message, state)
        return
    lists_str = ''
    lists_users_data = []
    lists_mapping = create_lists_mapping(lists)
    
    for i, list_users in enumerate(lists, 1):
        list_users_str = list_users[2].split(',')
        users = db.get_users(list_users_str)
        lists_users_data.append(users)
        lists_str += f'\nСписок #{i}:\n'
        lists_str += format_user_list(users)

    await message.answer(
        f'Вы можете выбрать один из существующих списков для рассылки, <b>написав его номер</b>, '
        f'или перейти в режим редактирования и создания списков, нажав на кнопку "Режим редактирования".\n\n'
        f'Существующие списки пользователей:\n'
        f'{lists_str}', reply_markup=get_keyboard(answer_yes="Режим редактирования", answer_no="", add_back=True), parse_mode='html')
    await state.update_data(data_users_lists=lists_users_data, lists_mapping=lists_mapping)
    await state.set_state(MainState.empty_yes_no)

@router.message(F.text == "Режим редактирования")
async def button_edit_mode(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать новый список", callback_data="Создать новый список")],
        [InlineKeyboardButton(text="Редактировать существующий", callback_data="Отредактировать старый")],
        [InlineKeyboardButton(text="Удалить список полностью", callback_data="Удалить список полностью")],
        [InlineKeyboardButton(text="Назад", callback_data="back_button")]
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
        await message.answer(MESSAGES['NO_RIGHTS'])
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
    # Проверяем, является ли входной параметр списком с ID списка
    if isinstance(users, list) and len(users) == 2 and isinstance(users[0], int):
        users = users[1]  # Берем только список пользователей
    
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

async def handle_no_lists(message, state):
    await message.answer(f'У вас нет созданных списков для рассылок.\n')
    await message.answer(MESSAGES['ENTER_LIST_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
    await state.set_state(MainState.create_list_users)

@router.message(Command("ОтправьКураторам"))
@router.message(MainState.empty_yes_no)
async def start_sending(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
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
        lists_mapping = create_lists_mapping(lists)
        
        for i, list_users in enumerate(lists, 1):
            list_users_str = list_users[2].split(',')
            users = db.get_users(list_users_str)
            lists_users_data.append(users)
            lists_str += f'\nСписок #{i}:\n'
            lists_str += format_user_list(users)

        await message.answer(
            f'Вы можете выбрать один из существующих списков для рассылки, *написав его номер*, '
            f'или можете перейти в режим редактирования и создания списков, нажав на кнопку "Режим редактирования"\n\n'
            f'Существующие списки пользователей:\n'
            f'{lists_str}', reply_markup=get_keyboard(answer_yes="Режим редактирования", answer_no="", add_back=True))
        await state.update_data(data_users_lists=lists_users_data, lists_mapping=lists_mapping)
        await state.set_state(MainState.empty_yes_no)
        return
    elif current_state == MainState.empty_yes_no:
        message_from_user = message.text.lower()
        if message_from_user.isdigit():
            data = await state.get_data()
            lists = data['data_users_lists']
            lists_mapping = data['lists_mapping']
            selected_number = int(message_from_user)
            
            if selected_number > len(lists) or selected_number < 1:
                await message.answer(MESSAGES['INVALID_NUMBER'], 
                                    reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
                return
                
            # Получаем ID списка из словаря сопоставления
            selected_list_id = lists_mapping[selected_number]
            await state.update_data(list_users_send=[selected_list_id, lists[selected_number - 1]])
            await message.answer(f"Отправьте мне текст сообщения для рассылки пожалуйста", 
                               reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await state.set_state(MainState.message)
            return
        elif message_from_user == 'режим редактирования':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Создать новый список", callback_data="Создать новый список")],
                [InlineKeyboardButton(text="Отредактировать старый", callback_data="Отредактировать старый")],
                [InlineKeyboardButton(text="Удалить список полностью", callback_data="Удалить список полностью")],
                [InlineKeyboardButton(text="Назад", callback_data="back_button")]
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
            await message.answer(MESSAGES['YES_NO_REQUEST'], 
                               reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            return

@router.callback_query(MainState.edit_mode_menu_yes_no)
@router.callback_query(MainState.edit_mode_user_yes_no)
async def edit_mode_menu(callback_query: CallbackQuery, state: FSMContext, message: Message = None):
    db = DataBase(db_name)
    current_state = await state.get_state()
    if current_state == MainState.edit_mode_menu_yes_no:
        message_from_user = callback_query.data.lower()
        if message_from_user == 'создать новый список':
            await callback_query.message.answer(MESSAGES['ENTER_LIST_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await state.set_state(MainState.create_list_users)
            return
        elif message_from_user == 'отредактировать старый':
            lists = db.get_user_lists(user_id=callback_query.from_user.id)
            if not lists:
                await handle_no_lists(callback_query.message, state)
                return
            lists_str = ''
            lists_users_data = []
            lists_mapping = create_lists_mapping(lists)
            
            for i, list_users in enumerate(lists, 1):
                list_users_str = list_users[2].split(',')
                users = db.get_users(list_users_str)
                lists_users_data.append(users)
                lists_str += f'\nСписок #{i}:\n'
                lists_str += format_user_list(users)
            await send_user_list_message(callback_query.message, lists_str)
            await state.update_data(data_users_lists=lists_users_data, lists_mapping=lists_mapping)
            await state.set_state(MainState.edit_mode_user_digit)
            return
        elif message_from_user == 'удалить список полностью':
            lists = db.get_user_lists(user_id=callback_query.from_user.id)
            if not lists:
                await handle_no_lists(callback_query.message, state)
                return
            lists_str = ''
            lists_users_data = []
            lists_mapping = create_lists_mapping(lists)
            
            for i, list_users in enumerate(lists, 1):
                list_users_str = list_users[2].split(',')
                users = db.get_users(list_users_str)
                lists_users_data.append(users)
                lists_str += f'\nСписок #{i}:\n'
                lists_str += format_user_list(users)
            await send_user_list_message(callback_query.message, lists_str)
            await state.update_data(data_users_lists=lists_users_data, lists_mapping=lists_mapping)
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
                f'Выберите пользователя, которого хотите удалить, <b>введя его номер</b>:\n'
                f'{lists_str}', reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True), parse_mode='html')
            await state.set_state(MainState.edit_mode_number_of_user_delete)
            return
        elif message_from_user == 'добавить':
            await callback_query.message.answer(MESSAGES['ENTER_USER_DATA'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await state.set_state(MainState.edit_mode_add_user)
            return
        else:
            await callback_query.message.answer(MESSAGES['YES_NO_REQUEST'], reply_markup=get_keyboard(add_back=True))
            return

@router.message(Command("РежимРедактирования"))
@router.message(MainState.edit_mode_user_digit)
@router.message(MainState.edit_mode_number_of_user_delete)
@router.message(MainState.edit_mode_add_user)
@router.message(MainState.edit_mode_delete_list)
@router.message(MainState.edit_mode_delete_list_yes_no)
async def edit_mode(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return
        
    if message.text == "Назад":
        await go_back(message, state)
        return
        
    current_state = await state.get_state()
    db = DataBase(db_name)

    if message.text == "/РежимРедактирования":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать новый список", callback_data="Создать новый список")],
            [InlineKeyboardButton(text="Редактировать существующий", callback_data="Отредактировать старый")],
            [InlineKeyboardButton(text="Удалить список полностью", callback_data="Удалить список полностью")],
            [InlineKeyboardButton(text="Назад", callback_data="back_button")]
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
            lists_mapping = data['lists_mapping']
            selected_number = int(message_from_user)
            
            if selected_number > len(lists) or selected_number < 1:
                await message.answer(MESSAGES['INVALID_NUMBER'], 
                    reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
                return
                
            # Получаем ID списка из словаря сопоставления
            selected_list_id = lists_mapping[selected_number]
            await state.update_data(list_users_send=[selected_list_id, lists[selected_number - 1]])
            await message.answer(f"Что Вы хотите сделать с данным списком?\n"
                                 f"- Удалить пользователя\n"
                                 f"- Добавить нового пользователя",
                                 reply_markup=get_keyboard(answer_yes="Удалить",
                                                       answer_no="Добавить", inline=True))
            await state.set_state(MainState.edit_mode_user_yes_no)
            return
        else:
            await message.answer(MESSAGES['INVALID_FORMAT'], 
                              reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            return
    elif current_state == MainState.edit_mode_delete_list:
        message_from_user = message.text.lower()
        if message_from_user.isdigit():
            data = await state.get_data()
            lists = data['data_users_lists']
            lists_mapping = data['lists_mapping']
            selected_number = int(message_from_user)
            
            if selected_number > len(lists) or selected_number < 1:
                await message.answer(MESSAGES['INVALID_NUMBER'], 
                    reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
                return
                
            # Получаем ID списка из словаря сопоставления
            selected_list_id = lists_mapping[selected_number]
            users = [selected_list_id, lists[selected_number - 1]]
            await state.update_data(list_users_send=users)
            lists_str = format_user_list(users[1])
            await message.answer(f'Вы уверены, что хотите удалить данный список пользователей?\n\n'
                               f"{lists_str}", 
                               reply_markup=get_keyboard())
            await state.set_state(MainState.edit_mode_delete_list_yes_no)
            return
        else:
            await message.answer(f'К сожалению, я не понял Ваш запрос. Пожалуйста, <b>введите номер списка</b>.', 
                              reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True), parse_mode='html')
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
            await message.answer(MESSAGES['YES_NO_REQUEST'], 
                              reply_markup=get_keyboard(add_back=True))
            return
    elif current_state == MainState.edit_mode_add_user:
        await message.answer(f"Вы хотите добавить в список данного пользователя?\n"
                             f"{message.text}\n"
                             f"Для подтверждения нажмите на кнопку 'Да', для отмены - на кнопку 'Нет'", reply_markup=get_keyboard(answer_yes="Да", answer_no="Нет"))
        await state.set_state(MainState.edit_mode_add_user_yes_no)
        await state.update_data(new_useer=message.text.split('@'))
        return
    elif current_state == MainState.edit_mode_number_of_user_delete:
        message_from_user = message.text.lower()
        id_admin = message.from_user.id
        db = DataBase(db_name)
        if message_from_user.isdigit():
            data = await state.get_data()
            users = data['list_users_send'][1]
            id_list = data['list_users_send'][0]
            selected_number = int(message_from_user)
            
            if selected_number > len(users) or selected_number < 1:
                await message.answer(MESSAGES['INVALID_NUMBER'], 
                    reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
                return
                
            user = users[selected_number - 1]
            # Добавляем пользователя в список
            db.edit_note_user_lists(id_admin, user, id_list, delete_user=True)
            
            # Получаем обновленный список пользователей
            lists = db.get_user_lists(user_id=id_admin)
            updated_list = None
            for list_item in lists:
                if list_item[0] == id_list:
                    list_users_str = list_item[2].split(',')
                    updated_list = db.get_users(list_users_str)
                    break
                    
            # Выводим обновленный список
            if updated_list:
                lists_str = format_user_list(updated_list)
                await message.answer(f'Пользователь успешно удален! Обновленный список №{id_list}:\n\n{lists_str}')
                
            # Спрашиваем о продолжении редактирования
            await message.answer('Хотите продолжить редактирование этого списка?', reply_markup=get_keyboard())
            
            # Сохраняем обновленный список в состоянии
            if updated_list:
                await state.update_data(list_users_send=[id_list, updated_list])
                
            # Устанавливаем состояние для продолжения редактирования
            await state.set_state(MainState.edit_mode_continue)
            return
        else:
            await message.answer(MESSAGES['INVALID_FORMAT'], 
                              reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            return

@router.message(MainState.create_list_users)
@router.message(MainState.create_list_users_yes_no)
@router.message(MainState.create_list_users_again)
async def create_list_users(message: Message, state: FSMContext):

    status = await get_status(state, message)

    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return

    current_state = await state.get_state()
    
    if message.text == "Назад":
        await go_back(message, state)
        return
        
    if current_state == MainState.create_list_users:
        message_from_user = message.text
        try:
            message_rows = message_from_user.split('\n')
            users = []
            users_str = ''
            for message_row in message_rows:
                parts = message_row.split('@')
                if len(parts) < 2:
                    raise ValueError(MESSAGES['INVALID_FORMAT'])
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
            await message.reply(MESSAGES['INVALID_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            return

        await message.answer(f'{users_str}\nДанный список пользователей корректен?', reply_markup=get_keyboard(add_back=True))
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
                                     f'\nПожалуйста, проверьте и отправьте список снова.', reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
                await message.answer(MESSAGES['ENTER_LIST_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
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
                                         f'\nПожалуйста, проверьте и отправьте список снова.', reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
                    await message.answer(MESSAGES['ENTER_LIST_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))

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
            await message.answer(MESSAGES['ENTER_LIST_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))

            await state.set_state(MainState.create_list_users)
            return
        else:
            await message.answer(MESSAGES['YES_NO_REQUEST'], reply_markup=get_keyboard())
            return

    elif current_state == MainState.create_list_users_again:
        message_from_user = message.text.lower()
        if message_from_user == 'да':
            await message.answer(MESSAGES['ENTER_LIST_FORMAT'], reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await state.set_state(MainState.create_list_users)
            return
        elif message_from_user == 'нет':
            await message.answer(MESSAGES['CONTINUE_WORK'], reply_markup=get_main_keyboard())
            await state.clear()
            return
        else:
            await message.answer(MESSAGES['YES_NO_REQUEST'], reply_markup=get_keyboard())
            return

@router.message(MainState.message)
async def message_for_send(message: Message, state: FSMContext):
    status = await get_status(state, message)

    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return
        
    if message.text == "Назад":
        await go_back(message, state)
        return

    current_state = await state.get_state()

    if current_state == MainState.message:
        message_from_user = message.text
        user_data = await state.get_data()
        list_users = user_data['list_users_send']
        list_users_str = format_user_list(list_users)

        # Отправляем сообщение с сохранением форматирования
        await message.answer(
            "Вы хотите отправить следующее сообщение:\n\n",
            parse_mode=None
        )
        
        # Отправляем само сообщение с форматированием
        if message.entities:
            await message.answer(
                message_from_user,
                entities=message.entities,
                parse_mode=None
            )
        else:
            await message.answer(
                message_from_user,
                parse_mode='HTML'
            )
            
        # Отправляем список получателей
        await message.answer(
            f"\nСледующим пользователям:\n\n"
            f"{list_users_str}\n"
            f"Всё верно?",
            reply_markup=get_keyboard()
        )

        await state.update_data(
            message_send=message_from_user,
            original_message=message  # Сохраняем оригинальное сообщение с форматированием
        )
        await state.set_state(MainState.message_yes_no)
        return

@router.message(MainState.message_yes_no)
async def message_yes_no_handler(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return

    if message.text == "Назад":
        await go_back(message, state)
        return

    message_from_user = message.text.lower()
    if message_from_user == "да":
        user_data = await state.get_data()
        list_users = user_data['list_users_send']
        message_to_send = user_data['message_send']
        original_message = user_data.get('original_message')

        # Получаем список пользователей с проверкой
        db = DataBase(db_name)
        users = db.get_users_for_sending(list_users[0], message.from_user.id)
        
        if users is None:
            await message.answer("Ошибка: список не найден или у вас нет прав доступа.")
            return
            
        if not users:
            await message.answer("Список пользователей пуст.")
            return

        # Отправляем сообщение каждому пользователю
        for user in users:
            chat_id = user[0]
            user_name = user[1]
            try:
                if original_message and original_message.entities:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message_to_send,
                        entities=original_message.entities,
                        parse_mode=None
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message_to_send,
                        parse_mode='HTML'
                    )
            except Exception as e:
                error_message = f"Ошибка при отправке сообщения пользователю {user_name}: {e}"
                try:
                    await message.answer(error_message)
                except Exception:
                    print(error_message)

        await message.answer(MESSAGES['OPERATION_COMPLETED'], reply_markup=get_main_keyboard())
        await cmd_cancel(message, state, True)
        return

    elif message_from_user == "нет":
        await message.answer(f"Пожалуйста, отправьте новый текст сообщения для рассылки.", 
                           reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
        await state.set_state(MainState.message)
        return

    else:
        await message.answer(MESSAGES['YES_NO_REQUEST'], reply_markup=get_keyboard())
        return

@router.message(Command("add_admin"))
async def cmd_add_admin(message: Message, state: FSMContext):
    """Обработчик команды для добавления/удаления администраторов"""
    status = await get_status(state, message)
    if status != "admin":
        await message.answer("У Вас нет прав для управления администраторами.")
        return
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить администратора")],
            [KeyboardButton(text="Удалить администратора")],
            [KeyboardButton(text="Список администраторов")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
    await message.answer("Выберите действие:", 
                        reply_markup=keyboard)
    await state.set_state(MainState.admin_management)

@router.message(MainState.admin_management)
async def process_admin_action(message: Message, state: FSMContext):
    """Обработка выбора действия с администраторами"""
    action = message.text.lower()
    
    if action == "назад":
        await go_back(message, state)
        return
    
    if action not in ["добавить администратора", "удалить администратора", "список администраторов"]:
        await message.answer("Пожалуйста, <b>выберите один из предложенных вариантов</b>.", 
                            reply_markup=get_keyboard(answer_yes="Добавить администратора", 
                            answer_no="Удалить администратора", add_back=True), parse_mode='html')
        return
    
    await state.update_data(admin_action=action)
    
    if action == "добавить администратора":
        await message.answer("Введите @username пользователя, которого нужно сделать администратором:", 
                           reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
    elif action == "список администраторов":
        db = DataBase(db_name)
        admins = db.get_active_users(status_info="admin")
        if not admins.empty:
            output = "Список администраторов:\n\n"
            for i, admin in enumerate(admins.to_dict('records'), 1):
                output += f"{i}. {admin['username']} {admin['full_name']}\n"
            await message.answer(output, parse_mode='HTML')
        else:
            await message.answer("Список администраторов пуст.")
    else:
        await message.answer("Введите @username пользователя, у которого нужно удалить права администратора:", 
                           reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
    
    await state.set_state(MainState.admin_username_input)

@router.message(MainState.admin_username_input)
async def process_admin_username(message: Message, state: FSMContext):
    """Обработка ввода имени пользователя"""
    if message.text == "Назад":
        await go_back(message, state)
        return
        
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
            await message.answer(f"Пользователь {username} не найден. Проверьте правильность ввода и попробуйте снова.", 
                               reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
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
        await message.answer(f"Произошла ошибка: {e}. Пожалуйста, попробуйте позже.", 
                           reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
        await state.set_state(MainState.empty)
        await message.answer("Операция отменена.", reply_markup=get_main_keyboard())

@router.message(MainState.admin_confirmation)
async def confirm_admin_action(message: Message, state: FSMContext):
    """Подтверждение действия с администратором"""
    if message.text == "Назад":
        await go_back(message, state)
        return
        
    confirmation = message.text.lower()
    
    if confirmation not in ["да", "нет"]:
        await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'.", reply_markup=get_keyboard(add_back=True))
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

@router.message(MainState.edit_mode_add_user_yes_no)
async def edit_mode_add_user_yes_no_handler(message: Message, state: FSMContext):
    status = await get_status(state, message)

    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return
        
    if message.text == "Назад":
        await go_back(message, state)
        return
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
                                f'\nПожалуйста, повторите ввод.', 
                                reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await message.answer(MESSAGES['ENTER_USER_DATA'], 
                                reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await state.set_state(MainState.edit_mode_add_user)
            return

        if id_user[0] is None:
            await message.answer(f'Имя пользователя указано некорректно или такой пользователь не существует.'
                                f'\nПожалуйста, повторите ввод.', 
                                reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await message.answer(MESSAGES['ENTER_USER_DATA'], 
                                reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
            await state.set_state(MainState.edit_mode_add_user)
            return
        for userfromlist in list_users[1]:
            if id_user[0] == userfromlist[0]:
                await message.answer(MESSAGES['USER_EXISTS'], 
                               reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
                await state.set_state(MainState.edit_mode_add_user)
                return
                
        # Убеждаемся, что тег включает @
        save_username = user[1]
        if not save_username.startswith('@'):
            save_username = '@' + save_username
            
        # Добавляем пользователя в БД, если его еще нет
        if not db.get_users(id_user[0], colum="user_id"):
            db.insert_new_user(id_user[0], user[0], save_username)
            
        # Добавляем пользователя в список
        db.edit_note_user_lists(id_admin, id_user, list_users[0], delete_user=False)
        
        # Получаем обновленный список пользователей
        lists = db.get_user_lists(user_id=id_admin)
        updated_list = None
        for list_item in lists:
            if list_item[0] == list_users[0]:
                list_users_str = list_item[2].split(',')
                updated_list = db.get_users(list_users_str)
                break
                
        # Выводим обновленный список
        if updated_list:
            lists_str = format_user_list(updated_list)
            await message.answer(f'Пользователь успешно добавлен! Обновленный список №{list_users[0]}:\n\n{lists_str}')
            
        # Спрашиваем о продолжении редактирования
        await message.answer('Хотите продолжить редактирование этого списка?', reply_markup=get_keyboard())
        
        # Сохраняем обновленный список в состоянии
        if updated_list:
            await state.update_data(list_users_send=[list_users[0], updated_list])
            
        # Устанавливаем состояние для продолжения редактирования
        await state.set_state(MainState.edit_mode_continue)
        return
    elif message_from_user == 'нет':
        await message.answer(MESSAGES['ENTER_USER_DATA'], 
                          reply_markup=get_keyboard(answer_yes="", answer_no="", add_back=True))
        await state.set_state(MainState.edit_mode_add_user)
        return
    else:
        await message.answer(MESSAGES['YES_NO_REQUEST'], 
                          reply_markup=get_keyboard())
        return

@router.message(MainState.edit_mode_continue)
async def continue_editing_handler(message: Message, state: FSMContext):
    status = await get_status(state, message)
    if status != "admin":
        await message.answer(MESSAGES['NO_RIGHTS'])
        return
        
    if message.text == "Назад":
        await go_back(message, state)
        return
        
    message_from_user = message.text.lower()
    if message_from_user == 'да':
        await message.answer(f"Что Вы хотите сделать с данным списком?\n"
                           f"- Удалить пользователя\n"
                           f"- Добавить нового пользователя",
                           reply_markup=get_keyboard(answer_yes="Удалить",
                                                  answer_no="Добавить", inline=True))
        await state.set_state(MainState.edit_mode_user_yes_no)
        return
    elif message_from_user == 'нет':
        await message.answer(MESSAGES['CONTINUE_WORK'], reply_markup=get_main_keyboard())
        await state.clear()
        return
    else:
        await message.answer(MESSAGES['YES_NO_REQUEST'], reply_markup=get_keyboard())
        return

@router.message(Command("delete_user"))
async def cmd_delete_user(message: Message, state: FSMContext):
    if message.from_user.id != 864146808:
        await message.answer("Иж что захотел, пока не дорос!")
        return
    await message.answer("Введите @username пользователя, которого нужно удалить:")
    await state.set_state(MainState.delete_user_username)

@router.message(MainState.delete_user_username)
async def process_delete_user_username(message: Message, state: FSMContext):
    username = message.text
    db = DataBase(db_name)
    db.delete_user(username)
    await message.answer(f"Пользователь {username} удален.")
    await state.clear()
    return
