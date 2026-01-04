# gui/main_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
import os
import sys


class MainWindow:
    def __init__(self, root, data_loader):
        self.root = root
        self.data_loader = data_loader
        self.logger = logging.getLogger(__name__)
        self.db_path = "neuro_data.db"

        self.setup_ui()
        self.create_menu()

    def create_menu(self):
        """Создание главного меню"""
        menubar = tk.Menu(self.root)

        # Меню Данные
        data_menu = tk.Menu(menubar, tearoff=0)
        data_menu.add_command(label="Миграция данных...", command=self.run_migration)
        data_menu.add_separator()
        data_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Данные", menu=data_menu)

        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

    def run_migration(self):
        """Запуск миграции данных"""
        response = messagebox.askyesno(
            "Миграция данных",
            "Это ОДНОКРАТНАЯ операция миграции данных из старых форматов в новую базу.\n\n"
            "Существующая база данных будет пересоздана.\n"
            "Продолжить?"
        )
        if response:
            try:
                migration_script = os.path.join(os.path.dirname(__file__), '..', 'utils', 'database_migration.py')
                if os.path.exists(migration_script):
                    # Запускаем миграцию в отдельном процессе
                    os.system(f'python "{migration_script}"')
                    messagebox.showinfo("Миграция", "Миграция данных завершена. Перезапустите приложение.")
                else:
                    messagebox.showerror("Ошибка", "Скрипт миграции не найден")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при миграции: {e}")

    def show_about(self):
        """Показать информацию о программе"""
        about_text = """
NeuroTransAnalytics v2.0

Система анализа скоростей зрительных реакций
с оценкой нейромедиаторной активности

📊 Возможности:
• Анализ индивидуальных и групповых данных
• Оценка активности нейромедиаторов
• Статистическая обработка малых выборок
• Визуализация результатов

🔬 Научная основа:
• V1 (глутамат/ГАМК) - простая зрительная реакция
• ΔV4 (ацетилхолин) - реакция на цвет
• ΔV5/MT (дофамин) - реакция на сдвиг

📁 Поддерживаемые форматы:
• CSV, Excel, Access (.mdb)
• SQLite база данных
        """
        messagebox.showinfo("О программе", about_text)

    def setup_ui(self):
        """Настройка главного интерфейса"""
        # Создаем Notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем вкладки
        self.setup_patient_tab()
        self.setup_data_tab()
        self.setup_analysis_tab()
        self.setup_neurotransmitter_tab()
        self.setup_help_tab()

        # Статус бар
        self.setup_status_bar()

    def setup_patient_tab(self):
        """Настройка вкладки выбора пациентов"""
        patient_tab = ttk.Frame(self.notebook)
        self.notebook.add(patient_tab, text="👥 Пациенты")

        try:
            from gui.components.patient_selector import PatientSelector

            # Создаем селектор пациентов
            self.patient_selector = PatientSelector(patient_tab, self.db_path)
            self.patient_selector.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Добавляем кнопку обновления данных
            refresh_btn = ttk.Button(
                patient_tab,
                text="🔄 Обновить список пациентов",
                command=self.refresh_patient_list
            )
            refresh_btn.pack(pady=5)

        except ImportError as e:
            error_label = ttk.Label(
                patient_tab,
                text=f"Компонент выбора пациентов недоступен:\n{str(e)}",
                foreground='red',
                justify=tk.LEFT
            )
            error_label.pack(padx=20, pady=20)

    def refresh_patient_list(self):
        """Обновить список пациентов"""
        if hasattr(self, 'patient_selector'):
            try:
                self.patient_selector.refresh_data()
                self.log_message("✅ Список пациентов обновлен")
                self.update_status("Список пациентов обновлен")
            except Exception as e:
                self.log_message(f"⚠️ Ошибка обновления пациентов: {e}")
                self.update_status("Ошибка обновления пациентов")

    def setup_data_tab(self):
        """Настройка вкладки данных"""
        from gui.components.data_loader_ui import DataLoaderUI

        data_tab = ttk.Frame(self.notebook)
        self.notebook.add(data_tab, text="📁 Данные")

        # Компонент загрузки данных с callback для обновления пациентов
        self.data_loader_component = DataLoaderUI(
            data_tab,
            self.data_loader,
            on_data_loaded=self.on_data_loaded_with_update
        )

        # ИСПРАВЛЕНИЕ: используем frame компонента вместо самого компонента
        self.data_loader_component.frame.pack(fill=tk.BOTH, expand=True)

        # Область для лога
        self.setup_log_area(data_tab)

    def on_data_loaded_with_update(self, data_type, file_path, data):
        """Обработка загрузки данных с обновлением пациентов"""
        # Вызываем оригинальный метод
        self.on_data_loaded(data_type, file_path, data)

        # Обновляем селектор пациентов если он существует
        if hasattr(self, 'patient_selector'):
            try:
                self.patient_selector.refresh_data()
                self.log_message("✅ Данные пациентов обновлены")
            except Exception as e:
                self.log_message(f"⚠️ Не удалось обновить пациентов: {e}")

    def on_data_loaded(self, data_type, file_path, data):
        """Обработка загрузки данных"""
        self.log_message(f"✅ Загружен {data_type}: {os.path.basename(file_path)}")
        self.log_message(f"   📊 Строк: {len(data)}, Столбцов: {len(data.columns)}")

        if len(data) > 0:
            sample = data.head(2)
            for _, row in sample.iterrows():
                if data_type == 'users':
                    self.log_message(f"   Пример: ID={row['ID']}, YBorn={row['YBorn']}")
                else:
                    self.log_message(f"   Пример: REG_ID={row['REG_ID']}, Date={row['CurrentDate']}")

        self.update_status(f"Загружены данные: {os.path.basename(file_path)}")

    def setup_log_area(self, parent):
        """Настройка области лога"""
        log_frame = ttk.LabelFrame(parent, text="Лог выполнения", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления логом
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=5)

        ttk.Button(log_controls, text="Очистить лог", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Экспорт лога...", command=self.export_log).pack(side=tk.LEFT, padx=5)

    def clear_log(self):
        """Очистить лог"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("🗑️ Лог очищен")

    def export_log(self):
        """Экспорт лога в файл"""
        try:
            from tkinter import filedialog
            import datetime

            log_content = self.log_text.get(1.0, tk.END)
            if not log_content.strip():
                messagebox.showwarning("Экспорт", "Лог пустой")
                return

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neuro_trans_analytics_log_{timestamp}.txt"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=filename
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"NeuroTransAnalytics Log - {timestamp}\n")
                    f.write("=" * 50 + "\n")
                    f.write(log_content)

                self.log_message(f"📤 Лог экспортирован: {file_path}")
                messagebox.showinfo("Экспорт", f"Лог успешно экспортирован в:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта лога: {e}")

    def log_message(self, message):
        """Добавление сообщения в лог"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.update_idletasks()

    def update_status(self, message):
        """Обновление статус бара"""
        self.status_label.config(text=message)

    def setup_analysis_tab(self):
        """Настройка вкладки анализа"""
        analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(analysis_tab, text="📊 Анализ СЗР")

        # Основной фрейм для анализа
        main_frame = ttk.Frame(analysis_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        info_text = """
🎯 Анализ скоростей зрительных реакций (СЗР)

Для начала анализа:
1. Выберите пациента во вкладке '👥 Пациенты'
2. Убедитесь, что данные загружены во вкладке '📁 Данные'
3. Перейдите во вкладку '🧠 Нейромедиаторы' для детального анализа

📈 Доступные виды анализа:
• Индивидуальный анализ по тестам
• Сравнительный анализ по группам
• Динамика изменений во времени
• Статистическая обработка результатов
        """

        info_label = ttk.Label(
            main_frame,
            text=info_text,
            font=("Arial", 11),
            justify=tk.LEFT,
            background='#f0f0f0',
            relief=tk.RIDGE,
            padding=20
        )
        info_label.pack(fill=tk.BOTH, expand=True)

        # Кнопка быстрого перехода к пациентам
        ttk.Button(
            main_frame,
            text="👥 Перейти к выбору пациентов",
            command=lambda: self.notebook.select(0)
        ).pack(pady=10)

    def setup_neurotransmitter_tab(self):
        """Настройка вкладки анализа нейромедиаторов"""
        neuro_tab = ttk.Frame(self.notebook)
        self.notebook.add(neuro_tab, text="🧠 Нейромедиаторы")

        # Основной фрейм
        main_frame = ttk.Frame(neuro_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        neuro_text = """
🧪 Анализ нейромедиаторной активности

На основе скоростей зрительных реакций оценивается активность:

• 🟣 ГЛУТАМАТ/ГАМК - V1 путь (простая зрительная реакция)
• 🔵 АЦЕТИЛХОЛИН - ΔV4 путь (реакция на цвет)  
• 🟢 ДОФАМИН - ΔV5/MT путь (реакция на сдвиг)

📊 Методика расчета:
V1 = Среднее время ПЗР (простая зрительная реакция)
ΔV4 = Время реакции на цвет - V1
ΔV5/MT = Время реакции на сдвиг - V1

⚠️ Примечание: В текущих данных отсутствует коррекция 
на моторное время (теппинг-тест не проводился)
        """

        neuro_label = ttk.Label(
            main_frame,
            text=neuro_text,
            font=("Arial", 11),
            justify=tk.LEFT,
            background='#f0f8ff',
            relief=tk.RIDGE,
            padding=20
        )
        neuro_label.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления анализом
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)

        ttk.Button(
            btn_frame,
            text="📈 Запустить анализ",
            command=self.run_neuro_analysis
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            btn_frame,
            text="📋 Показать результаты",
            command=self.show_neuro_results
        ).pack(side=tk.LEFT, padx=10)

    def run_neuro_analysis(self):
        """Запуск анализа нейромедиаторов"""
        try:
            from core.neuro_analyzer import NeurotransmitterAnalyzer

            analyzer = NeurotransmitterAnalyzer()
            analyzer.calculate_all_metrics()

            self.log_message("✅ Анализ нейромедиаторной активности завершен")
            messagebox.showinfo("Анализ", "Анализ нейромедиаторной активности успешно выполнен")

        except Exception as e:
            error_msg = f"❌ Ошибка анализа: {e}"
            self.log_message(error_msg)
            messagebox.showerror("Ошибка", error_msg)

    def show_neuro_results(self):
        """Показать результаты анализа нейромедиаторов"""
        messagebox.showinfo(
            "Результаты анализа",
            "Функция отображения результатов находится в разработке.\n\n"
            "Следите за обновлениями!"
        )

    def setup_help_tab(self):
        """Настройка вкладки помощи"""
        help_tab = ttk.Frame(self.notebook)
        self.notebook.add(help_tab, text="❓ Помощь")

        help_text = """
NeuroTransAnalytics v2.0 - Система анализа скоростей зрительных реакций

🎯 НАЗНАЧЕНИЕ:
Анализ индивидуальных и групповых данных тестирования 
скоростей зрительных реакций с оценкой нейромедиаторной активности

📋 ОСНОВНЫЕ ВОЗМОЖНОСТИ:
• Выбор и поиск пациентов в базе данных
• Загрузка данных из CSV, Excel, Access (.mdb)
• Анализ трех типов зрительных реакций
• Оценка активности нейромедиаторов
• Статистическая обработка данных

🚀 ИНСТРУКЦИЯ ПО РАБОТЕ:
1. ЗАГРУЗКА ДАННЫХ - используйте вкладку '📁 Данные' для импорта
2. ВЫБОР ПАЦИЕНТА - во вкладке '👥 Пациенты' выберите пациента
3. АНАЛИЗ - перейдите во вкладки '📊 Анализ СЗР' или '🧠 Нейромедиаторы'

📁 ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ:
• users.xlsx - данные пациентов (с полом)
• boxbase.xlsx/csv - результаты тестирования
• testbase.mdb - Access база данных

🆘 ЕСЛИ ВОЗНИКЛИ ПРОБЛЕМЫ:
• Проверьте наличие файлов в папке data/
• Убедитесь, что база данных создана (миграция выполнена)
• Для миграции данных используйте меню 'Данные → Миграция данных'

📞 ТЕХНИЧЕСКАЯ ПОДДЕРЖКА:
Для вопросов и предложений обращайтесь к разработчикам системы.
        """

        help_label = ttk.Label(help_tab, text=help_text, justify=tk.LEFT, padding=20)
        help_label.pack(fill=tk.BOTH, expand=True)

    def setup_status_bar(self):
        """Настройка статус бара"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(
            status_frame,
            text="Готов к работе | NeuroTransAnalytics v2.0",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, ipady=2)

        # Добавляем информацию о базе данных
        db_status = "✅ База данных доступна" if os.path.exists(self.db_path) else "❌ База данных не найдена"
        db_label = ttk.Label(status_frame, text=db_status, relief=tk.SUNKEN, anchor=tk.E)
        db_label.pack(side=tk.RIGHT, fill=tk.Y, ipadx=10)


