# update_metadata.py
"""
Утилита для добавления таблиц метаданных в существующую базу данных
"""
import logging
import sqlite3
from utils.database_migration_v2 import DatabaseMigrationV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("🔄 Запуск обновления метаданных тестирования...")

    migrator = DatabaseMigrationV2("neuro_data.db")

    # Проверяем текущую версию
    current_version = migrator.check_schema_version()
    print(f"🔍 Текущая версия схемы: {current_version}")

    if current_version == "v2_metadata":
        print("✅ Таблицы метаданных уже существуют")
        # Покажем текущее состояние
        show_current_metadata()

        response = input("Перезаписать метаданные полными данными? (y/n): ")
        if response.lower() not in ['y', 'yes', 'д', 'да']:
            return True
    else:
        print("❌ Таблицы метаданных не найдены, создаем...")

    try:
        # Создаем резервную копию
        print("🔄 Создание резервной копии...")
        backup_path = migrator.backup_database()

        # Подключаемся к БД
        conn = sqlite3.connect("neuro_data.db")

        # Создаем таблицы метаданных
        print("🔄 Создание таблиц метаданных...")
        migrator.create_metadata_tables(conn)

        # Заполняем полными данными
        print("🔄 Заполнение полными метаданными всех тестов...")
        migrator.populate_metadata_tables(conn)

        conn.close()

        # Проверяем результат
        new_version = migrator.check_schema_version()
        if new_version == "v2_metadata":
            print("🎉 Таблицы метаданных успешно добавлены с полными данными!")

            # Показываем созданные данные
            show_metadata_summary()
            return True
        else:
            print("❌ Ошибка: таблицы метаданных не созданы")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка обновления метаданных: {e}")
        return False


def show_current_metadata():
    """Показать текущее состояние метаданных"""
    try:
        conn = sqlite3.connect("neuro_data.db")
        cursor = conn.cursor()

        # Количество тестовых метаданных по типам
        cursor.execute("SELECT test_type, COUNT(*) FROM test_metadata GROUP BY test_type")
        test_counts = cursor.fetchall()
        print("\n📊 Текущие метаданные в БД:")
        for test_type, count in test_counts:
            print(f"   • {test_type}: {count} стимулов")

        # Системные параметры
        cursor.execute("SELECT COUNT(*) FROM testing_system_parameters")
        param_count = cursor.fetchone()[0]
        print(f"   • Системные параметры: {param_count} шт.")

        conn.close()

    except Exception as e:
        print(f"⚠️ Ошибка при показе текущих метаданных: {e}")


def show_metadata_summary():
    """Показать сводку по созданным метаданным"""
    try:
        conn = sqlite3.connect("neuro_data.db")
        cursor = conn.cursor()

        # Детальная статистика по тестам
        test_types = ["simple", "color_red", "shift"]
        print("\n📊 СОЗДАННЫЕ МЕТАДАННЫЕ ТЕСТИРОВАНИЯ:")
        print("=" * 50)

        for test_type in test_types:
            # Количество стимулов
            cursor.execute("SELECT COUNT(*) FROM test_metadata WHERE test_type = ?", (test_type,))
            count = cursor.fetchone()[0]

            # Статистика по цветам
            cursor.execute("""
                           SELECT color, COUNT(*)
                           FROM test_metadata
                           WHERE test_type = ?
                           GROUP BY color
                           """, (test_type,))
            color_stats = cursor.fetchall()

            # Статистика по позициям
            cursor.execute("""
                           SELECT position, COUNT(*)
                           FROM test_metadata
                           WHERE test_type = ?
                           GROUP BY position
                           """, (test_type,))
            position_stats = cursor.fetchall()

            print(f"🎯 Тест: {test_type}")
            print(f"   📊 Стимулов: {count}")
            print(f"   🎨 Цвета: {', '.join([f'{color} ({count})' for color, count in color_stats])}")
            print(f"   📍 Позиции: {', '.join([f'{pos} ({count})' for pos, count in position_stats])}")

            # Показать диапазон интервалов
            cursor.execute("""
                           SELECT MIN(prestimulus_interval), MAX(prestimulus_interval), AVG(prestimulus_interval)
                           FROM test_metadata
                           WHERE test_type = ?
                           """, (test_type,))
            min_int, max_int, avg_int = cursor.fetchone()
            print(f"   ⏱️  Интервалы: {min_int}-{max_int}ms (среднее: {avg_int:.0f}ms)")

            # Для теста со смещением показать параметры смещения
            if test_type == "shift":
                cursor.execute("""
                               SELECT DISTINCT shift_parameter, COUNT(*)
                               FROM test_metadata
                               WHERE test_type = 'shift'
                                 AND shift_parameter IS NOT NULL
                               GROUP BY shift_parameter
                               """)
                shift_stats = cursor.fetchall()
                if shift_stats:
                    print(f"   🔄 Смещения: {', '.join([f'{shift} ({count})' for shift, count in shift_stats])}")

            print()

        # Системные параметры
        print("⚙️ СИСТЕМНЫЕ ПАРАМЕТРЫ:")
        cursor.execute("SELECT parameter_name, parameter_value FROM testing_system_parameters")
        for name, value in cursor.fetchall():
            print(f"   • {name}: {value}")

        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM test_metadata")
        total_stimuli = cursor.fetchone()[0]
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   • Всего стимулов: {total_stimuli}")
        print(f"   • Всего тестов: {len(test_types)}")
        cursor.execute("SELECT COUNT(*) FROM testing_system_parameters")
        param_count = cursor.fetchone()[0]
        print(f"   • Всего параметров: {param_count}")

        conn.close()

    except Exception as e:
        print(f"⚠️ Ошибка при показе сводки: {e}")


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Обновление метаданных завершено успешно!")
        print("🚀 Теперь можно использовать полные метаданные в тестировании")
        print("💡 Перезапустите main.py для загрузки обновленных метаданных")
    else:
        print("\n❌ Обновление метаданных завершилось с ошибкой")

