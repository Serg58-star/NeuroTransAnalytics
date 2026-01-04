# utils/database_migration.py
"""
Утилита миграции данных из старых форматов в новую схему SQLite
"""
import os
import sys
import sqlite3
from pathlib import Path

# Добавляем пути к модулям
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(current_dir, 'core'))


def main():
    """Основная функция миграции"""
    print("🚀 Запуск миграции данных NeuroTransAnalytics")
    print("=" * 50)

    try:
        from core.legacy_migrator import LegacyMigrator
        from core.neuro_analyzer import NeurotransmitterAnalyzer

        migrator = LegacyMigrator()

        print("📊 Шаг 1: Создание новой схемы БД...")
        migrator.initialize_new_schema()

        print("👥 Шаг 2: Миграция пациентов...")
        users_xlsx_path = os.path.join(current_dir, 'data', 'users.xlsx')
        if os.path.exists(users_xlsx_path):
            migrator.migrate_patients_from_xlsx(users_xlsx_path)
        else:
            print("⚠️ Файл users.xlsx не найден")

        print("📋 Шаг 3: Миграция данных тестирования...")
        boxbase_sources = [
            os.path.join(current_dir, 'data', 'boxbase.xlsx'),
            os.path.join(current_dir, 'data', 'boxbase.csv'),
        ]

        boxbase_source = None
        for source in boxbase_sources:
            if os.path.exists(source):
                boxbase_source = source
                break

        if boxbase_source:
            migrator.migrate_boxbase_data(boxbase_source)
        else:
            print("⚠️ Файлы boxbase не найдены")

        print("🧮 Шаг 4: Расчет нейромедиаторных метрик...")
        analyzer = NeurotransmitterAnalyzer()
        analyzer.calculate_all_metrics()

        print("\n✅ Миграция успешно завершена!")
        print("Теперь доступны новые функции анализа нейромедиаторной активности!")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

