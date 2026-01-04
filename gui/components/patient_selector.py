# gui/components/patient_selector.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os


class PatientSelector(tk.Frame):
    def __init__(self, parent, db_path="neuro_data.db"):
        super().__init__(parent)
        self.db_path = db_path
        self.selected_patient = None
        self.selected_visits = []
        self.patients_data = {}
        self.all_patients_data = {}
        self.sort_order = "name"
        self.new_schema_available = False
        self.old_schema_available = False
        self.data_loader = None
        self._check_schema()
        self.init_ui()
        self.check_database()

    def set_data_loader(self, data_loader):
        """Устанавливает data_loader для доступа к данным"""
        self.data_loader = data_loader

    def _check_schema(self):
        """Проверяет доступность схем БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visual_tests'")
            self.new_schema_available = cursor.fetchone() is not None

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            self.old_schema_available = cursor.fetchone() is not None

            conn.close()
            print(f"🔍 Схемы БД: новая={self.new_schema_available}, старая={self.old_schema_available}")
        except:
            self.new_schema_available = False
            self.old_schema_available = False

    def init_ui(self):
        """Инициализация интерфейса"""
        self.notebook = ttk.Notebook(self)

        self.single_frame = ttk.Frame(self.notebook)
        self.create_single_tab()

        self.compare_frame = ttk.Frame(self.notebook)
        self.create_compare_tab()

        self.group_frame = ttk.Frame(self.notebook)
        self.create_group_tab()

        self.notebook.add(self.single_frame, text="Один пациент")
        self.notebook.add(self.compare_frame, text="Сравнение двух")
        self.notebook.add(self.group_frame, text="Групповой анализ")
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

    def create_single_tab(self):
        """Создает вкладку выбора одного пациента"""
        patient_frame = ttk.LabelFrame(self.single_frame, text="Выбор пациента", padding=10)
        patient_frame.pack(fill='x', padx=5, pady=5)

        schema_info = self._get_schema_info()
        schema_label = ttk.Label(patient_frame, text=schema_info, font=("Arial", 9), foreground="blue")
        schema_label.pack(fill='x', pady=5)

        sort_frame = ttk.Frame(patient_frame)
        sort_frame.pack(fill='x', pady=5)

        ttk.Label(sort_frame, text="Сортировка:").pack(side=tk.LEFT)

        self.sort_var = tk.StringVar(value="name")
        ttk.Radiobutton(sort_frame, text="По фамилии", variable=self.sort_var,
                        value="name", command=self.on_sort_changed).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(sort_frame, text="По ID", variable=self.sort_var,
                        value="id", command=self.on_sort_changed).pack(side=tk.LEFT, padx=10)

        search_frame = ttk.Frame(patient_frame)
        search_frame.pack(fill='x', pady=5)

        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_combo = ttk.Combobox(search_frame, textvariable=self.search_var, width=40)
        self.search_combo.pack(side=tk.LEFT, padx=5, pady=5, fill='x', expand=True)

        self.search_combo.bind('<KeyRelease>', self.on_search_keyrelease)
        self.search_combo.bind('<<ComboboxSelected>>', self.on_search_selected)

        ttk.Button(search_frame, text="❌", width=3,
                   command=self.clear_search).pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(patient_frame,
                                   text="Сначала загрузите данные во вкладке '📁 Данные'",
                                   justify='left', anchor='w', fg='gray', wraplength=500)
        self.info_label.pack(fill='x', pady=5)

        visits_frame = ttk.LabelFrame(self.single_frame, text="Посещения и тесты", padding=10)
        visits_frame.pack(fill='both', expand=True, padx=5, pady=5)

        columns = ('date', 'time', 'test_type', 'data_quality')
        self.visits_tree = ttk.Treeview(visits_frame, columns=columns, show='headings', height=10)

        self.visits_tree.heading('date', text='Дата')
        self.visits_tree.heading('time', text='Время')
        self.visits_tree.heading('test_type', text='Тип теста')
        self.visits_tree.heading('data_quality', text='Качество данных')

        self.visits_tree.column('date', width=100)
        self.visits_tree.column('time', width=80)
        self.visits_tree.column('test_type', width=150)
        self.visits_tree.column('data_quality', width=100)

        scrollbar = ttk.Scrollbar(visits_frame, orient='vertical', command=self.visits_tree.yview)
        self.visits_tree.configure(yscrollcommand=scrollbar.set)

        self.visits_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Добавляем Label для отображения статуса загрузки посещений
        self.visits_status_label = tk.Label(visits_frame, text="Выберите пациента для загрузки посещений",
                                            justify='left', anchor='w', fg='gray', wraplength=400)
        self.visits_status_label.pack(fill='x', padx=5, pady=5)

        button_frame = ttk.Frame(self.single_frame)
        button_frame.pack(fill='x', padx=5, pady=5)

        self.select_button = ttk.Button(button_frame, text="Выбрать для анализа",
                                        state='disabled', command=self.on_select_patient)
        self.select_button.pack(side='right', padx=5)

        self.refresh_button = ttk.Button(button_frame, text="Обновить данные",
                                         command=self.refresh_data)
        self.refresh_button.pack(side='right', padx=5)

    def on_select_patient(self):
        """Обработчик выбора пациента для анализа"""
        try:
            if not self.selected_patient:
                messagebox.showwarning("Внимание", "Сначала выберите пациента из списка")
                return

            patient_id = self.selected_patient['id']
            original_id = self.selected_patient.get('external_id', patient_id)
            print(f"🎯 Выбран пациент для анализа: ID={patient_id}, Original ID={original_id}")

            messagebox.showinfo("Выбор пациента",
                                f"Пациент выбран для анализа.\n\n"
                                f"ID в системе: {patient_id}\n"
                                f"Исходный ID: {original_id}\n\n"
                                f"Данные будут использоваться в модулях анализа СЗР и нейромедиаторов.")

        except Exception as e:
            print(f"❌ Ошибка при выборе пациента: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Не удалось выбрать пациента: {e}")

    def _get_schema_info(self):
        """Получает информацию о доступной схеме БД"""
        if self.new_schema_available:
            return "✅ Используется новая схема (нейромедиаторный анализ)"
        elif self.old_schema_available:
            return "🔸 Используется старая схема (базовый анализ)"
        else:
            return "❌ База данных не найдена"

    def create_compare_tab(self):
        """Создает вкладку сравнения двух пациентов"""
        main_frame = ttk.Frame(self.compare_frame)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        title_label = tk.Label(main_frame, text="Сравнение двух пациентов",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        schema_info = self._get_schema_info()
        schema_label = tk.Label(main_frame, text=schema_info, fg='blue')
        schema_label.pack(pady=5)

        instruction_label = tk.Label(main_frame,
                                     text="Для сравнения двух пациентов загрузите данные во вкладке '📁 Данные'",
                                     justify='center', fg='gray', wraplength=400)
        instruction_label.pack(pady=10)

    def create_group_tab(self):
        """Создает вкладку группового анализа"""
        main_frame = ttk.Frame(self.group_frame)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        title_label = tk.Label(main_frame, text="Групповой анализ",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        schema_info = self._get_schema_info()
        schema_label = tk.Label(main_frame, text=schema_info, fg='blue')
        schema_label.pack(pady=5)

        instruction_label = tk.Label(main_frame,
                                     text="Для группового анализа загрузите данные во вкладке '📁 Данные'",
                                     justify='center', fg='gray', wraplength=400)
        instruction_label.pack(pady=10)

    def on_search_keyrelease(self, event):
        """Обработка ввода в поле поиска"""
        search_text = self.search_var.get().strip()

        if not search_text:
            self.clear_patient_data()
            self.update_search_results(list(self.all_patients_data.keys()))
            return

        matches = []
        search_lower = search_text.lower()

        for display_name, patient_data in self.all_patients_data.items():
            # Поиск по исходному ID (external_id) - точное совпадение
            original_id = str(patient_data.get('external_id', ''))
            if search_text.isdigit() and search_text == original_id:
                matches.append(display_name)
                continue

            # Поиск по фамилии, имени, отчеству - частичное совпадение
            if (search_lower in patient_data.get('lname', '').lower() or
                    search_lower in patient_data.get('fname', '').lower() or
                    search_lower in patient_data.get('sname', '').lower() or
                    search_lower in display_name.lower()):
                matches.append(display_name)

        if self.sort_order == "name":
            matches.sort()
        else:
            matches.sort(key=lambda x: self.all_patients_data[x].get('external_id', 0))

        self.update_search_results(matches)

        # Автоматически выбираем пациента если найден точный ID
        if search_text.isdigit() and len(matches) == 1:
            single_match = matches[0]
            patient_data = self.all_patients_data[single_match]
            if str(patient_data.get('external_id', '')) == search_text:
                self.search_combo.set(single_match)
                self.on_search_selected()
                return

        # Если введены только цифры, но точного совпадения нет, показываем всех пациентов
        if search_text.isdigit() and not matches:
            self.update_search_results(list(self.all_patients_data.keys()))

    def update_search_results(self, matches):
        """Обновляет результаты поиска в комбобоксе"""
        if matches:
            self.search_combo['values'] = matches
            # Если есть только один результат, автоматически выбираем его
            if len(matches) == 1:
                self.search_combo.set(matches[0])
                self.on_search_selected()
        else:
            self.search_combo['values'] = ["Не найдено"]
            self.search_combo.set("Не найдено")
            self.clear_patient_data()

    def on_search_selected(self, event=None):
        """Обработка выбора из результатов поиска"""
        selected_name = self.search_var.get()

        # Если выбрано "Не найдено" или поле пустое, очищаем данные
        if not selected_name or selected_name == "Не найдено":
            self.clear_patient_data()
            return

        if selected_name in self.all_patients_data:
            patient = self.all_patients_data[selected_name]
            self.selected_patient = patient

            # Формируем информационный текст
            info_text = f"ID в системе: {patient['id']}\n"

            original_id = patient.get('external_id', '')
            if original_id:
                info_text += f"Исходный ID: {original_id}\n"

            if 'yborn' in patient and patient['yborn']:
                info_text += f"Год рождения: {patient['yborn']}\n"

            if 'gender' in patient:
                info_text += f"Пол: {patient['gender']}\n"

            if 'fname' in patient or 'lname' in patient:
                name_parts = []
                if 'lname' in patient:
                    name_parts.append(patient['lname'])
                if 'fname' in patient:
                    name_parts.append(patient['fname'])
                if 'sname' in patient:
                    name_parts.append(patient['sname'])

                if name_parts:
                    info_text += f"ФИО: {' '.join(name_parts)}"

            self.info_label.config(text=info_text)

            original_id = patient.get('external_id', 'N/A')
            print(f"🔍 Выбран пациент: ID={patient['id']}, Исходный ID={original_id}")

            # Загружаем посещения используя исходный ID
            self.load_patient_visits(patient['id'], original_id)

            self.select_button.config(state='normal')
        else:
            self.clear_patient_data()

    def clear_patient_data(self):
        """Очищает все данные о пациенте и посещениях"""
        self.selected_patient = None
        self.info_label.config(text="Сначала загрузите данные во вкладке '📁 Данные'", fg='gray')
        self.select_button.config(state='disabled')
        self.visits_status_label.config(text="Выберите пациента для загрузки посещений", fg='gray')

        # Очищаем дерево посещений
        for item in self.visits_tree.get_children():
            self.visits_tree.delete(item)

    def clear_search(self):
        """Очищает поле поиска и все связанные данные"""
        self.search_var.set("")
        self.update_search_results(list(self.all_patients_data.keys()))
        self.clear_patient_data()

    def on_sort_changed(self):
        """Обработка изменения сортировки"""
        self.sort_order = self.sort_var.get()
        current_search = self.search_var.get()
        if current_search:
            self.on_search_keyrelease(None)
        else:
            self.load_patients()

    def check_database(self):
        """Проверяет наличие БД и загружает данные если есть"""
        if os.path.exists(self.db_path):
            self.load_patients()
        else:
            self.show_no_database_message()

    def show_no_database_message(self):
        """Показывает сообщение об отсутствии БД"""
        message = """
База данных не найдена!

Для работы с пациентами:

1. Перейдите во вкладку '📁 Данные'
2. Загрузите файлы users.xlsx и boxbase.xlsx
3. Данные автоматически сохранятся в базу
4. Вернитесь в эту вкладку

Рекомендация: используйте Excel (.xlsx) для сохранения кириллицы!
"""
        for widget in self.single_frame.winfo_children():
            widget.destroy()

        info_label = tk.Label(self.single_frame, text=message,
                              justify='left', fg='blue', wraplength=500, font=("Arial", 10))
        info_label.pack(padx=20, pady=20)

    def refresh_data(self):
        """Обновляет данные из БД"""
        if os.path.exists(self.db_path):
            self._check_schema()
            success = self.load_patients()
            if success:
                messagebox.showinfo("Обновление", "Данные пациентов обновлены!")
                return True
        else:
            messagebox.showwarning("Внимание", "База данных еще не создана!")
            return False

    def load_patients(self):
        """Загрузка списка пациентов с поддержкой обеих схем"""
        if self.new_schema_available:
            return self._load_patients_new_schema()
        elif self.old_schema_available:
            return self._load_patients_old_schema()
        else:
            self.show_no_database_message()
            return False

    def _load_patients_new_schema(self):
        """Загрузка пациентов из новой схемы"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(patients)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            if 'external_id' in column_names:
                cursor.execute("""
                               SELECT id, external_id, fname, sname, lname, yborn, gender
                               FROM patients
                               ORDER BY lname, fname
                               """)
            else:
                cursor.execute("""
                               SELECT id, id as external_id, fname, sname, lname, yborn, gender
                               FROM patients
                               ORDER BY lname, fname
                               """)

            patients = cursor.fetchall()

            self.patients_data = {}
            self.all_patients_data = {}
            patient_names = []

            for patient in patients:
                patient_dict = {
                    'id': patient[0],
                    'external_id': patient[1],
                    'fname': patient[2] or '',
                    'sname': patient[3] or '',
                    'lname': patient[4] or '',
                    'yborn': patient[5],
                    'gender': 'Мужской' if patient[6] == 1 else 'Женский'
                }

                display_name = self._format_patient_display_name(patient_dict)
                patient_names.append(display_name)
                self.patients_data[display_name] = patient_dict
                self.all_patients_data[display_name] = patient_dict

            self.search_combo['values'] = patient_names
            if patient_names:
                self.search_combo.set("")

            self.info_label.config(text=f"Новая схема БД | Введите ID, фамилию или имя для поиска", fg='black')
            conn.close()
            print(f"✅ Загружено {len(patient_names)} пациентов из новой схемы")
            return True

        except Exception as e:
            print(f"Ошибка загрузки пациентов из новой схемы: {e}")
            return self._load_patients_old_schema()

    def _load_patients_old_schema(self):
        """Загрузка пациентов из старой схемы"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                conn.close()
                self.show_no_database_message()
                return False

            cursor.execute("PRAGMA table_info(users)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            print(f"🔍 Столбцы в таблице users: {column_names}")

            select_columns = []
            if 'FName' in column_names:
                select_columns.append('FName')
            if 'SName' in column_names:
                select_columns.append('SName')
            if 'LName' in column_names:
                select_columns.append('LName')
            if 'YBorn' in column_names:
                select_columns.append('YBorn')
            if 'Gender' in column_names:
                select_columns.append('Gender')

            select_columns.insert(0, 'ID')
            if 'Active' in column_names:
                select_columns.append('Active')

            select_str = ', '.join(select_columns)

            if self.sort_order == "name" and 'LName' in column_names and 'FName' in column_names:
                order_clause = "ORDER BY LName, FName, SName"
                sort_info = " (сортировка по фамилии)"
            else:
                order_clause = "ORDER BY ID"
                sort_info = " (сортировка по ID)"

            query = f"SELECT {select_str} FROM users WHERE Active = 1 {order_clause}"

            cursor.execute(query)
            patients = cursor.fetchall()
            self.patients_data = {}
            self.all_patients_data = {}

            patient_names = []

            for patient in patients:
                patient_dict = {
                    'id': patient[0],
                    'external_id': patient[0],  # В старой схеме ID = external_id
                    'original_id': patient[0]  # Сохраняем исходный ID
                }

                col_index = 1
                if 'FName' in column_names and col_index < len(patient):
                    patient_dict['fname'] = patient[col_index]
                    col_index += 1
                if 'SName' in column_names and col_index < len(patient):
                    patient_dict['sname'] = patient[col_index]
                    col_index += 1
                if 'LName' in column_names and col_index < len(patient):
                    patient_dict['lname'] = patient[col_index]
                    col_index += 1
                if 'YBorn' in column_names and col_index < len(patient):
                    patient_dict['yborn'] = patient[col_index]
                    col_index += 1
                if 'Gender' in column_names and col_index < len(patient):
                    patient_dict['gender'] = 'Мужской' if patient[col_index] == 1 else 'Женский'

                display_name = self._format_patient_display_name(patient_dict)
                patient_names.append(display_name)
                self.patients_data[display_name] = patient_dict
                self.all_patients_data[display_name] = patient_dict

            self.search_combo['values'] = patient_names
            if patient_names:
                self.search_combo.set("")

            self.info_label.config(text=f"Введите ID, фамилию или имя для поиска{sort_info}", fg='black')

            conn.close()
            print(f"✅ Загружено {len(patient_names)} пациентов из старой схемы")
            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки пациентов из старой схемы: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить пациентов: {e}")
            return False

    def _format_patient_display_name(self, patient_dict):
        """Форматирует отображаемое имя пациента"""
        name_parts = []
        if patient_dict.get('lname'):
            name_parts.append(patient_dict['lname'])
        if patient_dict.get('fname'):
            name_parts.append(patient_dict['fname'])
        if patient_dict.get('sname'):
            name_parts.append(patient_dict['sname'])

        display_name = ' '.join(name_parts) if name_parts else f"Пациент"

        # Добавляем исходный ID для поиска
        original_id = patient_dict.get('external_id', patient_dict.get('id'))
        display_name += f" (ID: {original_id})"

        return display_name

    def load_patient_visits(self, patient_id, original_id=None):
        """Загружает посещения и тесты выбранного пациента"""
        try:
            # Очищаем предыдущие данные
            for item in self.visits_tree.get_children():
                self.visits_tree.delete(item)

            # Обновляем статус загрузки
            self.visits_status_label.config(text="Загрузка посещений...", fg='blue')

            # Всегда используем исходный ID для поиска в boxbase
            search_id = original_id if original_id else patient_id

            if self.new_schema_available:
                visits_count = self._load_visits_new_schema(patient_id, search_id)
            else:
                visits_count = self._load_visits_old_schema(search_id)

            # Обновляем статус в GUI
            if visits_count > 0:
                self.visits_status_label.config(text=f"✅ Загружено {visits_count} посещений", fg='green')
            else:
                self.visits_status_label.config(
                    text=f"❌ Для пациента с ID {search_id} не найдено посещений\n"
                         f"Проверьте соответствие ID в данных тестирования",
                    fg='red'
                )

        except Exception as e:
            error_msg = f"❌ Ошибка загрузки посещений: {e}"
            print(error_msg)
            self.visits_status_label.config(text=error_msg, fg='red')
            import traceback
            traceback.print_exc()

    def _load_visits_new_schema(self, patient_id, original_id):
        """Загружает посещения из новой схемы"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Сначала проверим структуру таблицы testing_sessions
            cursor.execute("PRAGMA table_info(testing_sessions)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            print(f"🔍 Столбцы testing_sessions: {column_names}")

            # Проверим есть ли данные для этого пациента в testing_sessions
            cursor.execute("SELECT COUNT(*) FROM testing_sessions WHERE patient_id = ?", (patient_id,))
            count_new = cursor.fetchone()[0]

            # Проверим есть ли данные в boxbase по исходному ID
            cursor.execute("SELECT COUNT(*) FROM boxbase WHERE REG_ID = ?", (original_id,))
            count_old = cursor.fetchone()[0]

            print(f"🔍 Данные для пациента: testing_sessions={count_new}, boxbase={count_old}")

            visits = []

            # Пробуем загрузить из testing_sessions
            if count_new > 0 and 'session_date' in column_names and 'session_time' in column_names:
                cursor.execute("""
                               SELECT session_date,
                                      session_time,
                                      'Комплексный тест СЗР'                                      as test_type,
                                      CASE WHEN validity = 1 THEN 'Пригодно' ELSE 'Проверить' END as data_quality
                               FROM testing_sessions
                               WHERE patient_id = ?
                               ORDER BY session_date DESC, session_time DESC
                               """, (patient_id,))
                visits = cursor.fetchall()
                print(f"✅ Загружено {len(visits)} посещений из testing_sessions")

            # Если в testing_sessions нет данных, загружаем из boxbase
            if not visits and count_old > 0:
                cursor.execute("""
                               SELECT CurrentDate,
                                      CurrentTime,
                                      'Комплексный тест СЗР',
                                      CASE WHEN VidSost = 1 THEN 'Пригодно' ELSE 'Проверить' END
                               FROM boxbase
                               WHERE REG_ID = ?
                               ORDER BY CurrentDate DESC, CurrentTime DESC
                               """, (original_id,))
                visits = cursor.fetchall()
                print(f"✅ Загружено {len(visits)} посещений из boxbase")

            for visit in visits:
                self.visits_tree.insert('', 'end', values=visit)

            conn.close()
            return len(visits)

        except Exception as e:
            print(f"❌ Ошибка загрузки посещений из новой схемы: {e}")
            return 0

    def _load_visits_old_schema(self, original_id):
        """Загружает посещения из старой схемы"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM boxbase WHERE REG_ID = ?", (original_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                print(f"⚠️  Для пациента с ID {original_id} нет данных в boxbase")
                return 0

            cursor.execute("""
                           SELECT CurrentDate,
                                  CurrentTime,
                                  'Комплексный тест СЗР',
                                  CASE WHEN VidSost = 1 THEN 'Пригодно' ELSE 'Проверить' END
                           FROM boxbase
                           WHERE REG_ID = ?
                           ORDER BY CurrentDate DESC, CurrentTime DESC
                           """, (original_id,))

            visits = cursor.fetchall()

            for visit in visits:
                self.visits_tree.insert('', 'end', values=visit)

            conn.close()
            print(f"✅ Загружено {len(visits)} посещений из boxbase для пациента ID={original_id}")
            return len(visits)

        except Exception as e:
            print(f"❌ Ошибка загрузки посещений из старой схемы: {e}")
            return 0

    def get_selected_patient(self):
        """Возвращает выбранного пациента"""
        return self.selected_patient

    def get_selected_visits(self):
        """Возвращает выбранные посещения"""
        return self.selected_visits


# # gui/components/patient_selector.py
# import tkinter as tk
# from tkinter import ttk, messagebox
# import sqlite3
# from datetime import datetime
# import os
#
#
# class PatientSelector(tk.Frame):
#     def __init__(self, parent, db_path="neuro_data.db"):
#         super().__init__(parent)
#         self.db_path = db_path
#         self.selected_patient = None
#         self.selected_visits = []
#         self.patients_data = {}
#         self.all_patients_data = {}
#         self.sort_order = "name"
#         self.new_schema_available = False
#         self.old_schema_available = False
#         self.data_loader = None
#         self._check_schema()
#         self.init_ui()
#         self.check_database()
#
#     def set_data_loader(self, data_loader):
#         """Устанавливает data_loader для доступа к данным"""
#         self.data_loader = data_loader
#
#     def _check_schema(self):
#         """Проверяет доступность схем БД"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visual_tests'")
#             self.new_schema_available = cursor.fetchone() is not None
#
#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
#             self.old_schema_available = cursor.fetchone() is not None
#
#             conn.close()
#             print(f"🔍 Схемы БД: новая={self.new_schema_available}, старая={self.old_schema_available}")
#         except:
#             self.new_schema_available = False
#             self.old_schema_available = False
#
#     def init_ui(self):
#         """Инициализация интерфейса"""
#         self.notebook = ttk.Notebook(self)
#
#         self.single_frame = ttk.Frame(self.notebook)
#         self.create_single_tab()
#
#         self.compare_frame = ttk.Frame(self.notebook)
#         self.create_compare_tab()
#
#         self.group_frame = ttk.Frame(self.notebook)
#         self.create_group_tab()
#
#         self.notebook.add(self.single_frame, text="Один пациент")
#         self.notebook.add(self.compare_frame, text="Сравнение двух")
#         self.notebook.add(self.group_frame, text="Групповой анализ")
#         self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
#
#     def create_single_tab(self):
#         """Создает вкладку выбора одного пациента"""
#         patient_frame = ttk.LabelFrame(self.single_frame, text="Выбор пациента", padding=10)
#         patient_frame.pack(fill='x', padx=5, pady=5)
#
#         schema_info = self._get_schema_info()
#         schema_label = ttk.Label(patient_frame, text=schema_info, font=("Arial", 9), foreground="blue")
#         schema_label.pack(fill='x', pady=5)
#
#         sort_frame = ttk.Frame(patient_frame)
#         sort_frame.pack(fill='x', pady=5)
#
#         ttk.Label(sort_frame, text="Сортировка:").pack(side=tk.LEFT)
#
#         self.sort_var = tk.StringVar(value="name")
#         ttk.Radiobutton(sort_frame, text="По фамилии", variable=self.sort_var,
#                         value="name", command=self.on_sort_changed).pack(side=tk.LEFT, padx=10)
#         ttk.Radiobutton(sort_frame, text="По ID", variable=self.sort_var,
#                         value="id", command=self.on_sort_changed).pack(side=tk.LEFT, padx=10)
#
#         search_frame = ttk.Frame(patient_frame)
#         search_frame.pack(fill='x', pady=5)
#
#         ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
#
#         self.search_var = tk.StringVar()
#         self.search_combo = ttk.Combobox(search_frame, textvariable=self.search_var, width=40)
#         self.search_combo.pack(side=tk.LEFT, padx=5, pady=5, fill='x', expand=True)
#
#         self.search_combo.bind('<KeyRelease>', self.on_search_keyrelease)
#         self.search_combo.bind('<<ComboboxSelected>>', self.on_search_selected)
#
#         ttk.Button(search_frame, text="❌", width=3,
#                    command=self.clear_search).pack(side=tk.LEFT, padx=5)
#
#         self.info_label = tk.Label(patient_frame,
#                                    text="Сначала загрузите данные во вкладке '📁 Данные'",
#                                    justify='left', anchor='w', fg='gray', wraplength=500)
#         self.info_label.pack(fill='x', pady=5)
#
#         visits_frame = ttk.LabelFrame(self.single_frame, text="Посещения и тесты", padding=10)
#         visits_frame.pack(fill='both', expand=True, padx=5, pady=5)
#
#         columns = ('date', 'time', 'test_type', 'data_quality')
#         self.visits_tree = ttk.Treeview(visits_frame, columns=columns, show='headings', height=10)
#
#         self.visits_tree.heading('date', text='Дата')
#         self.visits_tree.heading('time', text='Время')
#         self.visits_tree.heading('test_type', text='Тип теста')
#         self.visits_tree.heading('data_quality', text='Качество данных')
#
#         self.visits_tree.column('date', width=100)
#         self.visits_tree.column('time', width=80)
#         self.visits_tree.column('test_type', width=150)
#         self.visits_tree.column('data_quality', width=100)
#
#         scrollbar = ttk.Scrollbar(visits_frame, orient='vertical', command=self.visits_tree.yview)
#         self.visits_tree.configure(yscrollcommand=scrollbar.set)
#
#         self.visits_tree.pack(side='left', fill='both', expand=True)
#         scrollbar.pack(side='right', fill='y')
#
#         # Добавляем Label для отображения статуса загрузки посещений
#         self.visits_status_label = tk.Label(visits_frame, text="Выберите пациента для загрузки посещений",
#                                             justify='left', anchor='w', fg='gray', wraplength=400)
#         self.visits_status_label.pack(fill='x', padx=5, pady=5)
#
#         button_frame = ttk.Frame(self.single_frame)
#         button_frame.pack(fill='x', padx=5, pady=5)
#
#         self.select_button = ttk.Button(button_frame, text="Выбрать для анализа",
#                                         state='disabled', command=self.on_select_patient)
#         self.select_button.pack(side='right', padx=5)
#
#         self.refresh_button = ttk.Button(button_frame, text="Обновить данные",
#                                          command=self.refresh_data)
#         self.refresh_button.pack(side='right', padx=5)
#
#     def on_select_patient(self):
#         """Обработчик выбора пациента для анализа"""
#         try:
#             if not self.selected_patient:
#                 messagebox.showwarning("Внимание", "Сначала выберите пациента из списка")
#                 return
#
#             patient_id = self.selected_patient['id']
#             original_id = self.selected_patient.get('external_id', patient_id)
#             print(f"🎯 Выбран пациент для анализа: ID={patient_id}, Original ID={original_id}")
#
#             messagebox.showinfo("Выбор пациента",
#                                 f"Пациент выбран для анализа.\n\n"
#                                 f"ID в системе: {patient_id}\n"
#                                 f"Исходный ID: {original_id}\n\n"
#                                 f"Данные будут использоваться в модулях анализа СЗР и нейромедиаторов.")
#
#         except Exception as e:
#             print(f"❌ Ошибка при выборе пациента: {e}")
#             import traceback
#             traceback.print_exc()
#             messagebox.showerror("Ошибка", f"Не удалось выбрать пациента: {e}")
#
#     def _get_schema_info(self):
#         """Получает информацию о доступной схеме БД"""
#         if self.new_schema_available:
#             return "✅ Используется новая схема (нейромедиаторный анализ)"
#         elif self.old_schema_available:
#             return "🔸 Используется старая схема (базовый анализ)"
#         else:
#             return "❌ База данных не найдена"
#
#     def create_compare_tab(self):
#         """Создает вкладку сравнения двух пациентов"""
#         main_frame = ttk.Frame(self.compare_frame)
#         main_frame.pack(expand=True, fill='both', padx=20, pady=20)
#
#         title_label = tk.Label(main_frame, text="Сравнение двух пациентов",
#                                font=("Arial", 14, "bold"))
#         title_label.pack(pady=10)
#
#         schema_info = self._get_schema_info()
#         schema_label = tk.Label(main_frame, text=schema_info, fg='blue')
#         schema_label.pack(pady=5)
#
#         instruction_label = tk.Label(main_frame,
#                                      text="Для сравнения двух пациентов загрузите данные во вкладке '📁 Данные'",
#                                      justify='center', fg='gray', wraplength=400)
#         instruction_label.pack(pady=10)
#
#     def create_group_tab(self):
#         """Создает вкладку группового анализа"""
#         main_frame = ttk.Frame(self.group_frame)
#         main_frame.pack(expand=True, fill='both', padx=20, pady=20)
#
#         title_label = tk.Label(main_frame, text="Групповой анализ",
#                                font=("Arial", 14, "bold"))
#         title_label.pack(pady=10)
#
#         schema_info = self._get_schema_info()
#         schema_label = tk.Label(main_frame, text=schema_info, fg='blue')
#         schema_label.pack(pady=5)
#
#         instruction_label = tk.Label(main_frame,
#                                      text="Для группового анализа загрузите данные во вкладке '📁 Данные'",
#                                      justify='center', fg='gray', wraplength=400)
#         instruction_label.pack(pady=10)
#
#     def on_search_keyrelease(self, event):
#         """Обработка ввода в поле поиска"""
#         search_text = self.search_var.get().strip()
#
#         if not search_text:
#             self.clear_patient_data()
#             self.update_search_results(list(self.all_patients_data.keys()))
#             return
#
#         matches = []
#         search_lower = search_text.lower()
#
#         for display_name, patient_data in self.all_patients_data.items():
#             # Поиск по исходному ID (external_id) - точное совпадение
#             original_id = str(patient_data.get('external_id', ''))
#             if search_text.isdigit() and search_text == original_id:
#                 matches.append(display_name)
#                 continue
#
#             # Поиск по фамилии, имени, отчеству - частичное совпадение
#             if (search_lower in patient_data.get('lname', '').lower() or
#                     search_lower in patient_data.get('fname', '').lower() or
#                     search_lower in patient_data.get('sname', '').lower() or
#                     search_lower in display_name.lower()):
#                 matches.append(display_name)
#
#         if self.sort_order == "name":
#             matches.sort()
#         else:
#             matches.sort(key=lambda x: self.all_patients_data[x].get('external_id', 0))
#
#         self.update_search_results(matches)
#
#         # Если найден только один пациент и это точное совпадение по ID, автоматически выбираем его
#         if len(matches) == 1 and search_text.isdigit():
#             single_match = matches[0]
#             patient_data = self.all_patients_data[single_match]
#             if str(patient_data.get('external_id', '')) == search_text:
#                 self.search_combo.set(single_match)
#                 self.on_search_selected()
#
#     def update_search_results(self, matches):
#         """Обновляет результаты поиска в комбобоксе"""
#         if matches:
#             self.search_combo['values'] = matches
#         else:
#             self.search_combo['values'] = ["Не найдено"]
#             self.search_combo.set("Не найдено")
#
#     def on_search_selected(self, event=None):
#         """Обработка выбора из результатов поиска"""
#         selected_name = self.search_var.get()
#
#         # Если выбрано "Не найдено" или поле пустое, очищаем данные
#         if not selected_name or selected_name == "Не найдено":
#             self.clear_patient_data()
#             return
#
#         if selected_name in self.all_patients_data:
#             patient = self.all_patients_data[selected_name]
#             self.selected_patient = patient
#
#             # Формируем информационный текст
#             info_text = f"ID в системе: {patient['id']}\n"
#
#             original_id = patient.get('external_id', '')
#             if original_id:
#                 info_text += f"Исходный ID: {original_id}\n"
#
#             if 'yborn' in patient and patient['yborn']:
#                 info_text += f"Год рождения: {patient['yborn']}\n"
#
#             if 'gender' in patient:
#                 info_text += f"Пол: {patient['gender']}\n"
#
#             if 'fname' in patient or 'lname' in patient:
#                 name_parts = []
#                 if 'lname' in patient:
#                     name_parts.append(patient['lname'])
#                 if 'fname' in patient:
#                     name_parts.append(patient['fname'])
#                 if 'sname' in patient:
#                     name_parts.append(patient['sname'])
#
#                 if name_parts:
#                     info_text += f"ФИО: {' '.join(name_parts)}"
#
#             self.info_label.config(text=info_text)
#
#             original_id = patient.get('external_id', 'N/A')
#             print(f"🔍 Выбран пациент: ID={patient['id']}, Исходный ID={original_id}")
#
#             # Загружаем посещения используя исходный ID
#             self.load_patient_visits(patient['id'], original_id)
#
#             self.select_button.config(state='normal')
#         else:
#             self.clear_patient_data()
#
#     def clear_patient_data(self):
#         """Очищает все данные о пациенте и посещениях"""
#         self.selected_patient = None
#         self.info_label.config(text="Сначала загрузите данные во вкладке '📁 Данные'", fg='gray')
#         self.select_button.config(state='disabled')
#         self.visits_status_label.config(text="Выберите пациента для загрузки посещений", fg='gray')
#
#         # Очищаем дерево посещений
#         for item in self.visits_tree.get_children():
#             self.visits_tree.delete(item)
#
#     def clear_search(self):
#         """Очищает поле поиска и все связанные данные"""
#         self.search_var.set("")
#         self.update_search_results(list(self.all_patients_data.keys()))
#         self.clear_patient_data()
#
#     def on_sort_changed(self):
#         """Обработка изменения сортировки"""
#         self.sort_order = self.sort_var.get()
#         current_search = self.search_var.get()
#         if current_search:
#             self.on_search_keyrelease(None)
#         else:
#             self.load_patients()
#
#     def check_database(self):
#         """Проверяет наличие БД и загружает данные если есть"""
#         if os.path.exists(self.db_path):
#             self.load_patients()
#         else:
#             self.show_no_database_message()
#
#     def show_no_database_message(self):
#         """Показывает сообщение об отсутствии БД"""
#         message = """
# База данных не найдена!
#
# Для работы с пациентами:
#
# 1. Перейдите во вкладку '📁 Данные'
# 2. Загрузите файлы users.xlsx и boxbase.xlsx
# 3. Данные автоматически сохранятся в базу
# 4. Вернитесь в эту вкладку
#
# Рекомендация: используйте Excel (.xlsx) для сохранения кириллицы!
# """
#         for widget in self.single_frame.winfo_children():
#             widget.destroy()
#
#         info_label = tk.Label(self.single_frame, text=message,
#                               justify='left', fg='blue', wraplength=500, font=("Arial", 10))
#         info_label.pack(padx=20, pady=20)
#
#     def refresh_data(self):
#         """Обновляет данные из БД"""
#         if os.path.exists(self.db_path):
#             self._check_schema()
#             success = self.load_patients()
#             if success:
#                 messagebox.showinfo("Обновление", "Данные пациентов обновлены!")
#                 return True
#         else:
#             messagebox.showwarning("Внимание", "База данных еще не создана!")
#             return False
#
#     def load_patients(self):
#         """Загрузка списка пациентов с поддержкой обеих схем"""
#         if self.new_schema_available:
#             return self._load_patients_new_schema()
#         elif self.old_schema_available:
#             return self._load_patients_old_schema()
#         else:
#             self.show_no_database_message()
#             return False
#
#     def _load_patients_new_schema(self):
#         """Загрузка пациентов из новой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("PRAGMA table_info(patients)")
#             columns_info = cursor.fetchall()
#             column_names = [col[1] for col in columns_info]
#
#             if 'external_id' in column_names:
#                 cursor.execute("""
#                                SELECT id, external_id, fname, sname, lname, yborn, gender
#                                FROM patients
#                                ORDER BY lname, fname
#                                """)
#             else:
#                 cursor.execute("""
#                                SELECT id, id as external_id, fname, sname, lname, yborn, gender
#                                FROM patients
#                                ORDER BY lname, fname
#                                """)
#
#             patients = cursor.fetchall()
#
#             self.patients_data = {}
#             self.all_patients_data = {}
#             patient_names = []
#
#             for patient in patients:
#                 patient_dict = {
#                     'id': patient[0],
#                     'external_id': patient[1],
#                     'fname': patient[2] or '',
#                     'sname': patient[3] or '',
#                     'lname': patient[4] or '',
#                     'yborn': patient[5],
#                     'gender': 'Мужской' if patient[6] == 1 else 'Женский'
#                 }
#
#                 display_name = self._format_patient_display_name(patient_dict)
#                 patient_names.append(display_name)
#                 self.patients_data[display_name] = patient_dict
#                 self.all_patients_data[display_name] = patient_dict
#
#             self.search_combo['values'] = patient_names
#             if patient_names:
#                 self.search_combo.set("")
#
#             self.info_label.config(text=f"Новая схема БД | Введите ID, фамилию или имя для поиска", fg='black')
#             conn.close()
#             print(f"✅ Загружено {len(patient_names)} пациентов из новой схемы")
#             return True
#
#         except Exception as e:
#             print(f"Ошибка загрузки пациентов из новой схемы: {e}")
#             return self._load_patients_old_schema()
#
#     def _load_patients_old_schema(self):
#         """Загрузка пациентов из старой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
#             if not cursor.fetchone():
#                 conn.close()
#                 self.show_no_database_message()
#                 return False
#
#             cursor.execute("PRAGMA table_info(users)")
#             columns_info = cursor.fetchall()
#             column_names = [col[1] for col in columns_info]
#             print(f"🔍 Столбцы в таблице users: {column_names}")
#
#             select_columns = []
#             if 'FName' in column_names:
#                 select_columns.append('FName')
#             if 'SName' in column_names:
#                 select_columns.append('SName')
#             if 'LName' in column_names:
#                 select_columns.append('LName')
#             if 'YBorn' in column_names:
#                 select_columns.append('YBorn')
#             if 'Gender' in column_names:
#                 select_columns.append('Gender')
#
#             select_columns.insert(0, 'ID')
#             if 'Active' in column_names:
#                 select_columns.append('Active')
#
#             select_str = ', '.join(select_columns)
#
#             if self.sort_order == "name" and 'LName' in column_names and 'FName' in column_names:
#                 order_clause = "ORDER BY LName, FName, SName"
#                 sort_info = " (сортировка по фамилии)"
#             else:
#                 order_clause = "ORDER BY ID"
#                 sort_info = " (сортировка по ID)"
#
#             query = f"SELECT {select_str} FROM users WHERE Active = 1 {order_clause}"
#
#             cursor.execute(query)
#             patients = cursor.fetchall()
#             self.patients_data = {}
#             self.all_patients_data = {}
#
#             patient_names = []
#
#             for patient in patients:
#                 patient_dict = {
#                     'id': patient[0],
#                     'external_id': patient[0],  # В старой схеме ID = external_id
#                     'original_id': patient[0]  # Сохраняем исходный ID
#                 }
#
#                 col_index = 1
#                 if 'FName' in column_names and col_index < len(patient):
#                     patient_dict['fname'] = patient[col_index]
#                     col_index += 1
#                 if 'SName' in column_names and col_index < len(patient):
#                     patient_dict['sname'] = patient[col_index]
#                     col_index += 1
#                 if 'LName' in column_names and col_index < len(patient):
#                     patient_dict['lname'] = patient[col_index]
#                     col_index += 1
#                 if 'YBorn' in column_names and col_index < len(patient):
#                     patient_dict['yborn'] = patient[col_index]
#                     col_index += 1
#                 if 'Gender' in column_names and col_index < len(patient):
#                     patient_dict['gender'] = 'Мужской' if patient[col_index] == 1 else 'Женский'
#
#                 display_name = self._format_patient_display_name(patient_dict)
#                 patient_names.append(display_name)
#                 self.patients_data[display_name] = patient_dict
#                 self.all_patients_data[display_name] = patient_dict
#
#             self.search_combo['values'] = patient_names
#             if patient_names:
#                 self.search_combo.set("")
#
#             self.info_label.config(text=f"Введите ID, фамилию или имя для поиска{sort_info}", fg='black')
#
#             conn.close()
#             print(f"✅ Загружено {len(patient_names)} пациентов из старой схемы")
#             return True
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки пациентов из старой схемы: {e}")
#             messagebox.showerror("Ошибка", f"Не удалось загрузить пациентов: {e}")
#             return False
#
#     def _format_patient_display_name(self, patient_dict):
#         """Форматирует отображаемое имя пациента"""
#         name_parts = []
#         if patient_dict.get('lname'):
#             name_parts.append(patient_dict['lname'])
#         if patient_dict.get('fname'):
#             name_parts.append(patient_dict['fname'])
#         if patient_dict.get('sname'):
#             name_parts.append(patient_dict['sname'])
#
#         display_name = ' '.join(name_parts) if name_parts else f"Пациент"
#
#         # Добавляем исходный ID для поиска
#         original_id = patient_dict.get('external_id', patient_dict.get('id'))
#         display_name += f" (ID: {original_id})"
#
#         return display_name
#
#     def load_patient_visits(self, patient_id, original_id=None):
#         """Загружает посещения и тесты выбранного пациента"""
#         try:
#             # Очищаем предыдущие данные
#             for item in self.visits_tree.get_children():
#                 self.visits_tree.delete(item)
#
#             # Обновляем статус загрузки
#             self.visits_status_label.config(text="Загрузка посещений...", fg='blue')
#
#             # Всегда используем исходный ID для поиска в boxbase
#             search_id = original_id if original_id else patient_id
#
#             if self.new_schema_available:
#                 visits_count = self._load_visits_new_schema(patient_id, search_id)
#             else:
#                 visits_count = self._load_visits_old_schema(search_id)
#
#             # Обновляем статус в GUI
#             if visits_count > 0:
#                 self.visits_status_label.config(text=f"✅ Загружено {visits_count} посещений", fg='green')
#             else:
#                 self.visits_status_label.config(
#                     text=f"❌ Для пациента с ID {search_id} не найдено посещений\n"
#                          f"Проверьте соответствие ID в данных тестирования",
#                     fg='red'
#                 )
#
#         except Exception as e:
#             error_msg = f"❌ Ошибка загрузки посещений: {e}"
#             print(error_msg)
#             self.visits_status_label.config(text=error_msg, fg='red')
#             import traceback
#             traceback.print_exc()
#
#     def _load_visits_new_schema(self, patient_id, original_id):
#         """Загружает посещения из новой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             # Сначала проверим структуру таблицы testing_sessions
#             cursor.execute("PRAGMA table_info(testing_sessions)")
#             columns_info = cursor.fetchall()
#             column_names = [col[1] for col in columns_info]
#             print(f"🔍 Столбцы testing_sessions: {column_names}")
#
#             # Проверим есть ли данные для этого пациента в testing_sessions
#             cursor.execute("SELECT COUNT(*) FROM testing_sessions WHERE patient_id = ?", (patient_id,))
#             count_new = cursor.fetchone()[0]
#
#             # Проверим есть ли данные в boxbase по исходному ID
#             cursor.execute("SELECT COUNT(*) FROM boxbase WHERE REG_ID = ?", (original_id,))
#             count_old = cursor.fetchone()[0]
#
#             print(f"🔍 Данные для пациента: testing_sessions={count_new}, boxbase={count_old}")
#
#             visits = []
#
#             # Пробуем загрузить из testing_sessions
#             if count_new > 0 and 'session_date' in column_names and 'session_time' in column_names:
#                 cursor.execute("""
#                                SELECT session_date,
#                                       session_time,
#                                       'Комплексный тест СЗР'                                      as test_type,
#                                       CASE WHEN validity = 1 THEN 'Пригодно' ELSE 'Проверить' END as data_quality
#                                FROM testing_sessions
#                                WHERE patient_id = ?
#                                ORDER BY session_date DESC, session_time DESC
#                                """, (patient_id,))
#                 visits = cursor.fetchall()
#                 print(f"✅ Загружено {len(visits)} посещений из testing_sessions")
#
#             # Если в testing_sessions нет данных, загружаем из boxbase
#             if not visits and count_old > 0:
#                 cursor.execute("""
#                                SELECT CurrentDate,
#                                       CurrentTime,
#                                       'Комплексный тест СЗР',
#                                       CASE WHEN VidSost = 1 THEN 'Пригодно' ELSE 'Проверить' END
#                                FROM boxbase
#                                WHERE REG_ID = ?
#                                ORDER BY CurrentDate DESC, CurrentTime DESC
#                                """, (original_id,))
#                 visits = cursor.fetchall()
#                 print(f"✅ Загружено {len(visits)} посещений из boxbase")
#
#             for visit in visits:
#                 self.visits_tree.insert('', 'end', values=visit)
#
#             conn.close()
#             return len(visits)
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки посещений из новой схемы: {e}")
#             return 0
#
#     def _load_visits_old_schema(self, original_id):
#         """Загружает посещения из старой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("SELECT COUNT(*) FROM boxbase WHERE REG_ID = ?", (original_id,))
#             count = cursor.fetchone()[0]
#
#             if count == 0:
#                 print(f"⚠️  Для пациента с ID {original_id} нет данных в boxbase")
#                 return 0
#
#             cursor.execute("""
#                            SELECT CurrentDate,
#                                   CurrentTime,
#                                   'Комплексный тест СЗР',
#                                   CASE WHEN VidSost = 1 THEN 'Пригодно' ELSE 'Проверить' END
#                            FROM boxbase
#                            WHERE REG_ID = ?
#                            ORDER BY CurrentDate DESC, CurrentTime DESC
#                            """, (original_id,))
#
#             visits = cursor.fetchall()
#
#             for visit in visits:
#                 self.visits_tree.insert('', 'end', values=visit)
#
#             conn.close()
#             print(f"✅ Загружено {len(visits)} посещений из boxbase для пациента ID={original_id}")
#             return len(visits)
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки посещений из старой схемы: {e}")
#             return 0
#
#     def get_selected_patient(self):
#         """Возвращает выбранного пациента"""
#         return self.selected_patient
#
#     def get_selected_visits(self):
#         """Возвращает выбранные посещения"""
#         return self.selected_visits

# # gui/components/patient_selector.py
# import tkinter as tk
# from tkinter import ttk, messagebox
# import sqlite3
# from datetime import datetime
# import os
#
#
# class PatientSelector(tk.Frame):
#     def __init__(self, parent, db_path="neuro_data.db"):
#         super().__init__(parent)
#         self.db_path = db_path
#         self.selected_patient = None
#         self.selected_visits = []
#         self.patients_data = {}
#         self.all_patients_data = {}
#         self.sort_order = "name"
#         self.new_schema_available = False
#         self.old_schema_available = False
#         self.data_loader = None
#         self._check_schema()
#         self.init_ui()
#         self.check_database()
#
#     def set_data_loader(self, data_loader):
#         """Устанавливает data_loader для доступа к данным"""
#         self.data_loader = data_loader
#
#     def _check_schema(self):
#         """Проверяет доступность схем БД"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visual_tests'")
#             self.new_schema_available = cursor.fetchone() is not None
#
#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
#             self.old_schema_available = cursor.fetchone() is not None
#
#             conn.close()
#             print(f"🔍 Схемы БД: новая={self.new_schema_available}, старая={self.old_schema_available}")
#         except:
#             self.new_schema_available = False
#             self.old_schema_available = False
#
#     def init_ui(self):
#         """Инициализация интерфейса"""
#         self.notebook = ttk.Notebook(self)
#
#         self.single_frame = ttk.Frame(self.notebook)
#         self.create_single_tab()
#
#         self.compare_frame = ttk.Frame(self.notebook)
#         self.create_compare_tab()
#
#         self.group_frame = ttk.Frame(self.notebook)
#         self.create_group_tab()
#
#         self.notebook.add(self.single_frame, text="Один пациент")
#         self.notebook.add(self.compare_frame, text="Сравнение двух")
#         self.notebook.add(self.group_frame, text="Групповой анализ")
#         self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
#
#     def create_single_tab(self):
#         """Создает вкладку выбора одного пациента"""
#         patient_frame = ttk.LabelFrame(self.single_frame, text="Выбор пациента", padding=10)
#         patient_frame.pack(fill='x', padx=5, pady=5)
#
#         schema_info = self._get_schema_info()
#         schema_label = ttk.Label(patient_frame, text=schema_info, font=("Arial", 9), foreground="blue")
#         schema_label.pack(fill='x', pady=5)
#
#         sort_frame = ttk.Frame(patient_frame)
#         sort_frame.pack(fill='x', pady=5)
#
#         ttk.Label(sort_frame, text="Сортировка:").pack(side=tk.LEFT)
#
#         self.sort_var = tk.StringVar(value="name")
#         ttk.Radiobutton(sort_frame, text="По фамилии", variable=self.sort_var,
#                         value="name", command=self.on_sort_changed).pack(side=tk.LEFT, padx=10)
#         ttk.Radiobutton(sort_frame, text="По ID", variable=self.sort_var,
#                         value="id", command=self.on_sort_changed).pack(side=tk.LEFT, padx=10)
#
#         search_frame = ttk.Frame(patient_frame)
#         search_frame.pack(fill='x', pady=5)
#
#         ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
#
#         self.search_var = tk.StringVar()
#         self.search_combo = ttk.Combobox(search_frame, textvariable=self.search_var, width=40)
#         self.search_combo.pack(side=tk.LEFT, padx=5, pady=5, fill='x', expand=True)
#
#         self.search_combo.bind('<KeyRelease>', self.on_search_keyrelease)
#         self.search_combo.bind('<<ComboboxSelected>>', self.on_search_selected)
#
#         ttk.Button(search_frame, text="❌", width=3,
#                    command=self.clear_search).pack(side=tk.LEFT, padx=5)
#
#         self.info_label = tk.Label(patient_frame,
#                                    text="Сначала загрузите данные во вкладке '📁 Данные'",
#                                    justify='left', anchor='w', fg='gray', wraplength=500)
#         self.info_label.pack(fill='x', pady=5)
#
#         visits_frame = ttk.LabelFrame(self.single_frame, text="Посещения и тесты", padding=10)
#         visits_frame.pack(fill='both', expand=True, padx=5, pady=5)
#
#         columns = ('date', 'time', 'test_type', 'data_quality')
#         self.visits_tree = ttk.Treeview(visits_frame, columns=columns, show='headings', height=10)
#
#         self.visits_tree.heading('date', text='Дата')
#         self.visits_tree.heading('time', text='Время')
#         self.visits_tree.heading('test_type', text='Тип теста')
#         self.visits_tree.heading('data_quality', text='Качество данных')
#
#         self.visits_tree.column('date', width=100)
#         self.visits_tree.column('time', width=80)
#         self.visits_tree.column('test_type', width=150)
#         self.visits_tree.column('data_quality', width=100)
#
#         scrollbar = ttk.Scrollbar(visits_frame, orient='vertical', command=self.visits_tree.yview)
#         self.visits_tree.configure(yscrollcommand=scrollbar.set)
#
#         self.visits_tree.pack(side='left', fill='both', expand=True)
#         scrollbar.pack(side='right', fill='y')
#
#         # Добавляем Label для отображения статуса загрузки посещений
#         self.visits_status_label = tk.Label(visits_frame, text="Выберите пациента для загрузки посещений",
#                                             justify='left', anchor='w', fg='gray', wraplength=400)
#         self.visits_status_label.pack(fill='x', padx=5, pady=5)
#
#         button_frame = ttk.Frame(self.single_frame)
#         button_frame.pack(fill='x', padx=5, pady=5)
#
#         self.select_button = ttk.Button(button_frame, text="Выбрать для анализа",
#                                         state='disabled', command=self.on_select_patient)
#         self.select_button.pack(side='right', padx=5)
#
#         self.refresh_button = ttk.Button(button_frame, text="Обновить данные",
#                                          command=self.refresh_data)
#         self.refresh_button.pack(side='right', padx=5)
#
#     def on_select_patient(self):
#         """Обработчик выбора пациента для анализа"""
#         try:
#             if not self.selected_patient:
#                 messagebox.showwarning("Внимание", "Сначала выберите пациента из списка")
#                 return
#
#             patient_id = self.selected_patient['id']
#             original_id = self.selected_patient.get('external_id', patient_id)
#             print(f"🎯 Выбран пациент для анализа: ID={patient_id}, Original ID={original_id}")
#
#             messagebox.showinfo("Выбор пациента",
#                                 f"Пациент выбран для анализа.\n\n"
#                                 f"ID в системе: {patient_id}\n"
#                                 f"Исходный ID: {original_id}\n\n"
#                                 f"Данные будут использоваться в модулях анализа СЗР и нейромедиаторов.")
#
#         except Exception as e:
#             print(f"❌ Ошибка при выборе пациента: {e}")
#             import traceback
#             traceback.print_exc()
#             messagebox.showerror("Ошибка", f"Не удалось выбрать пациента: {e}")
#
#     def _get_schema_info(self):
#         """Получает информацию о доступной схеме БД"""
#         if self.new_schema_available:
#             return "✅ Используется новая схема (нейромедиаторный анализ)"
#         elif self.old_schema_available:
#             return "🔸 Используется старая схема (базовый анализ)"
#         else:
#             return "❌ База данных не найдена"
#
#     def create_compare_tab(self):
#         """Создает вкладку сравнения двух пациентов"""
#         main_frame = ttk.Frame(self.compare_frame)
#         main_frame.pack(expand=True, fill='both', padx=20, pady=20)
#
#         title_label = tk.Label(main_frame, text="Сравнение двух пациентов",
#                                font=("Arial", 14, "bold"))
#         title_label.pack(pady=10)
#
#         schema_info = self._get_schema_info()
#         schema_label = tk.Label(main_frame, text=schema_info, fg='blue')
#         schema_label.pack(pady=5)
#
#         instruction_label = tk.Label(main_frame,
#                                      text="Для сравнения двух пациентов загрузите данные во вкладке '📁 Данные'",
#                                      justify='center', fg='gray', wraplength=400)
#         instruction_label.pack(pady=10)
#
#     def create_group_tab(self):
#         """Создает вкладку группового анализа"""
#         main_frame = ttk.Frame(self.group_frame)
#         main_frame.pack(expand=True, fill='both', padx=20, pady=20)
#
#         title_label = tk.Label(main_frame, text="Групповой анализ",
#                                font=("Arial", 14, "bold"))
#         title_label.pack(pady=10)
#
#         schema_info = self._get_schema_info()
#         schema_label = tk.Label(main_frame, text=schema_info, fg='blue')
#         schema_label.pack(pady=5)
#
#         instruction_label = tk.Label(main_frame,
#                                      text="Для группового анализа загрузите данные во вкладке '📁 Данные'",
#                                      justify='center', fg='gray', wraplength=400)
#         instruction_label.pack(pady=10)
#
#     def on_search_keyrelease(self, event):
#         """Обработка ввода в поле поиска"""
#         search_text = self.search_var.get().strip()
#
#         if not search_text:
#             self.update_search_results(list(self.all_patients_data.keys()))
#             return
#
#         matches = []
#         search_lower = search_text.lower()
#
#         for display_name, patient_data in self.all_patients_data.items():
#             # Поиск по исходному ID (external_id)
#             original_id = str(patient_data.get('external_id', ''))
#             if search_text.isdigit() and search_text == original_id:
#                 matches.append(display_name)
#                 continue
#
#             # Поиск по фамилии, имени, отчеству
#             if (search_lower in patient_data.get('lname', '').lower() or
#                     search_lower in patient_data.get('fname', '').lower() or
#                     search_lower in patient_data.get('sname', '').lower() or
#                     search_lower in display_name.lower()):
#                 matches.append(display_name)
#
#         if self.sort_order == "name":
#             matches.sort()
#         else:
#             matches.sort(key=lambda x: self.all_patients_data[x].get('external_id', 0))
#
#         self.update_search_results(matches)
#
#     def update_search_results(self, matches):
#         """Обновляет результаты поиска в комбобоксе"""
#         if matches:
#             self.search_combo['values'] = matches
#         else:
#             self.search_combo['values'] = ["Не найдено"]
#             self.search_combo.set("Не найдено")
#
#     def on_search_selected(self, event=None):
#         """Обработка выбора из результатов поиска"""
#         selected_name = self.search_var.get()
#         if selected_name and selected_name in self.all_patients_data and selected_name != "Не найдено":
#             patient = self.all_patients_data[selected_name]
#             self.selected_patient = patient
#
#             # Формируем информационный текст
#             info_text = f"ID в системе: {patient['id']}\n"
#
#             original_id = patient.get('external_id', '')
#             if original_id:
#                 info_text += f"Исходный ID: {original_id}\n"
#
#             if 'yborn' in patient and patient['yborn']:
#                 info_text += f"Год рождения: {patient['yborn']}\n"
#
#             if 'gender' in patient:
#                 info_text += f"Пол: {patient['gender']}\n"
#
#             if 'fname' in patient or 'lname' in patient:
#                 name_parts = []
#                 if 'lname' in patient:
#                     name_parts.append(patient['lname'])
#                 if 'fname' in patient:
#                     name_parts.append(patient['fname'])
#                 if 'sname' in patient:
#                     name_parts.append(patient['sname'])
#
#                 if name_parts:
#                     info_text += f"ФИО: {' '.join(name_parts)}"
#
#             self.info_label.config(text=info_text)
#
#             original_id = patient.get('external_id', 'N/A')
#             print(f"🔍 Выбран пациент: ID={patient['id']}, Исходный ID={original_id}")
#
#             # Загружаем посещения используя исходный ID
#             self.load_patient_visits(patient['id'], original_id)
#
#             self.select_button.config(state='normal')
#
#     def clear_search(self):
#         """Очищает поле поиска"""
#         self.search_var.set("")
#         self.update_search_results(list(self.all_patients_data.keys()))
#         self.select_button.config(state='disabled')
#         self.visits_status_label.config(text="Выберите пациента для загрузки посещений", fg='gray')
#
#     def on_sort_changed(self):
#         """Обработка изменения сортировки"""
#         self.sort_order = self.sort_var.get()
#         current_search = self.search_var.get()
#         if current_search:
#             self.on_search_keyrelease(None)
#         else:
#             self.load_patients()
#
#     def check_database(self):
#         """Проверяет наличие БД и загружает данные если есть"""
#         if os.path.exists(self.db_path):
#             self.load_patients()
#         else:
#             self.show_no_database_message()
#
#     def show_no_database_message(self):
#         """Показывает сообщение об отсутствии БД"""
#         message = """
# База данных не найдена!
#
# Для работы с пациентами:
#
# 1. Перейдите во вкладку '📁 Данные'
# 2. Загрузите файлы users.xlsx и boxbase.xlsx
# 3. Данные автоматически сохранятся в базу
# 4. Вернитесь в эту вкладку
#
# Рекомендация: используйте Excel (.xlsx) для сохранения кириллицы!
# """
#         for widget in self.single_frame.winfo_children():
#             widget.destroy()
#
#         info_label = tk.Label(self.single_frame, text=message,
#                               justify='left', fg='blue', wraplength=500, font=("Arial", 10))
#         info_label.pack(padx=20, pady=20)
#
#     def refresh_data(self):
#         """Обновляет данные из БД"""
#         if os.path.exists(self.db_path):
#             self._check_schema()
#             success = self.load_patients()
#             if success:
#                 messagebox.showinfo("Обновление", "Данные пациентов обновлены!")
#                 return True
#         else:
#             messagebox.showwarning("Внимание", "База данных еще не создана!")
#             return False
#
#     def load_patients(self):
#         """Загрузка списка пациентов с поддержкой обеих схем"""
#         if self.new_schema_available:
#             return self._load_patients_new_schema()
#         elif self.old_schema_available:
#             return self._load_patients_old_schema()
#         else:
#             self.show_no_database_message()
#             return False
#
#     def _load_patients_new_schema(self):
#         """Загрузка пациентов из новой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("PRAGMA table_info(patients)")
#             columns_info = cursor.fetchall()
#             column_names = [col[1] for col in columns_info]
#
#             if 'external_id' in column_names:
#                 cursor.execute("""
#                                SELECT id, external_id, fname, sname, lname, yborn, gender
#                                FROM patients
#                                ORDER BY lname, fname
#                                """)
#             else:
#                 cursor.execute("""
#                                SELECT id, id as external_id, fname, sname, lname, yborn, gender
#                                FROM patients
#                                ORDER BY lname, fname
#                                """)
#
#             patients = cursor.fetchall()
#
#             self.patients_data = {}
#             self.all_patients_data = {}
#             patient_names = []
#
#             for patient in patients:
#                 patient_dict = {
#                     'id': patient[0],
#                     'external_id': patient[1],
#                     'fname': patient[2] or '',
#                     'sname': patient[3] or '',
#                     'lname': patient[4] or '',
#                     'yborn': patient[5],
#                     'gender': 'Мужской' if patient[6] == 1 else 'Женский'
#                 }
#
#                 display_name = self._format_patient_display_name(patient_dict)
#                 patient_names.append(display_name)
#                 self.patients_data[display_name] = patient_dict
#                 self.all_patients_data[display_name] = patient_dict
#
#             self.search_combo['values'] = patient_names
#             if patient_names:
#                 self.search_combo.set("")
#
#             self.info_label.config(text=f"Новая схема БД | Введите ID, фамилию или имя для поиска", fg='black')
#             conn.close()
#             print(f"✅ Загружено {len(patient_names)} пациентов из новой схемы")
#             return True
#
#         except Exception as e:
#             print(f"Ошибка загрузки пациентов из новой схемы: {e}")
#             return self._load_patients_old_schema()
#
#     def _load_patients_old_schema(self):
#         """Загрузка пациентов из старой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
#             if not cursor.fetchone():
#                 conn.close()
#                 self.show_no_database_message()
#                 return False
#
#             cursor.execute("PRAGMA table_info(users)")
#             columns_info = cursor.fetchall()
#             column_names = [col[1] for col in columns_info]
#             print(f"🔍 Столбцы в таблице users: {column_names}")
#
#             select_columns = []
#             if 'FName' in column_names:
#                 select_columns.append('FName')
#             if 'SName' in column_names:
#                 select_columns.append('SName')
#             if 'LName' in column_names:
#                 select_columns.append('LName')
#             if 'YBorn' in column_names:
#                 select_columns.append('YBorn')
#             if 'Gender' in column_names:
#                 select_columns.append('Gender')
#
#             select_columns.insert(0, 'ID')
#             if 'Active' in column_names:
#                 select_columns.append('Active')
#
#             select_str = ', '.join(select_columns)
#
#             if self.sort_order == "name" and 'LName' in column_names and 'FName' in column_names:
#                 order_clause = "ORDER BY LName, FName, SName"
#                 sort_info = " (сортировка по фамилии)"
#             else:
#                 order_clause = "ORDER BY ID"
#                 sort_info = " (сортировка по ID)"
#
#             query = f"SELECT {select_str} FROM users WHERE Active = 1 {order_clause}"
#
#             cursor.execute(query)
#             patients = cursor.fetchall()
#             self.patients_data = {}
#             self.all_patients_data = {}
#
#             patient_names = []
#
#             for patient in patients:
#                 patient_dict = {
#                     'id': patient[0],
#                     'external_id': patient[0],  # В старой схеме ID = external_id
#                     'original_id': patient[0]  # Сохраняем исходный ID
#                 }
#
#                 col_index = 1
#                 if 'FName' in column_names and col_index < len(patient):
#                     patient_dict['fname'] = patient[col_index]
#                     col_index += 1
#                 if 'SName' in column_names and col_index < len(patient):
#                     patient_dict['sname'] = patient[col_index]
#                     col_index += 1
#                 if 'LName' in column_names and col_index < len(patient):
#                     patient_dict['lname'] = patient[col_index]
#                     col_index += 1
#                 if 'YBorn' in column_names and col_index < len(patient):
#                     patient_dict['yborn'] = patient[col_index]
#                     col_index += 1
#                 if 'Gender' in column_names and col_index < len(patient):
#                     patient_dict['gender'] = 'Мужской' if patient[col_index] == 1 else 'Женский'
#
#                 display_name = self._format_patient_display_name(patient_dict)
#                 patient_names.append(display_name)
#                 self.patients_data[display_name] = patient_dict
#                 self.all_patients_data[display_name] = patient_dict
#
#             self.search_combo['values'] = patient_names
#             if patient_names:
#                 self.search_combo.set("")
#
#             self.info_label.config(text=f"Введите ID, фамилию или имя для поиска{sort_info}", fg='black')
#
#             conn.close()
#             print(f"✅ Загружено {len(patient_names)} пациентов из старой схемы")
#             return True
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки пациентов из старой схемы: {e}")
#             messagebox.showerror("Ошибка", f"Не удалось загрузить пациентов: {e}")
#             return False
#
#     def _format_patient_display_name(self, patient_dict):
#         """Форматирует отображаемое имя пациента"""
#         name_parts = []
#         if patient_dict.get('lname'):
#             name_parts.append(patient_dict['lname'])
#         if patient_dict.get('fname'):
#             name_parts.append(patient_dict['fname'])
#         if patient_dict.get('sname'):
#             name_parts.append(patient_dict['sname'])
#
#         display_name = ' '.join(name_parts) if name_parts else f"Пациент"
#
#         # Добавляем исходный ID для поиска
#         original_id = patient_dict.get('external_id', patient_dict.get('id'))
#         display_name += f" (ID: {original_id})"
#
#         return display_name
#
#     def load_patient_visits(self, patient_id, original_id=None):
#         """Загружает посещения и тесты выбранного пациента"""
#         try:
#             # Очищаем предыдущие данные
#             for item in self.visits_tree.get_children():
#                 self.visits_tree.delete(item)
#
#             # Обновляем статус загрузки
#             self.visits_status_label.config(text="Загрузка посещений...", fg='blue')
#
#             # Всегда используем исходный ID для поиска в boxbase
#             search_id = original_id if original_id else patient_id
#
#             if self.new_schema_available:
#                 visits_count = self._load_visits_new_schema(patient_id, search_id)
#             else:
#                 visits_count = self._load_visits_old_schema(search_id)
#
#             # Обновляем статус в GUI
#             if visits_count > 0:
#                 self.visits_status_label.config(text=f"✅ Загружено {visits_count} посещений", fg='green')
#             else:
#                 self.visits_status_label.config(
#                     text=f"❌ Для пациента с ID {search_id} не найдено посещений\n"
#                          f"Проверьте соответствие ID в данных тестирования",
#                     fg='red'
#                 )
#
#         except Exception as e:
#             error_msg = f"❌ Ошибка загрузки посещений: {e}"
#             print(error_msg)
#             self.visits_status_label.config(text=error_msg, fg='red')
#             import traceback
#             traceback.print_exc()
#
#     def _load_visits_new_schema(self, patient_id, original_id):
#         """Загружает посещения из новой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             # Сначала проверим структуру таблицы testing_sessions
#             cursor.execute("PRAGMA table_info(testing_sessions)")
#             columns_info = cursor.fetchall()
#             column_names = [col[1] for col in columns_info]
#             print(f"🔍 Столбцы testing_sessions: {column_names}")
#
#             # Проверим есть ли данные для этого пациента в testing_sessions
#             cursor.execute("SELECT COUNT(*) FROM testing_sessions WHERE patient_id = ?", (patient_id,))
#             count_new = cursor.fetchone()[0]
#
#             # Проверим есть ли данные в boxbase по исходному ID
#             cursor.execute("SELECT COUNT(*) FROM boxbase WHERE REG_ID = ?", (original_id,))
#             count_old = cursor.fetchone()[0]
#
#             print(f"🔍 Данные для пациента: testing_sessions={count_new}, boxbase={count_old}")
#
#             visits = []
#
#             # Пробуем загрузить из testing_sessions
#             if count_new > 0 and 'session_date' in column_names and 'session_time' in column_names:
#                 cursor.execute("""
#                                SELECT session_date,
#                                       session_time,
#                                       'Комплексный тест СЗР'                                      as test_type,
#                                       CASE WHEN validity = 1 THEN 'Пригодно' ELSE 'Проверить' END as data_quality
#                                FROM testing_sessions
#                                WHERE patient_id = ?
#                                ORDER BY session_date DESC, session_time DESC
#                                """, (patient_id,))
#                 visits = cursor.fetchall()
#                 print(f"✅ Загружено {len(visits)} посещений из testing_sessions")
#
#             # Если в testing_sessions нет данных, загружаем из boxbase
#             if not visits and count_old > 0:
#                 cursor.execute("""
#                                SELECT CurrentDate,
#                                       CurrentTime,
#                                       'Комплексный тест СЗР',
#                                       CASE WHEN VidSost = 1 THEN 'Пригодно' ELSE 'Проверить' END
#                                FROM boxbase
#                                WHERE REG_ID = ?
#                                ORDER BY CurrentDate DESC, CurrentTime DESC
#                                """, (original_id,))
#                 visits = cursor.fetchall()
#                 print(f"✅ Загружено {len(visits)} посещений из boxbase")
#
#             for visit in visits:
#                 self.visits_tree.insert('', 'end', values=visit)
#
#             conn.close()
#             return len(visits)
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки посещений из новой схемы: {e}")
#             return 0
#
#     def _load_visits_old_schema(self, original_id):
#         """Загружает посещения из старой схемы"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             cursor.execute("SELECT COUNT(*) FROM boxbase WHERE REG_ID = ?", (original_id,))
#             count = cursor.fetchone()[0]
#
#             if count == 0:
#                 print(f"⚠️  Для пациента с ID {original_id} нет данных в boxbase")
#                 return 0
#
#             cursor.execute("""
#                            SELECT CurrentDate,
#                                   CurrentTime,
#                                   'Комплексный тест СЗР',
#                                   CASE WHEN VidSost = 1 THEN 'Пригодно' ELSE 'Проверить' END
#                            FROM boxbase
#                            WHERE REG_ID = ?
#                            ORDER BY CurrentDate DESC, CurrentTime DESC
#                            """, (original_id,))
#
#             visits = cursor.fetchall()
#
#             for visit in visits:
#                 self.visits_tree.insert('', 'end', values=visit)
#
#             conn.close()
#             print(f"✅ Загружено {len(visits)} посещений из boxbase для пациента ID={original_id}")
#             return len(visits)
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки посещений из старой схемы: {e}")
#             return 0
#
#     def get_selected_patient(self):
#         """Возвращает выбранного пациента"""
#         return self.selected_patient
#
#     def get_selected_visits(self):
#         """Возвращает выбранные посещения"""
#         return self.selected_visits
#
#
