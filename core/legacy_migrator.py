# core/legacy_migrator.py
import sqlite3
import json
import pandas as pd
from datetime import datetime
import os
import logging


class LegacyMigrator:
    def __init__(self, db_path='neuro_data.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

    def initialize_new_schema(self):
        """Создание новой схемы базы данных с поддержкой нейромедиаторного анализа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Удаляем старые таблицы если существуют (для чистоты миграции)
                conn.execute('DROP TABLE IF EXISTS raw_legacy_data')
                conn.execute('DROP TABLE IF EXISTS patients')
                conn.execute('DROP TABLE IF EXISTS testing_sessions')
                conn.execute('DROP TABLE IF EXISTS visual_tests')
                conn.execute('DROP TABLE IF EXISTS motor_tests')
                conn.execute('DROP TABLE IF EXISTS test_relationships')
                conn.execute('DROP TABLE IF EXISTS neurotransmitter_profiles')

                # Таблица для сырых исторических данных
                conn.execute('''
                             CREATE TABLE raw_legacy_data
                             (
                                 id           INTEGER PRIMARY KEY AUTOINCREMENT,
                                 source_table TEXT,
                                 original_id  INTEGER,
                                 raw_data     JSON,
                                 imported_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                             ''')

                # Основные таблицы пациентов
                conn.execute('''
                             CREATE TABLE patients
                             (
                                 id             INTEGER PRIMARY KEY AUTOINCREMENT,
                                 external_id    INTEGER,
                                 fname          TEXT,
                                 sname          TEXT,
                                 lname          TEXT,
                                 yborn          TEXT,
                                 regdate        TEXT,
                                 gender         INTEGER,
                                 legacy_data_id INTEGER,
                                 created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                             ''')

                # Таблица сессий тестирования
                conn.execute('''
                             CREATE TABLE testing_sessions
                             (
                                 id             INTEGER PRIMARY KEY AUTOINCREMENT,
                                 patient_id     INTEGER,
                                 session_date   TEXT,
                                 session_time   TEXT,
                                 systolic_bp    INTEGER,
                                 diastolic_bp   INTEGER,
                                 conditions     INTEGER,
                                 validity       INTEGER,
                                 legacy_data_id INTEGER,
                                 created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                             ''')

                # Таблица визуальных тестов
                conn.execute('''
                             CREATE TABLE visual_tests
                             (
                                 id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                                 session_id              INTEGER,
                                 test_type               TEXT,
                                 test_version            INTEGER  DEFAULT 1,
                                 raw_reaction_times      JSON,
                                 raw_metadata            JSON,
                                 raw_aggregates          JSON,
                                 calculated_metrics      JSON,
                                 neurotransmitter_scores JSON,
                                 statistical_analysis    JSON,
                                 analysis_version        TEXT     DEFAULT '1.0',
                                 is_processed            BOOLEAN  DEFAULT FALSE,
                                 processed_at            DATETIME,
                                 created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                             ''')

                print("✅ Новая схема базы данных создана")

        except Exception as e:
            print(f"❌ Ошибка создания схемы БД: {e}")
            raise

    def migrate_patients_from_xlsx(self, xlsx_path):
        """Миграция пациентов из users.xlsx"""
        try:
            df = pd.read_excel(xlsx_path)
            print(f"📊 Загружено {len(df)} пациентов из XLSX")

            with sqlite3.connect(self.db_path) as conn:
                for _, row in df.iterrows():
                    try:
                        # Сохраняем сырые данные
                        raw_data = row.to_dict()
                        cursor = conn.execute(
                            'INSERT INTO raw_legacy_data (source_table, original_id, raw_data) VALUES (?, ?, ?)',
                            ('users', row['ID'], json.dumps(raw_data, default=str))
                        )
                        legacy_id = cursor.lastrowid

                        # Создаем структурированную запись
                        conn.execute('''
                                     INSERT INTO patients
                                     (external_id, fname, sname, lname, yborn, regdate, gender, legacy_data_id)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                     ''', (
                                         row['ID'],
                                         str(row.get('FName', '')),
                                         str(row.get('SName', '')),
                                         str(row.get('LName', '')),
                                         str(row.get('YBorn', '')),
                                         str(row.get('RegDate', '')),
                                         row.get('Gender', 0),
                                         legacy_id
                                     ))
                    except Exception as e:
                        print(f"⚠️ Ошибка миграции пациента ID {row.get('ID', 'unknown')}: {e}")
                        continue

                print(f"✅ Мигрировано пациентов: {len(df)}")

        except Exception as e:
            print(f"❌ Ошибка миграции пациентов: {e}")
            import traceback
            traceback.print_exc()

    def migrate_boxbase_data(self, source_path):
        """Миграция данных тестирования из boxbase"""
        try:
            # Загрузка данных
            if source_path.endswith('.xlsx'):
                data = pd.read_excel(source_path)
            elif source_path.endswith('.csv'):
                data = pd.read_csv(source_path)
            else:
                print(f"⚠️ Формат не поддерживается: {source_path}")
                return

            print(f"📊 Загружено {len(data)} записей тестирования")

            migrated_sessions = 0
            migrated_tests = 0

            with sqlite3.connect(self.db_path) as conn:
                # Создаем mapping external_id -> internal_id
                cursor = conn.execute("SELECT id, external_id FROM patients")
                patient_mapping = {row[1]: row[0] for row in cursor.fetchall()}
                print(f"🔍 Создан mapping пациентов: {len(patient_mapping)} записей")

                for _, record in data.iterrows():
                    try:
                        session_id = self._migrate_single_test_session(conn, record, patient_mapping)
                        if session_id:
                            migrated_sessions += 1
                            migrated_tests += 3  # По три теста на сессию
                    except Exception as e:
                        session_id = record.get('cnt', 'unknown')
                        print(f"⚠️ Ошибка миграции сессии {session_id}: {e}")
                        continue

            print(f"✅ Мигрировано сессий: {migrated_sessions}, тестов: {migrated_tests}")

        except Exception as e:
            print(f"❌ Ошибка миграции boxbase: {e}")
            import traceback
            traceback.print_exc()

    def _migrate_single_test_session(self, conn, record, patient_mapping):
        """Миграция одной сессии тестирования"""
        try:
            reg_id = record.get('REG_ID')
            if reg_id not in patient_mapping:
                print(f"⚠️ Пропущена сессия: пациент REG_ID={reg_id} не найден в mapping")
                return None

            patient_id = patient_mapping[reg_id]

            # Сохранение сырых данных
            cursor = conn.execute(
                'INSERT INTO raw_legacy_data (source_table, original_id, raw_data) VALUES (?, ?, ?)',
                ('boxbase', record.get('cnt'), json.dumps(record.to_dict(), default=str))
            )
            legacy_id = cursor.lastrowid

            # Создание сессии тестирования
            cursor = conn.execute('''
                                  INSERT INTO testing_sessions
                                  (patient_id, session_date, session_time, systolic_bp, diastolic_bp,
                                   conditions, validity, legacy_data_id)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                  ''', (
                                      patient_id,  # Используем internal patient_id
                                      str(record.get('CurrentDate', '')),
                                      str(record.get('CurrentTime', '')),
                                      record.get('AD1'),
                                      record.get('AD2'),
                                      record.get('VidSost_txt'),
                                      record.get('VidSost'),
                                      legacy_id
                                  ))
            session_id = cursor.lastrowid

            # Миграция трех тестов
            self._migrate_visual_test(conn, session_id, 'simple_color', record, 'Tst1')
            self._migrate_visual_test(conn, session_id, 'color_red', record, 'Tst2')
            self._migrate_visual_test(conn, session_id, 'shift', record, 'Tst3')

            return session_id

        except Exception as e:
            print(f"❌ Ошибка миграции сессии: {e}")
            return None

    def _migrate_visual_test(self, conn, session_id, test_type, record, prefix):
        """Миграция отдельного визуального теста"""
        try:
            # Сбор сырых данных реакций
            reaction_times = []
            for i in range(1, 37):
                col_name = f'{prefix}_{i}'
                reaction_times.append(record.get(col_name))

            # Сбор агрегированных данных
            aggregates = {
                'result': record.get(f'result_{prefix[-1]}'),
                'std_dev': record.get(f'SrKvadrOtkl_{prefix[-1]}'),
                'early_responses': record.get(f'RANO_POKAZ_{prefix[-1]}', 0),
                'late_responses': record.get(f'POZDNO_POKAZ_{prefix[-1]}', 0)
            }

            conn.execute('''
                         INSERT INTO visual_tests
                             (session_id, test_type, raw_reaction_times, raw_aggregates)
                         VALUES (?, ?, ?, ?)
                         ''', (
                             session_id,
                             test_type,
                             json.dumps(reaction_times),
                             json.dumps(aggregates)
                         ))

        except Exception as e:
            print(f"⚠️ Ошибка миграции теста {test_type}: {e}")

    def verify_migration(self):
        """Проверка корректности миграции данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Проверяем пациентов
                cursor.execute("SELECT COUNT(*) FROM patients")
                patients_count = cursor.fetchone()[0]

                # Проверяем сессии тестирования
                cursor.execute("SELECT COUNT(*) FROM testing_sessions")
                sessions_count = cursor.fetchone()[0]

                # Проверяем визуальные тесты
                cursor.execute("SELECT COUNT(*) FROM visual_tests")
                tests_count = cursor.fetchone()[0]

                # Проверяем связь пациентов и сессий
                cursor.execute("""
                               SELECT COUNT(DISTINCT ts.patient_id)
                               FROM testing_sessions ts
                                        JOIN patients p ON ts.patient_id = p.id
                               """)
                linked_patients = cursor.fetchone()[0]

                print(f"🔍 ПРОВЕРКА МИГРАЦИИ:")
                print(f"   • Пациентов: {patients_count}")
                print(f"   • Сессий тестирования: {sessions_count}")
                print(f"   • Визуальных тестов: {tests_count}")
                print(f"   • Пациентов с тестами: {linked_patients}")

                # Проверяем несколько конкретных пациентов
                cursor.execute("""
                               SELECT p.id, p.external_id, p.fname, p.lname, COUNT(ts.id) as session_count
                               FROM patients p
                                        LEFT JOIN testing_sessions ts ON p.id = ts.patient_id
                               GROUP BY p.id LIMIT 5
                               """)
                sample_patients = cursor.fetchall()

                print(f"   • Пример пациентов:")
                for patient in sample_patients:
                    print(
                        f"     - ID:{patient[0]}, External:{patient[1]}, Name:{patient[2]} {patient[3]}, Sessions:{patient[4]}")

                # Проверяем структуру данных для нескольких сессий
                cursor.execute("""
                               SELECT ts.id, ts.patient_id, p.external_id, COUNT(vt.id) as test_count
                               FROM testing_sessions ts
                                        JOIN patients p ON ts.patient_id = p.id
                                        LEFT JOIN visual_tests vt ON ts.id = vt.session_id
                               GROUP BY ts.id LIMIT 3
                               """)
                sample_sessions = cursor.fetchall()

                print(f"   • Пример сессий:")
                for session in sample_sessions:
                    print(
                        f"     - Session ID:{session[0]}, Patient ID:{session[1]}, External ID:{session[2]}, Tests:{session[3]}")

                return {
                    'patients_count': patients_count,
                    'sessions_count': sessions_count,
                    'tests_count': tests_count,
                    'linked_patients': linked_patients,
                    'sample_patients': sample_patients,
                    'sample_sessions': sample_sessions
                }

        except Exception as e:
            print(f"❌ Ошибка проверки миграции: {e}")
            return None

    def run_complete_migration(self, users_path=None, boxbase_path=None):
        """Полная миграция всех данных"""
        try:
            print("🚀 Запуск полной миграции данных")
            print("=" * 50)

            # 1. Инициализация новой схемы
            print("📊 Шаг 1: Создание новой схемы БД...")
            self.initialize_new_schema()

            # 2. Миграция пациентов
            if users_path and os.path.exists(users_path):
                print(f"👥 Шаг 2: Миграция пациентов из {os.path.basename(users_path)}...")
                self.migrate_patients_from_xlsx(users_path)
            else:
                print("⚠️ Файл patients не указан или не найден")

            # 3. Миграция данных тестирования
            if boxbase_path and os.path.exists(boxbase_path):
                print(f"📋 Шаг 3: Миграция данных тестирования из {os.path.basename(boxbase_path)}...")
                self.migrate_boxbase_data(boxbase_path)
            else:
                print("⚠️ Файл тестирования не указан или не найден")

            # 4. Проверка результатов
            print("🔍 Шаг 4: Проверка результатов миграции...")
            verification = self.verify_migration()

            if verification and verification['sessions_count'] > 0:
                print("\n🎉 Миграция успешно завершена!")
                print("Теперь доступны новые функции анализа нейромедиаторной активности!")
            else:
                print("\n⚠️ Миграция завершена с ограничениями")
                print("Некоторые данные могут быть недоступны")

            return verification

        except Exception as e:
            print(f"❌ Критическая ошибка миграции: {e}")
            import traceback
            traceback.print_exc()
            return None


# Утилитарные функции для использования в других модулях
def verify_migration(db_path='neuro_data.db'):
    """Проверить корректность миграции"""
    migrator = LegacyMigrator(db_path)
    return migrator.verify_migration()


def run_migration(users_path, boxbase_path, db_path='neuro_data.db'):
    """Запустить миграцию"""
    migrator = LegacyMigrator(db_path)
    return migrator.run_complete_migration(users_path, boxbase_path)


if __name__ == "__main__":
    # Пример использования
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', 'data')

    users_path = os.path.join(data_dir, 'users.xlsx')
    boxbase_path = os.path.join(data_dir, 'boxbase.xlsx')

    migrator = LegacyMigrator()
    migrator.run_complete_migration(users_path, boxbase_path)

