# test_access.py
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.data_loader import DataLoader


def test_access_loading():
    """Тестирование загрузки Access файлов"""
    print("🧪 ТЕСТИРОВАНИЕ ACCESS ЗАГРУЗКИ")
    print("=" * 50)

    loader = DataLoader()

    # Проверяем доступность драйверов
    available, message = loader.check_pyodbc_available()
    print(f"🔧 Доступность Access: {available}")
    print(f"📝 Сообщение: {message}")

    # Показываем информацию о данных
    info = loader.get_data_info()
    print(f"\n📊 Информация о данных:")
    print(f"   Access драйверы доступны: {info['access_drivers_available']}")
    print(f"   Найдены драйверы: {info['available_access_drivers']}")

    print("\n✅ Система готова к работе с Access файлами!")
    print("\n💡 Инструкция:")
    print("   1. Запустите main.py")
    print("   2. Во вкладке 'Загрузка данных' выберите Access файл")
    print("   3. Нажмите одну из кнопок загрузки")

    loader.close_connection()


if __name__ == "__main__":
    test_access_loading()