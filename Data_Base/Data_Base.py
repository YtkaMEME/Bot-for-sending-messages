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
                    user_id TEXT UNIQUE NOT NULL,
                    status_info TEXT NOT NULL
                )
            """,
            'user_lists': """
                CREATE TABLE IF NOT EXISTS user_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    list_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if query.strip().lower().startswith("select"):
                if fetch_one:
                    return self.cursor.fetchone()
                elif fetch_all:
                    return self.cursor.fetchall()
                return True

            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
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
        query = "SELECT * FROM user_lists WHERE user_id = ?"
        return self.execute_query(query, (user_id,), fetch_all=True) or []

    def insert_new_note_user_lists(self, user_id, list_name):
        """Добавляет новый список пользователей"""
        query = "INSERT INTO user_lists (user_id, list_name) VALUES (?, ?)"
        if self.execute_query(query, (user_id, list_name)):
            # Переупорядочить ID
            self._reorder_user_lists(user_id)
            return True
        return False

    def _reorder_user_lists(self, user_id):
        """Переупорядочивает ID в списках пользователей"""
        reorder_query = """
            UPDATE user_lists
            SET id = (
                SELECT COUNT(*)
                FROM user_lists AS ul
                WHERE ul.id <= user_lists.id
            )
            WHERE user_id = ?;
        """
        return self.execute_query(reorder_query, (user_id,))

    def edit_note_user_lists(self, user_id, new_user_in_list, id_list):
        """Редактирует список пользователей"""
        # Получаем текущий список
        query = "SELECT list_name FROM user_lists WHERE user_id = ? AND id = ?"
        current_list = self.execute_query(query, (user_id, id_list), fetch_one=True)
        
        if not current_list:
            return None
            
        current_list = current_list[0]
        users = set(map(int, current_list.split(','))) if current_list else set()
        id_new_user_in_list = new_user_in_list[0]
        
        # Добавляем/удаляем пользователя
        if id_new_user_in_list in users:
            users.remove(id_new_user_in_list)
        else:
            users.add(id_new_user_in_list)
            
        updated_list = ','.join(map(str, users))
        
        # Обновляем список
        query = "UPDATE user_lists SET list_name = ? WHERE user_id = ? AND id = ?"
        self.execute_query(query, (updated_list, user_id, id_list))
        
        # Если список пустой, удаляем его
        if not updated_list:
            self.delete_user_list(user_id, id_list)
            
        return True

    def delete_user_list(self, user_id, id_list):
        """Удаляет список пользователей"""
        delete_query = "DELETE FROM user_lists WHERE user_id = ? AND id = ?"
        if self.execute_query(delete_query, (user_id, id_list)):
            # Переупорядочить ID
            self._reorder_user_lists(user_id)
            return True
        return False

    # Методы для работы с пользователями
    def insert_new_user(self, user_id, username, full_name):
        """Добавляет нового пользователя"""
        query = "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)"
        return self.execute_query(query, (user_id, username, full_name))

    def get_users(self, data, colum="user_id"):
        """Получает пользователей по указанным ID или другим параметрам"""
        if not data:
            return []
            
        if isinstance(data, list):
            placeholders = ",".join("?" for _ in data)
            query = f"SELECT * FROM users WHERE {colum} IN ({placeholders})"
        else:
            query = f"SELECT * FROM users WHERE {colum} = ?"
            data = [data]  # Преобразуем одиночное значение в список для единообразия
            
        return self.execute_query(query, data, fetch_all=True) or []

    def delete_user(self, user_id):
        """Удаляет пользователя"""
        query = "DELETE FROM users WHERE user_id = ?"
        return self.execute_query(query, (user_id,))