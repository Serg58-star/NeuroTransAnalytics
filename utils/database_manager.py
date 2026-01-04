# utils/database_manager.py
import argparse
from core.legacy_migrator import LegacyMigrator
from core.neuro_analyzer import NeurotransmitterAnalyzer


def main():
    parser = argparse.ArgumentParser(description='Управление базой данных NeuroTransAnalytics')
    parser.add_argument('--migrate', action='store_true', help='Запустить миграцию данных')
    parser.add_argument('--analyze', action='store_true', help='Пересчитать аналитические метрики')
    parser.add_argument('--backup', help='Создать бэкап базы данных')

    args = parser.parse_args()

    if args.migrate:
        print("Запуск миграции...")
        migrator = LegacyMigrator()
        migrator.initialize_new_schema()
        migrator.migrate_patients_from_xlsx('data/users.xlsx')
        migrator.migrate_boxbase_data('data/boxbase.csv')

    if args.analyze:
        print("Пересчет метрик...")
        analyzer = NeurotransmitterAnalyzer()
        analyzer.calculate_all_metrics()

    print("Операция завершена")


if __name__ == "__main__":
    main()