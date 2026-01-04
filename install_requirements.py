# install_requirements.py
import subprocess
import sys
import os


def install_requirements():
    """Установка необходимых пакетов"""
    packages = [
        'pandas',
        'pyodbc',
        'openpyxl',
        'xlrd'
    ]

    print("🔄 Установка необходимых пакетов...")

    for package in packages:
        try:
            print(f"📦 Устанавливаю {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} успешно установлен")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки {package}: {e}")

    print("\n🎯 Проверка доступности драйверов Access...")
    check_access_drivers()


def check_access_drivers():
    """Проверка доступных драйверов Access"""
    try:
        import pyodbc
        drivers = pyodbc.drivers()
        access_drivers = [d for d in drivers if any(keyword in d.lower() for keyword in ['access', 'mdb', 'ace'])]

        if access_drivers:
            print("✅ Найдены драйверы Access:")
            for driver in access_drivers:
                print(f"   - {driver}")
        else:
            print("❌ Драйверы Access не найдены")
            print("\n📋 Для работы с Access файлами необходимо:")
            print("   1. Скачать и установить Microsoft Access Database Engine 2016 Redistributable")
            print("   2. Скачать можно с официального сайта Microsoft")
            print("   3. Выберите версию соответствующую разрядности вашей системы (x86 или x64)")
            print("   4. Перезапустите приложение после установки")

    except ImportError:
        print("❌ PyODBC не установлен")


if __name__ == "__main__":
    install_requirements()