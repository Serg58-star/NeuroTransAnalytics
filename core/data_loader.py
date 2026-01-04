# core/data_loader.py
import pandas as pd
import os
import sqlite3
from tkinter import messagebox
import logging
from typing import Optional, Dict, Any, Tuple, List
import sys
import json


class DataLoader:
    def __init__(self):
        self.users_df: Optional[pd.DataFrame] = None
        self.boxbase_df: Optional[pd.DataFrame] = None
        self.db_connection = None
        self.setup_logging()
        self.access_drivers_available = False
        self.available_access_drivers = []
        self.new_schema_available = False
        self.db_path = "neuro_data.db"
        self._check_access_drivers()
        self._check_new_schema()

    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _check_new_schema(self):
        """Проверяет наличие новой схемы БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visual_tests'")
            self.new_schema_available = cursor.fetchone() is not None
            conn.close()
            self.logger.info(f"Новая схема БД доступна: {self.new_schema_available}")
        except:
            self.new_schema_available = False

    def _check_access_drivers(self):
        """Проверка доступности драйверов Access при инициализации"""
        try:
            import pyodbc
            # Получаем список всех драйверов ODBC
            all_drivers = pyodbc.drivers()

            # Ищем драйверы Access
            access_drivers = []
            for driver in all_drivers:
                driver_lower = driver.lower()
                if any(keyword in driver_lower for keyword in ['access', 'mdb', 'ace', 'jet']):
                    access_drivers.append(driver)

            self.available_access_drivers = access_drivers
            self.access_drivers_available = len(access_drivers) > 0

            if self.access_drivers_available:
                self.logger.info(f"Найдены драйверы Access: {access_drivers}")
            else:
                self.logger.warning("Драйверы Access не найдены")

        except ImportError:
            self.logger.warning("PyODBC не установлен. Access файлы недоступны.")
            self.access_drivers_available = False

    def check_pyodbc_available(self) -> Tuple[bool, str]:
        """Проверка доступности pyodbc и драйверов Access"""
        try:
            import pyodbc
            if not self.access_drivers_available:
                if self.available_access_drivers:
                    return False, f"Драйверы Access найдены, но недоступны: {self.available_access_drivers}"
                else:
                    return False, "Драйверы Access не найдены. Установите Microsoft Access Database Engine"
            return True, f"PyODBC доступен. Драйверы: {', '.join(self.available_access_drivers)}"
        except ImportError:
            return False, "PyODBC не установлен. Установите: pip install pyodbc"

    def get_patients_from_new_schema(self) -> Optional[pd.DataFrame]:
        """Получение пациентов из новой схемы"""
        if not self.new_schema_available:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql("SELECT * FROM patients", conn)
            conn.close()
            self.logger.info(f"Загружено {len(df)} пациентов из новой схемы")
            return df
        except Exception as e:
            self.logger.error(f"Ошибка получения пациентов из новой схемы: {e}")
            return None

    def get_visual_tests(self, patient_id: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Получение визуальных тестов из новой схемы"""
        if not self.new_schema_available:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            if patient_id:
                query = """
                        SELECT vt.*, ts.session_date, ts.session_time
                        FROM visual_tests vt
                                 JOIN testing_sessions ts ON vt.session_id = ts.id
                        WHERE ts.patient_id = ? \
                        """
                df = pd.read_sql(query, conn, params=(patient_id,))
            else:
                df = pd.read_sql("SELECT * FROM visual_tests", conn)
            conn.close()
            self.logger.info(f"Загружено {len(df)} визуальных тестов из новой схемы")
            return df
        except Exception as e:
            self.logger.error(f"Ошибка получения визуальных тестов: {e}")
            return None

    def get_neurotransmitter_scores(self, patient_id: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Получение нейромедиаторных показателей"""
        if not self.new_schema_available:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                    SELECT vt.*, ts.session_date, p.fname, p.lname
                    FROM visual_tests vt
                             JOIN testing_sessions ts ON vt.session_id = ts.id
                             JOIN patients p ON ts.patient_id = p.id \
                    """
            if patient_id:
                query += " WHERE ts.patient_id = ?"
                df = pd.read_sql(query, conn, params=(patient_id,))
            else:
                df = pd.read_sql(query, conn)
            conn.close()
            self.logger.info(f"Загружено {len(df)} нейромедиаторных показателей")
            return df
        except Exception as e:
            self.logger.error(f"Ошибка получения нейромедиаторных показателей: {e}")
            return None

    def load_from_access_database(self, access_file_path: str, table_name: str = None) -> Dict[str, pd.DataFrame]:
        """Загрузка таблицы напрямую из Access базы данных"""
        try:
            # Проверяем доступность драйверов
            pyodbc_available, message = self.check_pyodbc_available()
            if not pyodbc_available:
                raise ImportError(message)

            import pyodbc

            # Проверяем существование файла
            if not os.path.exists(access_file_path):
                raise FileNotFoundError(f"Access файл не найден: {access_file_path}")

            self.logger.info(f"Попытка загрузки из Access: {access_file_path}")

            # Формируем connection string
            conn_str = self._get_access_connection_string(access_file_path)

            # Подключаемся к базе
            connection = pyodbc.connect(conn_str)
            cursor = connection.cursor()

            # Получаем список таблиц
            tables = cursor.tables(tableType='TABLE')
            available_tables = [table.table_name for table in tables]

            self.logger.info(f"Доступные таблицы в Access: {available_tables}")

            # Если таблица не указана, используем логику выбора
            if table_name is None:
                return self._auto_detect_and_load_tables(connection, available_tables)
            else:
                # Загружаем конкретную таблицу
                if table_name not in available_tables:
                    raise ValueError(f"Таблица {table_name} не найдена в базе. Доступные: {available_tables}")

                df = pd.read_sql(f"SELECT * FROM [{table_name}]", connection)
                connection.close()

                self.logger.info(f"Загружена таблица {table_name}: {len(df)} строк")
                return {table_name: df}

        except Exception as e:
            self.logger.error(f"Ошибка загрузки из Access: {e}")
            if 'connection' in locals():
                try:
                    connection.close()
                except:
                    pass
            raise

    def _get_access_connection_string(self, access_file_path: str) -> str:
        """Получение строки подключения для Access"""
        if not self.available_access_drivers:
            raise ConnectionError("Нет доступных драйверов Access")

        # Пробуем разные драйверы в порядке приоритета
        test_drivers = self.available_access_drivers + [
            '{Microsoft Access Driver (*.mdb, *.accdb)}',
            '{Microsoft Access Driver (*.mdb)}',
            '{Microsoft Access (*.mdb)}'
        ]

        for driver in test_drivers:
            try:
                conn_str = f'DRIVER={driver};DBQ={access_file_path};'
                import pyodbc
                # Пробуем подключиться
                test_conn = pyodbc.connect(conn_str)
                test_conn.close()
                self.logger.info(f"Успешный драйвер: {driver}")
                return conn_str
            except Exception as e:
                self.logger.debug(f"Драйвер {driver} не сработал: {e}")
                continue

        raise ConnectionError(
            f"Не удалось подключиться к Access файлу ни с одним драйвером. Испробованы: {test_drivers}")

    def _auto_detect_and_load_tables(self, connection, available_tables: list) -> Dict[str, pd.DataFrame]:
        """Автоматическое определение и загрузка таблиц users и boxbase"""
        loaded_data = {}

        # Поиск таблицы users
        users_table = self._find_table_by_pattern(available_tables,
                                                  ['user', 'patient', 'subject', 'испытуем', 'пациент'])
        if users_table:
            try:
                df = pd.read_sql(f"SELECT * FROM [{users_table}]", connection)
                loaded_data['users'] = df
                self.logger.info(f"Загружена таблица {users_table} как users: {len(df)} строк")
            except Exception as e:
                self.logger.warning(f"Не удалось загрузить таблицу {users_table}: {e}")

        # Поиск таблицы boxbase
        boxbase_table = self._find_table_by_pattern(available_tables,
                                                    ['box', 'test', 'result', 'data', 'base', 'реакц', 'тест'])
        if boxbase_table:
            try:
                df = pd.read_sql(f"SELECT * FROM [{boxbase_table}]", connection)
                loaded_data['boxbase'] = df
                self.logger.info(f"Загружена таблица {boxbase_table} как boxbase: {len(df)} строк")
            except Exception as e:
                self.logger.warning(f"Не удалось загрузить таблицу {boxbase_table}: {e}")

        connection.close()

        if not loaded_data:
            # Если не нашли по шаблонам, пробуем загрузить первую таблицу
            try:
                connection = pyodbc.connect(self._get_access_connection_string(access_file_path))
                first_table = available_tables[0]
                df = pd.read_sql(f"SELECT * FROM [{first_table}]", connection)
                loaded_data[first_table] = df
                self.logger.info(f"Загружена первая таблица {first_table}: {len(df)} строк")
                connection.close()
            except:
                pass

        if not loaded_data:
            raise ValueError("Не найдены подходящие таблицы в базе данных")

        return loaded_data

    def _find_table_by_pattern(self, tables: list, patterns: list) -> Optional[str]:
        """Поиск таблицы по шаблонам названий"""
        for table in tables:
            table_lower = table.lower()
            for pattern in patterns:
                if pattern in table_lower:
                    return table
        return None

    def load_users_from_access(self, access_file_path: str) -> pd.DataFrame:
        """Загрузка данных users напрямую из Access"""
        try:
            result = self.load_from_access_database(access_file_path)

            if 'users' in result:
                self.users_df = result['users']
                self._normalize_users_columns()
                self.clean_users_data()
                self.logger.info(f"Users данные загружены из Access: {len(self.users_df)} строк")
                return self.users_df
            else:
                # Если не нашли users, но есть одна таблица - используем её
                if len(result) == 1:
                    table_name, df = list(result.items())[0]
                    self.users_df = df
                    self._normalize_users_columns()
                    self.clean_users_data()
                    self.logger.info(f"Использована таблица {table_name} как users: {len(self.users_df)} строк")
                    return self.users_df
                else:
                    raise ValueError("Таблица users не найдена в Access базе")

        except Exception as e:
            self.logger.error(f"Ошибка загрузки users из Access: {e}")
            raise

    def load_boxbase_from_access(self, access_file_path: str) -> pd.DataFrame:
        """Загрузка данных boxbase напрямую из Access"""
        try:
            result = self.load_from_access_database(access_file_path)

            if 'boxbase' in result:
                self.boxbase_df = result['boxbase']
                self._normalize_boxbase_columns()
                self.clean_boxbase_data()
                self.logger.info(f"Boxbase данные загружены из Access: {len(self.boxbase_df)} строк")
                return self.boxbase_df
            else:
                # Если не нашли boxbase, но есть одна таблица - используем её
                if len(result) == 1:
                    table_name, df = list(result.items())[0]
                    self.boxbase_df = df
                    self._normalize_boxbase_columns()
                    self.clean_boxbase_data()
                    self.logger.info(f"Использована таблица {table_name} как boxbase: {len(self.boxbase_df)} строк")
                    return self.boxbase_df
                else:
                    raise ValueError("Таблица boxbase не найдена в Access базе")

        except Exception as e:
            self.logger.error(f"Ошибка загрузки boxbase из Access: {e}")
            raise

    def load_both_from_access(self, access_file_path: str) -> Dict[str, pd.DataFrame]:
        """Загрузка обоих таблиц из одной Access базы"""
        try:
            result = self.load_from_access_database(access_file_path)

            loaded_tables = []

            if 'users' in result:
                self.users_df = result['users']
                self._normalize_users_columns()
                self.clean_users_data()
                loaded_tables.append('users')
            elif len(result) == 2:
                # Если две таблицы, пробуем определить какая есть users
                for table_name, df in result.items():
                    if any(pattern in table_name.lower() for pattern in ['user', 'patient', 'subject']):
                        self.users_df = df
                        self._normalize_users_columns()
                        self.clean_users_data()
                        loaded_tables.append('users')
                        break

            if 'boxbase' in result:
                self.boxbase_df = result['boxbase']
                self._normalize_boxbase_columns()
                self.clean_boxbase_data()
                loaded_tables.append('boxbase')
            elif len(result) == 2:
                # Если две таблицы, вторая будет boxbase
                for table_name, df in result.items():
                    if self.users_df is None or not df.equals(self.users_df):
                        self.boxbase_df = df
                        self._normalize_boxbase_columns()
                        self.clean_boxbase_data()
                        loaded_tables.append('boxbase')
                        break

            self.logger.info(f"✅ Загружены таблицы из Access: {', '.join(loaded_tables)}")
            return {
                'users': self.users_df,
                'boxbase': self.boxbase_df
            }

        except Exception as e:
            self.logger.error(f"Ошибка загрузки из Access: {e}")
            raise

    def load_csv(self, file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """Загрузка CSV файла с автоматическим определением кодировки"""
        try:
            # Пробуем разные кодировки
            encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin1']

            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        nrows=nrows,
                        sep=None,
                        engine='python',
                        on_bad_lines='skip'
                    )
                    self.logger.info(f"CSV загружен ({encoding}): {file_path}, строк: {len(df)}")
                    return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    self.logger.debug(f"Кодировка {encoding} не подошла: {e}")
                    continue

            # Если все кодировки не подошли, пробуем с обработкой ошибок
            try:
                df = pd.read_csv(
                    file_path,
                    encoding='utf-8',
                    nrows=nrows,
                    sep=',',
                    on_bad_lines='skip',
                    engine='python'
                )
                self.logger.info(f"CSV загружен (с обработкой ошибок): {file_path}")
                return df
            except Exception as e:
                self.logger.error(f"Все методы загрузки CSV не сработали: {e}")
                raise ValueError("Не удалось загрузить CSV файл")

        except Exception as e:
            self.logger.error(f"Критическая ошибка загрузки CSV: {e}")
            raise

    def load_excel(self, file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """Загрузка Excel файла с оптимизацией памяти"""
        try:
            # Используем openpyxl для .xlsx
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(
                    file_path,
                    nrows=nrows,
                    engine='openpyxl'
                )
            else:
                # Для .xls используем xlrd
                df = pd.read_excel(
                    file_path,
                    nrows=nrows,
                    engine='xlrd'
                )

            self.logger.info(f"Excel загружен: {file_path}, строк: {len(df)}")
            return df

        except Exception as e:
            self.logger.error(f"Ошибка загрузки Excel: {e}")

            # Альтернативная попытка
            try:
                df = pd.read_excel(file_path, nrows=nrows)
                self.logger.info(f"Excel загружен (автоопределение): {file_path}")
                return df
            except Exception:
                self.logger.error("Все методы загрузки Excel не сработали")
                raise

    def load_access(self, file_path: str) -> pd.DataFrame:
        """Загрузка Access файла (устаревший метод - используйте новые методы)"""
        try:
            result = self.load_from_access_database(file_path)
            if result:
                return list(result.values())[0]
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки Access: {e}")
            messagebox.showerror(
                "Ошибка Access",
                f"Не удалось загрузить Access файл:\n{str(e)}"
            )
            return pd.DataFrame()

    def load_data(self, file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """Универсальная загрузка данных по расширению файла"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.csv':
            return self.load_csv(file_path, nrows)
        elif file_ext in ['.xlsx', '.xls']:
            return self.load_excel(file_path, nrows)
        elif file_ext in ['.mdb', '.accdb']:
            return self.load_access(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")

    def load_users_data(self, file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """Специализированная загрузка данных users"""
        try:
            self.users_df = self.load_data(file_path, nrows)

            # Отладочная информация о столбцах
            self.logger.info(f"Оригинальные столбцы users: {self.users_df.columns.tolist()}")

            # Минимальная нормализация столбцов
            self._normalize_users_columns()

            # Проверяем наличие необходимых столбцов (в любом регистре)
            required_columns = ['ID', 'YBORN', 'REGDATE', 'GENDER']
            available_columns = [col for col in self.users_df.columns if col.upper() in required_columns]

            if len(available_columns) < len(required_columns):
                missing = set(required_columns) - set(col.upper() for col in available_columns)
                self.logger.warning(f"В users отсутствуют столбцы: {missing}")
                messagebox.showwarning(
                    "Внимание",
                    f"В файле users отсутствуют столбцы: {', '.join(missing)}\n"
                    f"Найдены столбцы: {', '.join(self.users_df.columns.tolist())}"
                )

            # Очистка и подготовка данных
            self.clean_users_data()

            self.logger.info(f"Users данные подготовлены: {len(self.users_df)} строк")
            self.logger.info(f"Финальные столбцы users: {self.users_df.columns.tolist()}")
            return self.users_df

        except Exception as e:
            self.logger.error(f"Ошибка загрузки users: {e}")
            raise

    def load_boxbase_data(self, file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """Специализированная загрузка данных boxbase"""
        try:
            self.boxbase_df = self.load_data(file_path, nrows)

            # Отладочная информация о столбцах
            self.logger.info(f"Оригинальные столбцы boxbase: {self.boxbase_df.columns.tolist()}")

            # Минимальная нормализация столбцов
            self._normalize_boxbase_columns()

            # Проверяем основные столбцы (в любом регистре)
            expected_columns = ['CNT', 'CURRENTDATE', 'CURRENTTIME', 'REG_ID']
            available_columns = [col for col in self.boxbase_df.columns if col.upper() in expected_columns]

            if len(available_columns) < 2:
                self.logger.warning(
                    f"В boxbase отсутствуют ключевые столбцы. "
                    f"Найдены: {list(self.boxbase_df.columns)}"
                )

            # Очистка и подготовка данных
            self.clean_boxbase_data()

            self.logger.info(f"Boxbase данные подготовлены: {len(self.boxbase_df)} строк")
            self.logger.info(f"Финальные столбцы boxbase: {self.boxbase_df.columns.tolist()}")
            return self.boxbase_df

        except Exception as e:
            self.logger.error(f"Ошибка загрузки boxbase: {e}")
            raise

    def _normalize_users_columns(self):
        """Нормализация названий столбцов users - минимальная"""
        if self.users_df is None:
            return

        # Сохраняем оригинальные названия для отладки
        original_columns = self.users_df.columns.tolist()

        # Создаем mapping для нормализации
        column_mapping = {}
        for col in self.users_df.columns:
            col_upper = col.upper()
            if col_upper == 'ID' or col_upper == 'SUBJECT_ID':
                column_mapping[col] = 'ID'
            elif col_upper == 'YBORN':
                column_mapping[col] = 'YBorn'
            elif col_upper == 'REGDATE':
                column_mapping[col] = 'RegDate'
            elif col_upper == 'GENDER' or col_upper == 'SEX':
                column_mapping[col] = 'Gender'
            # Остальные столбцы оставляем как есть

        # Применяем замены
        self.users_df.rename(columns=column_mapping, inplace=True)

        self.logger.info(f"Столбцы users после нормализации: {self.users_df.columns.tolist()}")

    def _normalize_boxbase_columns(self):
        """Нормализация названий столбцов boxbase - минимальная"""
        if self.boxbase_df is None:
            return

        # Создаем mapping для нормализации
        column_mapping = {}
        for col in self.boxbase_df.columns:
            col_upper = col.upper()
            if col_upper == 'REG_ID' or col_upper == 'REGID':
                column_mapping[col] = 'REG_ID'
            elif col_upper == 'CURRENTDATE':
                column_mapping[col] = 'CurrentDate'
            elif col_upper == 'CURRENTTIME':
                column_mapping[col] = 'CurrentTime'
            elif col_upper == 'VIDSOST':
                column_mapping[col] = 'VidSost'
            elif col_upper == 'VIDSOST_TXT':
                column_mapping[col] = 'VidSost_txt'
            # Остальные столбцы оставляем как есть

        # Применяем замены
        self.boxbase_df.rename(columns=column_mapping, inplace=True)

        self.logger.info(f"Столбцы boxbase после нормализации: {self.boxbase_df.columns.tolist()}")

    def clean_users_data(self):
        """Очистка и подготовка данных users"""
        if self.users_df is None:
            return

        # Удаляем полностью пустые строки
        initial_count = len(self.users_df)
        self.users_df = self.users_df.dropna(how='all')
        if initial_count != len(self.users_df):
            self.logger.info(f"Удалено пустых строк users: {initial_count - len(self.users_df)}")

        # Находим столбец ID (в любом регистре)
        id_column = None
        for col in self.users_df.columns:
            if col.upper() == 'ID':
                id_column = col
                break

        if id_column and id_column != 'ID':
            # Переименовываем в стандартный ID
            self.users_df.rename(columns={id_column: 'ID'}, inplace=True)
            id_column = 'ID'

        if 'ID' in self.users_df.columns:
            # Удаляем строки с пустыми ID и преобразуем к int
            self.users_df = self.users_df.dropna(subset=['ID'])
            self.users_df['ID'] = pd.to_numeric(self.users_df['ID'], errors='coerce')
            self.users_df = self.users_df.dropna(subset=['ID'])
            self.users_df['ID'] = self.users_df['ID'].astype(int)
        else:
            self.logger.warning("Столбец ID не найден в данных users")

        # Преобразуем даты с правильным форматом DD.MM.YYYY
        date_columns = ['YBorn', 'RegDate']
        for col in date_columns:
            if col in self.users_df.columns:
                try:
                    self.users_df[col] = pd.to_datetime(
                        self.users_df[col],
                        dayfirst=True,
                        errors='coerce'
                    )
                    success_count = self.users_df[col].notna().sum()
                    self.logger.info(f"Преобразовано дат {col}: {success_count}/{len(self.users_df)}")
                except Exception as e:
                    self.logger.warning(f"Не удалось преобразовать даты в столбце {col}: {e}")

        # Нормализуем пол (0-жен, 1-муж)
        if 'Gender' in self.users_df.columns:
            self.users_df['Gender'] = pd.to_numeric(self.users_df['Gender'], errors='coerce')
            self.users_df['Gender'] = self.users_df['Gender'].fillna(0).astype(int)
            self.users_df['Gender'] = self.users_df['Gender'].clip(0, 1)

            # Логируем распределение
            gender_counts = self.users_df['Gender'].value_counts()
            self.logger.info(f"Распределение по полу: ♂{gender_counts.get(1, 0)} ♀{gender_counts.get(0, 0)}")

    def clean_boxbase_data(self):
        """Очистка и подготовка данных boxbase"""
        if self.boxbase_df is None:
            return

        # Удаляем полностью пустые строки
        initial_count = len(self.boxbase_df)
        self.boxbase_df = self.boxbase_df.dropna(how='all')
        if initial_count != len(self.boxbase_df):
            self.logger.info(f"Удалено пустых строк boxbase: {initial_count - len(self.boxbase_df)}")

        # Находим столбец REG_ID (в любом регистре)
        reg_id_column = None
        for col in self.boxbase_df.columns:
            if col.upper() == 'REG_ID':
                reg_id_column = col
                break

        if reg_id_column and reg_id_column != 'REG_ID':
            # Переименовываем в стандартный REG_ID
            self.boxbase_df.rename(columns={reg_id_column: 'REG_ID'}, inplace=True)
            reg_id_column = 'REG_ID'

        if 'REG_ID' in self.boxbase_df.columns:
            # Удаляем строки с пустыми REG_ID и преобразуем к int
            self.boxbase_df = self.boxbase_df.dropna(subset=['REG_ID'])
            self.boxbase_df['REG_ID'] = pd.to_numeric(self.boxbase_df['REG_ID'], errors='coerce')
            self.boxbase_df = self.boxbase_df.dropna(subset=['REG_ID'])
            self.boxbase_df['REG_ID'] = self.boxbase_df['REG_ID'].astype(int)
        else:
            self.logger.warning("Столбец REG_ID не найден в данных boxbase")

        # Преобразуем даты
        if 'CurrentDate' in self.boxbase_df.columns:
            try:
                self.boxbase_df['CurrentDate'] = pd.to_datetime(
                    self.boxbase_df['CurrentDate'],
                    dayfirst=True,
                    errors='coerce'
                )
                success_count = self.boxbase_df['CurrentDate'].notna().sum()
                self.logger.info(f"Преобразовано дат CurrentDate: {success_count}/{len(self.boxbase_df)}")
            except Exception as e:
                self.logger.warning(f"Не удалось преобразовать даты в CurrentDate: {e}")

        # Преобразуем числовые колонки тестов
        test_columns = [col for col in self.boxbase_df.columns if col.startswith(('Tst1_', 'Tst2_', 'Tst3_'))]
        for col in test_columns:
            self.boxbase_df[col] = pd.to_numeric(self.boxbase_df[col], errors='coerce')

        self.logger.info(f"Обработано тестовых колонок: {len(test_columns)}")

    def get_data_info(self) -> Dict[str, Any]:
        """Получение подробной информации о загруженных данных"""
        info = {
            'users_loaded': self.users_df is not None,
            'boxbase_loaded': self.boxbase_df is not None,
            'users_rows': len(self.users_df) if self.users_df is not None else 0,
            'boxbase_rows': len(self.boxbase_df) if self.boxbase_df is not None else 0,
            'users_columns': [],
            'boxbase_columns': [],
            'users_sample': [],
            'boxbase_sample': [],
            'users_memory_usage': 0,
            'boxbase_memory_usage': 0,
            'access_drivers_available': self.access_drivers_available,
            'available_access_drivers': self.available_access_drivers,
            'new_schema_available': self.new_schema_available
        }

        if self.users_df is not None:
            info['users_columns'] = self.users_df.columns.tolist()
            info['users_sample'] = self.users_df.head(3).fillna('').to_dict('records')
            info['users_memory_usage'] = self.users_df.memory_usage(deep=True).sum()

            if 'Gender' in self.users_df.columns:
                gender_counts = self.users_df['Gender'].value_counts()
                info['users_gender_dist'] = {
                    'male': gender_counts.get(1, 0),
                    'female': gender_counts.get(0, 0)
                }

            if 'YBorn' in self.users_df.columns:
                info['users_age_info'] = {
                    'min_year': self.users_df['YBorn'].dt.year.min(),
                    'max_year': self.users_df['YBorn'].dt.year.max()
                }

        if self.boxbase_df is not None:
            info['boxbase_columns'] = self.boxbase_df.columns.tolist()
            info['boxbase_sample'] = self.boxbase_df.head(3).fillna('').to_dict('records')
            info['boxbase_memory_usage'] = self.boxbase_df.memory_usage(deep=True).sum()

            test_cols = [col for col in self.boxbase_df.columns if col.startswith(('Tst1_', 'Tst2_', 'Tst3_'))]
            info['boxbase_test_columns_count'] = len(test_cols)

            if 'CurrentDate' in self.boxbase_df.columns:
                info['boxbase_date_range'] = {
                    'min_date': self.boxbase_df['CurrentDate'].min(),
                    'max_date': self.boxbase_df['CurrentDate'].max()
                }

        return info

    def save_to_sqlite(self, db_path: str = 'neuro_data.db') -> str:
        """Сохранение данных в SQLite базу"""
        try:
            self.db_connection = sqlite3.connect(db_path)

            if self.users_df is not None:
                self.users_df.to_sql('users', self.db_connection,
                                     if_exists='replace', index=False)
                self.logger.info(f"Users сохранены в SQLite: {db_path}")

            if self.boxbase_df is not None:
                self.boxbase_df.to_sql('boxbase', self.db_connection,
                                       if_exists='replace', index=False)
                self.logger.info(f"Boxbase сохранены в SQLite: {db_path}")

            return db_path

        except Exception as e:
            self.logger.error(f"Ошибка сохранения в SQLite: {e}")
            raise

    def close_connection(self):
        """Закрытие соединений"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None

    def __del__(self):
        """Деструктор - закрываем соединения"""
        self.close_connection()

