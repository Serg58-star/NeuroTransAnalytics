# main.py
import tkinter as tk
import os
import sys
import logging
import sqlite3

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('neuro_trans_analytics.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Добавляем пути к модулям
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_paths = [
    os.path.join(current_dir, 'core'),
    os.path.join(current_dir, 'gui'),
    os.path.join(current_dir, 'modules'),
    os.path.join(current_dir, 'utils'),
    os.path.join(current_dir, 'data')
]

for path in modules_paths:
    if path not in sys.path:
        sys.path.append(path)


def check_database_exists():
    """Проверяет существование базы данных"""
    db_path = os.path.join(current_dir, 'neuro_data.db')
    return os.path.exists(db_path)


def auto_migrate_database():
    """Автоматическая миграция базы данных при запуске"""
    try:
        from utils.database_migration_v2 import check_database_schema_version, run_database_migration_v2

        if not check_database_exists():
            logger.info("❌ База данных не найдена, миграция не требуется")
            return True

        logger.info("🔍 Проверка необходимости миграции БД...")
        current_version = check_database_schema_version()

        if current_version == "v2_metadata":
            logger.info("✅ База данных актуальна (v2 с метаданными)")
            return True
        elif current_version in ["v2", "v1", "none"]:
            logger.info(f"🔄 Обнаружена схема {current_version}, запуск миграции...")
            return run_database_migration_v2()
        else:
            logger.error("❌ Ошибка проверки схемы БД")
            return False

    except ImportError as e:
        logger.error(f"❌ Модуль миграции не найден: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка автоматической миграции: {e}")
        return False


def initialize_test_metadata():
    """Инициализировать метаданные тестирования из базы данных"""
    try:
        from core.test_metadata import metadata_manager

        conn = sqlite3.connect("neuro_data.db")
        success = metadata_manager.load_from_database(conn)
        conn.close()

        if success:
            print("✅ Метаданные тестирования загружены из базы данных")
        else:
            print("ℹ️ Метаданные: использование встроенных данных")

        # Показать сводку
        metadata_manager.print_summary()
        return True

    except ImportError as e:
        print(f"⚠️ Модуль метаданных не найден: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка инициализации метаданных: {e}")
        print("ℹ️ Метаданные: использование встроенных данных")
        return False


def main():
    """Главная функция приложения"""
    try:
        from core.data_loader import DataLoader
        from gui.main_window import MainWindow

        print("🎯 Запуск NeuroTransAnalytics...")

        # Проверяем существование папки data
        data_path = os.path.join(current_dir, 'data')
        if not os.path.exists(data_path):
            print(f"⚠️ Папка data не найдена: {data_path}")
            os.makedirs(data_path, exist_ok=True)
            print(f"✅ Папка data создана: {data_path}")

        # Автоматическая миграция БД
        print("🔍 Проверка и обновление базы данных...")
        if not auto_migrate_database():
            print("❌ Ошибка миграции базы данных")
            response = input("Продолжить запуск с ограниченной функциональностью? (y/n): ")
            if response.lower() not in ['y', 'yes', 'д', 'да']:
                return

        # Проверяем существование БД
        if not check_database_exists():
            print("\n❌ База данных не найдена!")
            print("Для начала работы необходимо загрузить данные через интерфейс")
            print("Используйте вкладку '📁 Данные' для импорта файлов")
        else:
            print("✅ База данных найдена и актуальна")

        # Инициализация метаданных тестирования
        print("🔍 Инициализация метаданных тестирования...")
        initialize_test_metadata()

        # Инициализация загрузчика данных
        data_loader = DataLoader()

        # Создание главного окна
        root = tk.Tk()
        root.title("NeuroTransAnalytics - Анализ скоростей зрительных реакций")
        root.geometry("1200x800")

        # Создание главного интерфейса
        app = MainWindow(root, data_loader)

        # Запуск приложения
        print("🚀 Запуск графического интерфейса...")
        root.mainloop()

    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--migrate':
            from utils.database_migration_v2 import run_database_migration_v2

            success = run_database_migration_v2()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == '--check-schema':
            from utils.database_migration_v2 import check_database_schema_version

            version = check_database_schema_version()
            print(f"Версия схемы БД: {version}")
        elif sys.argv[1] == '--backup':
            from utils.database_migration_v2 import backup_database

            backup_path = backup_database()
            if backup_path:
                print(f"✅ Резервная копия создана: {backup_path}")
            else:
                print("❌ Ошибка создания резервной копии")
        elif sys.argv[1] == '--update-metadata':
            from utils.database_migration_v2 import update_test_metadata

            print("🔄 Обновление метаданных тестирования...")
            success = update_test_metadata()
            if success:
                print("✅ Метаданные успешно обновлены")
            else:
                print("❌ Ошибка обновления метаданных")
        elif sys.argv[1] == '--help':
            print("""
NeuroTransAnalytics - Аргументы командной строки:
--migrate         Принудительный запуск миграции на схему v2
--check-schema    Проверить версию схемы базы данных  
--backup          Создать резервную копию базы данных
--update-metadata Обновить метаданные тестирования в БД
--help            Показать эту справку
Без аргументов: автоматическая миграция и запуск GUI
            """)
        else:
            print(f"❌ Неизвестный аргумент: {sys.argv[1]}")
    else:
        main()

