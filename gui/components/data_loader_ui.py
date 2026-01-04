# gui/components/data_loader_ui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from typing import Callable, Optional
import pandas as pd
import sqlite3


class DataLoaderUI:
    """Компонент интерфейса для загрузки данных с автоматическим сохранением в SQLite"""

    def __init__(self, parent, data_loader, on_data_loaded: Callable):
        self.parent = parent
        self.data_loader = data_loader
        self.on_data_loaded = on_data_loaded
        self.db_path = "neuro_data.db"

        self.users_data: Optional[pd.DataFrame] = None
        self.boxbase_data: Optional[pd.DataFrame] = None
        self._auto_save_shown = False  # Для отслеживания показа уведомления
        self.new_schema_available = False
        self._check_new_schema()

        self.create_widgets()
        self.initialize_database()

    def _check_new_schema(self):
        """Проверяет наличие новой схемы БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visual_tests'")
            self.new_schema_available = cursor.fetchone() is not None
            conn.close()
        except:
            self.new_schema_available = False

    def initialize_database(self):
        """Инициализация SQLite базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Создаем таблицу users если не существует
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS users
                           (
                               ID
                               INTEGER
                               PRIMARY
                               KEY,
                               FName
                               TEXT,
                               SName
                               TEXT,
                               LName
                               TEXT,
                               YBorn
                               INTEGER,
                               RegDate
                               TEXT,
                               Active
                               INTEGER,
                               Gender
                               INTEGER
                           )
                           """)

            # Создаем таблицу boxbase если не существует
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS boxbase
                           (
                               cnt
                               INTEGER
                               PRIMARY
                               KEY,
                               CurrentDate
                               TEXT,
                               CurrentTime
                               TEXT,
                               REG_ID
                               INTEGER,
                               AD1
                               REAL,
                               AD2
                               REAL,
                               VidSost
                               INTEGER,
                               VidSost_txt
                               INTEGER,
                               Tst1_1
                               REAL,
                               Tst1_2
                               REAL,
                               Tst1_3
                               REAL,
                               Tst1_4
                               REAL,
                               Tst1_5
                               REAL,
                               Tst1_6
                               REAL,
                               Tst1_7
                               REAL,
                               Tst1_8
                               REAL,
                               Tst1_9
                               REAL,
                               Tst1_10
                               REAL,
                               Tst1_11
                               REAL,
                               Tst1_12
                               REAL,
                               Tst1_13
                               REAL,
                               Tst1_14
                               REAL,
                               Tst1_15
                               REAL,
                               Tst1_16
                               REAL,
                               Tst1_17
                               REAL,
                               Tst1_18
                               REAL,
                               Tst1_19
                               REAL,
                               Tst1_20
                               REAL,
                               Tst1_21
                               REAL,
                               Tst1_22
                               REAL,
                               Tst1_23
                               REAL,
                               Tst1_24
                               REAL,
                               Tst1_25
                               REAL,
                               Tst1_26
                               REAL,
                               Tst1_27
                               REAL,
                               Tst1_28
                               REAL,
                               Tst1_29
                               REAL,
                               Tst1_30
                               REAL,
                               Tst1_31
                               REAL,
                               Tst1_32
                               REAL,
                               Tst1_33
                               REAL,
                               Tst1_34
                               REAL,
                               Tst1_35
                               REAL,
                               Tst1_36
                               REAL,
                               RANO_POKAZ_1
                               INTEGER,
                               POZDNO_POKAZ_1
                               INTEGER,
                               result_1
                               REAL,
                               SrKvadrOtkl_1
                               REAL,
                               Tst2_1
                               REAL,
                               Tst2_2
                               REAL,
                               Tst2_3
                               REAL,
                               Tst2_4
                               REAL,
                               Tst2_5
                               REAL,
                               Tst2_6
                               REAL,
                               Tst2_7
                               REAL,
                               Tst2_8
                               REAL,
                               Tst2_9
                               REAL,
                               Tst2_10
                               REAL,
                               Tst2_11
                               REAL,
                               Tst2_12
                               REAL,
                               Tst2_13
                               REAL,
                               Tst2_14
                               REAL,
                               Tst2_15
                               REAL,
                               Tst2_16
                               REAL,
                               Tst2_17
                               REAL,
                               Tst2_18
                               REAL,
                               Tst2_19
                               REAL,
                               Tst2_20
                               REAL,
                               Tst2_21
                               REAL,
                               Tst2_22
                               REAL,
                               Tst2_23
                               REAL,
                               Tst2_24
                               REAL,
                               Tst2_25
                               REAL,
                               Tst2_26
                               REAL,
                               Tst2_27
                               REAL,
                               Tst2_28
                               REAL,
                               Tst2_29
                               REAL,
                               Tst2_30
                               REAL,
                               Tst2_31
                               REAL,
                               Tst2_32
                               REAL,
                               Tst2_33
                               REAL,
                               Tst2_34
                               REAL,
                               Tst2_35
                               REAL,
                               Tst2_36
                               REAL,
                               RANO_POKAZ_2
                               INTEGER,
                               POZDNO_POKAZ_2
                               INTEGER,
                               result_2
                               REAL,
                               SrKvadrOtkl_2
                               REAL,
                               Tst3_1
                               REAL,
                               Tst3_2
                               REAL,
                               Tst3_3
                               REAL,
                               Tst3_4
                               REAL,
                               Tst3_5
                               REAL,
                               Tst3_6
                               REAL,
                               Tst3_7
                               REAL,
       
                                  
                            
                                     
                                       Tst3_8
                            
                                 
                                                       REAL,
                               Tst3_9
                               REAL,
                               Tst3_10
                               REAL,
                               Tst3_11
                               REAL,
                               Tst3_12
                               REAL,


                               Tst3_13


                               REAL,


                               Tst3_15
                               REAL,
                               Tst3_16
                               REAL,
                               Tst3_17
                               REAL,
                               Tst3_18
                               REAL,
                               Tst3_19
                               REAL,
                               Tst3_20
                               REAL,
                               Tst3_21
                               REAL,
                               Tst3_22
                               REAL,
                               Tst3_23
                               REAL,
                               Tst3_24
                               REAL,
                               Tst3_25
                               REAL,
                               Tst3_26
                               REAL,
                               Tst3_27
                               REAL,
                               Tst3_28
                               REAL,
                               Tst3_29
                               REAL,
                               Tst3_30
                               REAL,
                               Tst3_31
                               REAL,
                               Tst3_32
                               REAL,
                               Tst3_33
                               REAL,
                               Tst3_34
                               REAL,
                               Tst3_35
                               REAL,
                               Tst3_36
                               REAL,
                               RANO_POKAZ_3
                               INTEGER,
                               POZDNO_POKAZ_3
                               INTEGER,
                               result_3
                               REAL,
                               SrKvadrOtkl_3
                               REAL,
                               FOREIGN KEY (REG_ID) REFERENCES users (ID)
                               )
                           """)

            conn.commit()
            conn.close()

        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось инициализировать БД: {str(e)}")

    def create_widgets(self):
        """Создание виджетов компонента"""
        # Основной фрейм
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Вкладки для разных типов загрузки
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка Excel/CSV
        self.setup_excel_csv_tab()

        # Вкладка Access
        self.setup_access_tab()

        # Вкладка База данных
        self.setup_database_tab()

    def setup_excel_csv_tab(self):
        """Настройка вкладки Excel/CSV"""
        excel_tab = ttk.Frame(self.notebook)
        self.notebook.add(excel_tab, text="Excel/CSV")

        # Фрейм загрузки данных
        data_frame = ttk.LabelFrame(excel_tab, text="Загрузка данных (рекомендуется Excel для кириллицы)", padding="10")
        data_frame.pack(fill=tk.X, pady=5)

        # Кнопки загрузки Users (только Excel)
        users_frame = ttk.Frame(data_frame)
        users_frame.pack(fill=tk.X, pady=5)

        ttk.Label(users_frame, text="Users (только Excel):", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(users_frame, text="📊 Загрузить Users.xlsx",
                   command=self.load_users_excel).pack(side=tk.LEFT, padx=5)

        # Кнопки загрузки Boxbase (любой формат)
        boxbase_frame = ttk.Frame(data_frame)
        boxbase_frame.pack(fill=tk.X, pady=5)

        ttk.Label(boxbase_frame, text="Boxbase (любой формат):", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(boxbase_frame, text="📁 Загрузить Boxbase",
                   command=self.load_boxbase_any).pack(side=tk.LEFT, padx=5)

        # Кнопки управления
        button_frame = ttk.Frame(data_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="💾 Сохранить в базу",
                   command=self.save_to_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📊 Информация о данных",
                   command=self.show_data_info).pack(side=tk.LEFT, padx=5)

        # Статус загрузки
        self.status_label = ttk.Label(data_frame, text="Данные не загружены", foreground="red")
        self.status_label.pack(pady=5)

        # Информация о базе данных
        self.db_status_label = ttk.Label(data_frame, text="База данных: не создана", foreground="orange")
        self.db_status_label.pack(pady=2)

    def setup_access_tab(self):
        """Настройка вкладки Access"""
        access_tab = ttk.Frame(self.notebook)
        self.notebook.add(access_tab, text="Access")

        # Фрейм загрузки Access
        access_frame = ttk.LabelFrame(access_tab, text="Загрузка из Access базы", padding="10")
        access_frame.pack(fill=tk.X, pady=5)

        # Выбор файла Access
        file_frame = ttk.Frame(access_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Label(file_frame, text="Файл Access:").pack(side=tk.LEFT)
        self.access_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.access_file_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Обзор", command=self.browse_access_file).pack(side=tk.LEFT, padx=5)

        # Кнопки загрузки Access
        button_frame = ttk.Frame(access_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Загрузить Users из Access",
                   command=lambda: self.load_from_access('users')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Загрузить Boxbase из Access",
                   command=lambda: self.load_from_access('boxbase')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Загрузить все из Access",
                   command=lambda: self.load_from_access('both')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Сохранить в SQLite",
                   command=self.save_to_database).pack(side=tk.LEFT, padx=5)

        # Информация о Access
        access_info = ttk.Label(
            access_frame,
            text="✅ Драйверы Access доступны" if self.data_loader.access_drivers_available
            else "❌ Драйверы Access не найдены",
            foreground="green" if self.data_loader.access_drivers_available else "red"
        )
        access_info.pack(pady=5)

    def setup_database_tab(self):
        """Настройка вкладки работы с базой данных"""
        db_tab = ttk.Frame(self.notebook)
        self.notebook.add(db_tab, text="База данных")

        # Фрейм информации о БД
        info_frame = ttk.LabelFrame(db_tab, text="Информация о базе данных", padding="10")
        info_frame.pack(fill=tk.X, pady=5)

        # Кнопки управления БД
        button_frame = ttk.Frame(info_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="🔄 Обновить статистику",
                   command=self.update_db_stats).pack(side=tk.LEFT, padx=5)

        # КНОВКА МИГРАЦИИ В НОВУЮ СХЕМУ
        ttk.Button(button_frame, text="🚀 Миграция в новую схему",
                   command=self.run_migration).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="🗑️ Очистить базу данных",
                   command=self.clear_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📋 Показать структуру",
                   command=self.show_database_structure).pack(side=tk.LEFT, padx=5)

        # Статистика БД
        self.db_stats_frame = ttk.Frame(info_frame)
        self.db_stats_frame.pack(fill=tk.X, pady=5)

        self.update_db_stats()

    def run_migration(self):
        """Запуск миграции в новую схему"""
        if not messagebox.askyesno(
                "Миграция данных",
                "Это ОДНОКРАТНАЯ операция миграции данных в новую схему.\n\n"
                "Новая схема поддерживает:\n"
                "• Анализ нейромедиаторной активности\n"
                "• Расширенную статистику\n"
                "• Подготовку к будущим тестам\n\n"
                "Продолжить?"
        ):
            return

        try:
            # Запускаем миграцию через утилиту
            import subprocess
            import sys
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            migration_script = os.path.join(current_dir, 'utils', 'database_migration.py')

            if os.path.exists(migration_script):
                # Запускаем в отдельном процессе
                subprocess.run([sys.executable, migration_script], check=True)

                # Обновляем статус
                self._check_new_schema()
                self.update_db_stats()

                messagebox.showinfo("Миграция завершена",
                                    "Данные успешно мигрированы в новую схему!\n\n"
                                    "Теперь доступны:\n"
                                    "• Анализ нейромедиаторной активности\n"
                                    "• Расширенные статистические функции\n"
                                    "• Подготовка к будущим тестам")
            else:
                messagebox.showerror("Ошибка", "Скрипт миграции не найден")

        except Exception as e:
            messagebox.showerror("Ошибка миграции", f"Не удалось выполнить миграцию: {e}")

    def load_users_excel(self):
        """Загрузка данных users ТОЛЬКО из Excel"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл Users (Excel)",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self._load_data_thread('users', file_path)

    def load_boxbase_any(self):
        """Загрузка данных boxbase из любого формата"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл Boxbase",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Access files", "*.mdb *.accdb"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.mdb', '.accdb']:
                # Если выбран Access файл для boxbase
                self.access_file_var.set(file_path)
                self.load_from_access('boxbase')
            else:
                # Excel или CSV
                self._load_data_thread('boxbase', file_path)

    def _auto_save_to_database(self):
        """Автоматическое сохранение данных в SQLite базу"""
        try:
            conn = sqlite3.connect(self.db_path)

            if self.users_data is not None:
                self.users_data.to_sql('users', conn, if_exists='replace', index=False)
                print("✅ Users автоматически сохранены в SQLite")

            if self.boxbase_data is not None:
                self.boxbase_data.to_sql('boxbase', conn, if_exists='replace', index=False)
                print("✅ Boxbase автоматически сохранены в SQLite")

            conn.commit()
            conn.close()

            # Обновляем статистику БД
            self.update_db_stats()

            # Показываем уведомление только один раз
            if not self._auto_save_shown:
                messagebox.showinfo("Автосохранение", "Данные автоматически сохранены в базу!")
                self._auto_save_shown = True
            else:
                print("✅ Данные автоматически сохранены в базу")

        except Exception as e:
            print(f"❌ Ошибка автосохранения: {e}")

    def save_to_database(self):
        """Сохранение загруженных данных в SQLite базу"""
        if self.users_data is None and self.boxbase_data is None:
            messagebox.showwarning("Внимание", "Нет данных для сохранения в базу")
            return

        try:
            conn = sqlite3.connect(self.db_path)

            if self.users_data is not None:
                self.users_data.to_sql('users', conn, if_exists='replace', index=False)

            if self.boxbase_data is not None:
                self.boxbase_data.to_sql('boxbase', conn, if_exists='replace', index=False)

            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Данные успешно сохранены в базу!")
            self.update_db_stats()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные в базу: {str(e)}")

    def update_db_stats(self):
        """Обновление статистики базы данных с информацией о схемах"""
        # Очищаем предыдущую статистику
        for widget in self.db_stats_frame.winfo_children():
            widget.destroy()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Информация о схемах
            schema_info = ""

            # Проверяем новую схему
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='patients'")
            new_schema_exists = cursor.fetchone()[0] > 0

            new_patients = 0
            new_tests = 0
            if new_schema_exists:
                cursor.execute("SELECT COUNT(*) FROM patients")
                new_patients = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM visual_tests")
                new_tests = cursor.fetchone()[0]

            # Проверяем старую схему
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users'")
            old_schema_exists = cursor.fetchone()[0] > 0

            old_patients = 0
            old_tests = 0
            if old_schema_exists:
                cursor.execute("SELECT COUNT(*) FROM users")
                old_patients = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM boxbase")
                old_tests = cursor.fetchone()[0]

            conn.close()

            # Формируем информацию
            schema_text = f"""
📊 СТАТУС СХЕМ БАЗЫ ДАННЫХ:

🔹 НОВАЯ СХЕМА (нейромедиаторный анализ):
   • Пациентов: {new_patients}
   • Тестов: {new_tests}
   • Статус: {'✅ активна' if new_patients > 0 else '⚠️ требуется миграция'}

🔸 СТАРАЯ СХЕМА (базовый анализ):
   • Пациентов: {old_patients}
   • Тестов: {old_tests}
   • Статус: {'✅ доступна' if old_schema_exists else '❌ отсутствует'}

💡 РЕКОМЕНДАЦИЯ: {'Используйте новую схему для расширенного анализа' if new_patients > 0 else 'Выполните миграцию для доступа к новым функциям'}
            """.strip()

            stats_label = tk.Label(self.db_stats_frame, text=schema_text, justify=tk.LEFT,
                                   font=("Arial", 9), background='#f0f0f0', relief=tk.RIDGE, padx=10, pady=10)
            stats_label.pack(fill=tk.X, padx=5, pady=5)

        except Exception as e:
            error_label = tk.Label(self.db_stats_frame, text=f"Ошибка загрузки статистики: {str(e)}",
                                   fg="red", justify=tk.LEFT)
            error_label.pack(anchor='w')

    def clear_database(self):
        """Очистка базы данных"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю базу данных?"):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM users")
                cursor.execute("DELETE FROM boxbase")

                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "База данных очищена")
                self.update_db_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить базу: {str(e)}")

    def show_database_structure(self):
        """Показать структуру базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Получаем информацию о таблицах
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            structure_info = "Структура базы данных:\n\n"

            for table in tables:
                table_name = table[0]
                structure_info += f"Таблица: {table_name}\n"

                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                for col in columns:
                    col_name, col_type = col[1], col[2]
                    structure_info += f"  - {col_name} ({col_type})\n"

                structure_info += "\n"

            conn.close()

            # Показываем в отдельном окне
            structure_window = tk.Toplevel(self.parent)
            structure_window.title("Структура базы данных")
            structure_window.geometry("500x400")

            text_widget = tk.Text(structure_window, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(structure_window, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            text_widget.insert("1.0", structure_info)
            text_widget.config(state=tk.DISABLED)

            text_widget.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            scrollbar.pack(side="right", fill="y")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить структуру базы: {str(e)}")

    def browse_access_file(self):
        """Выбор файла Access"""
        filename = filedialog.askopenfilename(
            title="Выберите файл Access",
            filetypes=[("Access files", "*.mdb *.accdb"), ("All files", "*.*")]
        )
        if filename:
            self.access_file_var.set(filename)

    def load_from_access(self, data_type):
        """Загрузка данных из Access"""
        access_file = self.access_file_var.get()
        if not access_file:
            messagebox.showwarning("Внимание", "Выберите файл Access")
            return

        thread = threading.Thread(target=self._load_access_data, args=(data_type, access_file))
        thread.daemon = True
        thread.start()

    def _load_access_data(self, data_type, access_file):
        """Загрузка данных из Access в отдельном потоке"""
        try:
            if data_type == 'users':
                self.users_data = self.data_loader.load_users_from_access(access_file)
                self.parent.after(0, self._on_access_loaded, 'users', access_file)
            elif data_type == 'boxbase':
                self.boxbase_data = self.data_loader.load_boxbase_from_access(access_file)
                self.parent.after(0, self._on_access_loaded, 'boxbase', access_file)
            elif data_type == 'both':
                result = self.data_loader.load_both_from_access(access_file)
                self.users_data = result.get('users')
                self.boxbase_data = result.get('boxbase')
                self.parent.after(0, self._on_access_loaded, 'both', access_file)

        except Exception as e:
            self.parent.after(0, self._on_load_error, f"Access {data_type}: {str(e)}")

    def _on_access_loaded(self, data_type, file_path):
        """Обработка успешной загрузки из Access"""
        self.update_status()

        # АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ В SQLite ПОСЛЕ ЗАГРУЗКИ ИЗ ACCESS
        try:
            self._auto_save_to_database()
        except Exception as e:
            print(f"⚠️ Не удалось автосохранить Access данные: {e}")

        if data_type == 'users':
            messagebox.showinfo("Успех", f"Users загружены из Access: {len(self.users_data)} строк")
            self.on_data_loaded('users', file_path, self.users_data)
        elif data_type == 'boxbase':
            messagebox.showinfo("Успех", f"Boxbase загружены из Access: {len(self.boxbase_data)} строк")
            self.on_data_loaded('boxbase', file_path, self.boxbase_data)
        elif data_type == 'both':
            users_count = len(self.users_data) if self.users_data is not None else 0
            boxbase_count = len(self.boxbase_data) if self.boxbase_data is not None else 0
            messagebox.showinfo("Успех",
                                f"Загружено из Access: Users={users_count} строк, Boxbase={boxbase_count} строк")
            if self.users_data is not None:
                self.on_data_loaded('users', file_path, self.users_data)
            if self.boxbase_data is not None:
                self.on_data_loaded('boxbase', file_path, self.boxbase_data)

    def _load_data_thread(self, data_type, file_path):
        """Загрузка данных в отдельном потоке"""
        thread = threading.Thread(target=self._load_data, args=(data_type, file_path))
        thread.daemon = True
        thread.start()

    def _load_data(self, data_type, file_path):
        """Загрузка данных"""
        try:
            if data_type == 'users':
                self.users_data = self.data_loader.load_users_data(file_path)
            else:
                self.boxbase_data = self.data_loader.load_boxbase_data(file_path)

            self.parent.after(0, self._on_data_loaded, data_type, file_path)

        except Exception as e:
            self.parent.after(0, self._on_load_error, f"{data_type}: {str(e)}")

    def _on_data_loaded(self, data_type, file_path):
        """Обработка успешной загрузки с автоматическим сохранением в базу"""
        self.update_status()
        data = self.users_data if data_type == 'users' else self.boxbase_data

        # Вызываем callback для основного приложения
        self.on_data_loaded(data_type, file_path, data)

        # АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ В БАЗУ ПОСЛЕ ЗАГРУЗКИ ОБОИХ ФАЙЛОВ
        if self.users_data is not None and self.boxbase_data is not None:
            self._auto_save_to_database()

    def _on_load_error(self, error_msg):
        """Обработка ошибки загрузки"""
        messagebox.showerror("Ошибка загрузки", error_msg)

    def update_status(self):
        """Обновление статуса загрузки"""
        users_loaded = self.users_data is not None
        boxbase_loaded = self.boxbase_data is not None

        users_status = "✅" if users_loaded else "❌"
        boxbase_status = "✅" if boxbase_loaded else "❌"

        status_text = f"Users: {users_status} | Boxbase: {boxbase_status}"
        status_color = "green" if (users_loaded and boxbase_loaded) else "orange"

        self.status_label.config(text=status_text, foreground=status_color)

    def show_data_info(self):
        """Показать информацию о данных"""
        try:
            info = self.data_loader.get_data_info()
            schema_info = "Новая схема: доступна" if info['new_schema_available'] else "Новая схема: недоступна"

            messagebox.showinfo(
                "Информация о данных",
                f"Users: {'Загружены' if info['users_loaded'] else 'Не загружены'}\n"
                f"Boxbase: {'Загружены' if info['boxbase_loaded'] else 'Не загружены'}\n"
                f"Строк Users: {info['users_rows']}\n"
                f"Строк Boxbase: {info['boxbase_rows']}\n"
                f"{schema_info}\n\n"
                f"SQLite база: {'✅ создана' if os.path.exists(self.db_path) else '❌ отсутствует'}"
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить информацию: {e}")

