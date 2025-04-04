import sqlite3
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DB_PATH

class DataBase:
    def __init__(self, db_name=None):
        self.name = db_name or DB_PATH
        self.connection = sqlite3.connect(self.name)
        self.cursor = self.connection.cursor()
        self._initialize_tables()
        
    def _initialize_tables(self):
        """Инициализирует все необходимые таблицы в базе данных"""
        tables = {
            'status_table': """
                CREATE TABLE IF NOT EXISTS status_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    status_info TEXT NOT NULL
                )
            """,
            'user_lists': """
                CREATE TABLE IF NOT EXISTS user_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    list_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """,
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY NOT NULL,
                    username TEXT NOT NULL,
                    full_name TEXT NOT NULL UNIQUE
                )
            """
        }
        
        for table_name, query in tables.items():
            try:
                self.cursor.execute(query)
                self.connection.commit()
            except sqlite3.Error as e:
                print(f"Ошибка при создании таблицы {table_name}: {e}")

    def check_table(self, table_name):
        """Проверяет существование таблицы в БД"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        return bool(self.execute_query(query, (table_name,), fetch_one=True))

    def close(self):
        """Закрывает соединение с БД"""
        self.connection.close()

    def drop_table(self, table_name):
        """Удаляет таблицу из БД"""
        sql_query = f"DROP table if exists {table_name}"
        return self.execute_query(sql_query)

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """
        Выполняет SQL-запрос и возвращает результат в зависимости от параметров
        
        Args:
            query: SQL-запрос
            params: параметры запроса
            fetch_one: вернуть одну запись
            fetch_all: вернуть все записи
            
        Returns:
            Результат запроса в зависимости от параметров
        """
        try:
            # Начинаем транзакцию
            self.connection.execute("BEGIN TRANSACTION")
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if query.strip().lower().startswith("select"):
                if fetch_one:
                    result = self.cursor.fetchone()
                elif fetch_all:
                    result = self.cursor.fetchall()
                else:
                    result = True
            else:
                result = True

            # Фиксируем транзакцию
            self.connection.commit()
            return result
            
        except sqlite3.Error as e:
            # Откатываем транзакцию в случае ошибки
            self.connection.rollback()
            print(f"Ошибка выполнения запроса: {e}")
            print(f"Запрос: {query}")
            print(f"Параметры: {params}")
            return False
        except Exception as e:
            # Откатываем транзакцию в случае любой другой ошибки
            self.connection.rollback()
            print(f"Неожиданная ошибка: {e}")
            return False

    def get_table(self, table_name, num=0):
        """Возвращает данные таблицы в виде pandas DataFrame"""
        if not self.check_table(table_name):
            return pd.DataFrame()

        sql_query = f"SELECT * FROM {table_name}"
        data = self.execute_query(sql_query, fetch_all=True)
        
        if not data:
            return pd.DataFrame()
            
        column_names = [description[0] for description in self.cursor.description]
        df = pd.DataFrame(data, columns=column_names)
        df = df.fillna(" ")
        
        return df if num == 0 else df.head(num)
    
    def get_active_users(self, status_info=None):
        if status_info:
            sql_query = f"SELECT * FROM users WHERE users.user_id IN (SELECT user_id FROM status_table WHERE status_info = ?)"
            data = self.execute_query(sql_query, (status_info,), fetch_all=True)
        else:
            sql_query = f"SELECT * FROM users WHERE users.user_id IN (SELECT user_id FROM status_table)"
            data = self.execute_query(sql_query, fetch_all=True)
        column_names = [description[0] for description in self.cursor.description]
        df = pd.DataFrame(data, columns=column_names)
        df = df.fillna(" ")
        return df
    
    def get_unique_elements(self, table_name, column_name):
        """Возвращает уникальные значения столбца таблицы"""
        if not self.check_table(table_name):
            return []

        query = f"SELECT DISTINCT {column_name} FROM {table_name}"
        data = self.execute_query(query, fetch_all=True)
        return [item[0] for item in data] if data else []

    # Методы для работы со статусами пользователей
    def get_status(self, user_id):
        """Получает статус пользователя"""
        query = "SELECT status_info FROM status_table WHERE user_id = ?"
        result = self.execute_query(query, (user_id,), fetch_all=True)
        return result[0] if result else None

    def get_data(self, user_id):
        """Получает данные пользователя"""
        query = "SELECT data_info FROM status_table WHERE user_id = ?"
        return self.execute_query(query, (user_id,), fetch_one=True)

    def insert_new_note_status(self, user_id, status_info):
        """Добавляет новую запись о статусе пользователя"""
        query = "INSERT INTO status_table (user_id, status_info) VALUES (?, ?)"
        return self.execute_query(query, (user_id, status_info))

    def update_status(self, user_id, status_info):
        """Обновляет статус пользователя, используя UPSERT (обновление или вставка)"""
        # Проверяем, существует ли запись для пользователя
        status = self.get_status(user_id)
        
        if status:
            # Если запись существует, обновляем статус
            query = "UPDATE status_table SET status_info = ? WHERE user_id = ?"
            return self.execute_query(query, (status_info, user_id))
        else:
            # Если записи нет, создаем новую
            query = "INSERT INTO status_table (user_id, status_info) VALUES (?, ?)"
            return self.execute_query(query, (user_id, status_info))

    def delete_status(self, user_id):
        """Удаляет статус пользователя или изменяет его на обычного пользователя"""
        # Проверяем, существует ли запись для пользователя
        status = self.get_status(user_id)
        
        if status:
            # Если запись существует, обновляем статус на "user"
            query = "UPDATE status_table SET status_info = ? WHERE user_id = ?"
            return self.execute_query(query, ("user", user_id))
        
        return False

    # Методы для работы со списками пользователей
    def get_user_lists(self, user_id):
        """Получает все списки пользователя"""
        try:
            # Проверяем существование пользователя
            check_query = "SELECT COUNT(*) FROM users WHERE user_id = ?"
            if not self.execute_query(check_query, (user_id,), fetch_one=True)[0]:
                return []

            query = """
                SELECT ul.id, ul.user_id, ul.list_name, GROUP_CONCAT(u.user_id) as user_ids
                FROM user_lists ul
                LEFT JOIN users u ON u.user_id IN (
                    SELECT CAST(value AS INTEGER) 
                    FROM json_each('[' || REPLACE(ul.list_name, ',', ',') || ']')
                )
                WHERE ul.user_id = ?
                GROUP BY ul.id
            """
            return self.execute_query(query, (user_id,), fetch_all=True) or []
        except Exception as e:
            print(f"Ошибка при получении списков пользователя: {e}")
            return []

    def insert_new_note_user_lists(self, user_id, list_name):
        """Добавляет новый список пользователей"""
        try:
            # Проверяем существование пользователя
            check_query = "SELECT COUNT(*) FROM users WHERE user_id = ?"
            if not self.execute_query(check_query, (user_id,), fetch_one=True)[0]:
                return False

            # Проверяем, что все ID в списке существуют в таблице users
            try:
                user_ids = list(map(int, list_name.split(',')))
            except ValueError:
                print("Некорректный формат списка ID пользователей")
                return False

            if user_ids:
                placeholders = ','.join('?' for _ in user_ids)
                check_query = f"SELECT COUNT(*) FROM users WHERE user_id IN ({placeholders})"
                count = self.execute_query(check_query, user_ids, fetch_one=True)
                if count[0] != len(user_ids):
                    print("Не все пользователи из списка существуют в базе")
                    return False

            # Вставляем новый список
            query = "INSERT INTO user_lists (user_id, list_name) VALUES (?, ?)"
            return self.execute_query(query, (user_id, list_name))
        except Exception as e:
            print(f"Ошибка при добавлении списка пользователей: {e}")
            return False

    def edit_note_user_lists(self, user_id, new_user_in_list, id_list, delete_user=False):
        """Редактирует список пользователей"""
        try:
            # Проверяем существование списка
            query = "SELECT list_name FROM user_lists WHERE user_id = ? AND id = ?"
            current_list = self.execute_query(query, (user_id, id_list), fetch_one=True)
            
            if not current_list:
                return False
                
            current_list = current_list[0]
            try:
                users = set(map(int, current_list.split(','))) if current_list else set()
            except ValueError:
                print("Некорректный формат списка пользователей")
                return False

            id_new_user_in_list = new_user_in_list[0]

            # Проверяем существование пользователя в базе
            if not delete_user:
                check_query = "SELECT COUNT(*) FROM users WHERE user_id = ?"
                if not self.execute_query(check_query, (id_new_user_in_list,), fetch_one=True)[0]:
                    print("Пользователь не существует в базе")
                    return False

            # Добавляем/удаляем пользователя
            if id_new_user_in_list in users or delete_user:
                users.remove(id_new_user_in_list)
            else:
                users.add(id_new_user_in_list)
                
            updated_list = ','.join(map(str, users))
            
            # Обновляем список
            query = "UPDATE user_lists SET list_name = ? WHERE user_id = ? AND id = ?"
            if not self.execute_query(query, (updated_list, user_id, id_list)):
                return False
            
            # Если список пустой, удаляем его
            if not updated_list:
                return self.delete_user_list(user_id, id_list)
                
            return True
        except Exception as e:
            print(f"Ошибка при редактировании списка пользователей: {e}")
            return False

    def delete_user_list(self, user_id, id_list):
        """Удаляет список пользователей"""
        try:
            # Проверяем существование списка перед удалением
            check_query = "SELECT COUNT(*) FROM user_lists WHERE user_id = ? AND id = ?"
            if not self.execute_query(check_query, (user_id, id_list), fetch_one=True)[0]:
                return False

            delete_query = "DELETE FROM user_lists WHERE user_id = ? AND id = ?"
            return self.execute_query(delete_query, (user_id, id_list))
        except Exception as e:
            print(f"Ошибка при удалении списка пользователей: {e}")
            return False

    def get_users_for_sending(self, list_id, user_id):
        """Получает список пользователей для рассылки с проверкой корректности"""
        try:
            # Получаем список и проверяем права доступа
            query = """
                SELECT ul.list_name
                FROM user_lists ul
                WHERE ul.id = ? AND ul.user_id = ?
            """
            result = self.execute_query(query, (list_id, user_id), fetch_one=True)
            
            if not result:
                return None
                
            list_name = result[0]
            if not list_name:
                return []
                
            # Получаем пользователей из списка
            try:
                user_ids = list(map(int, list_name.split(',')))
            except ValueError:
                print("Некорректный формат списка ID пользователей")
                return []

            if not user_ids:
                return []
                
            # Проверяем существование всех пользователей
            placeholders = ','.join('?' for _ in user_ids)
            query = f"""
                SELECT u.user_id, u.full_name, u.username
                FROM users u
                WHERE u.user_id IN ({placeholders})
            """
            return self.execute_query(query, user_ids, fetch_all=True) or []
        except Exception as e:
            print(f"Ошибка при получении списка пользователей для рассылки: {e}")
            return None

    # Методы для работы с пользователями
    def insert_new_user(self, user_id, username, full_name):
        """Добавляет нового пользователя"""
        try:
            # Проверяем, не существует ли уже пользователь с таким ID
            check_query = "SELECT COUNT(*) FROM users WHERE user_id = ?"
            if self.execute_query(check_query, (user_id,), fetch_one=True)[0] > 0:
                return False

            # Проверяем, не существует ли уже пользователь с таким username
            check_query = "SELECT COUNT(*) FROM users WHERE username = ?"
            if self.execute_query(check_query, (username,), fetch_one=True)[0] > 0:
                return False

            # Проверяем, не существует ли уже пользователь с таким full_name
            check_query = "SELECT COUNT(*) FROM users WHERE full_name = ?"
            if self.execute_query(check_query, (full_name,), fetch_one=True)[0] > 0:
                return False

            # Вставляем нового пользователя
            query = "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)"
            return self.execute_query(query, (user_id, username, full_name))
        except Exception as e:
            print(f"Ошибка при добавлении пользователя: {e}")
            return False

    def get_users(self, data, colum="user_id"):
        """Получает пользователей по указанным ID или другим параметрам"""
        try:
            if not data:
                return []

            # Проверяем корректность параметра colum
            valid_columns = ["user_id", "username", "full_name"]
            if colum not in valid_columns:
                print(f"Некорректный параметр colum: {colum}")
                return []

            if isinstance(data, list):
                # Проверяем, что все элементы списка имеют правильный тип
                if colum == "user_id":
                    try:
                        data = [int(x) for x in data]
                    except ValueError:
                        print("Некорректный формат ID пользователей")
                        return []
                placeholders = ",".join("?" for _ in data)
                query = f"SELECT * FROM users WHERE {colum} IN ({placeholders})"
            else:
                if colum == "user_id":
                    try:
                        data = int(data)
                    except ValueError:
                        print("Некорректный формат ID пользователя")
                        return []
                query = f"SELECT * FROM users WHERE {colum} = ?"
                data = [data]

            return self.execute_query(query, data, fetch_all=True) or []
        except Exception as e:
            print(f"Ошибка при получении пользователей: {e}")
            return []

    def delete_user(self, username):
        """Удаляет пользователя и его ID из всех списков"""
        try:
            # Получаем user_id по username
            query = "SELECT user_id FROM users WHERE full_name = ?"
            result = self.execute_query(query, (username,), fetch_one=True)

            if not result:
                return False
            user_id = result[0]

            # Получаем все списки пользователей
            query = "SELECT id, list_name FROM user_lists"
            lists = self.execute_query(query, fetch_all=True)
            
            # Обновляем каждый список, удаляя user_id
            for list_id, list_name in lists:
                if list_name:
                    try:
                        # Разбиваем список на отдельные ID
                        user_ids = list(map(int, list_name.split(',')))
                        # Удаляем user_id из списка
                        if user_id in user_ids:
                            user_ids.remove(user_id)
                            # Собираем список обратно
                            new_users_list = ','.join(map(str, user_ids))
                            # Обновляем список в базе данных
                            update_query = "UPDATE user_lists SET list_name = ? WHERE id = ?"
                            if not self.execute_query(update_query, (new_users_list, list_id)):
                                return False
                    except ValueError:
                        print(f"Ошибка при обработке списка пользователей: {list_name}")
                        continue

            # Удаляем пользователя из таблицы users
            query = "DELETE FROM users WHERE full_name = ?"
            return self.execute_query(query, (username,))
        except Exception as e:
            print(f"Ошибка при удалении пользователя: {e}")
            return False