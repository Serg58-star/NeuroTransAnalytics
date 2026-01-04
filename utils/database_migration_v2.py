# utils/database_migration_v2.py
import sqlite3
import os
import logging
import sys
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class DatabaseMigrationV2:
    def __init__(self, db_path="neuro_data.db"):
        self.db_path = db_path

    def backup_database(self):
        """Создание резервной копии базы данных"""
        try:
            if os.path.exists(self.db_path):
                backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"✅ Резервная копия создана: {backup_path}")
                return backup_path
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка создания резервной копии: {e}")
            return None

    def check_schema_version(self):
        """Проверка версии схемы базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Проверяем существование таблицы analysis_results (новая схема v2)
            cursor.execute("""
                           SELECT name
                           FROM sqlite_master
                           WHERE type = 'table'
                             AND name = 'analysis_results'
                           """)
            has_v2_schema = cursor.fetchone() is not None

            # Проверяем существование таблиц метаданных (v2 с метаданными)
            cursor.execute("""
                           SELECT name
                           FROM sqlite_master
                           WHERE type = 'table'
                             AND name = 'test_metadata'
                           """)
            has_metadata_schema = cursor.fetchone() is not None

            # Проверяем существование старой схемы (v1)
            cursor.execute("""
                           SELECT name
                           FROM sqlite_master
                           WHERE type = 'table'
                             AND name = 'users'
                           """)
            has_v1_schema = cursor.fetchone() is not None

            conn.close()

            if has_metadata_schema:
                return "v2_metadata"
            elif has_v2_schema:
                return "v2"
            elif has_v1_schema:
                return "v1"
            else:
                return "none"

        except Exception as e:
            logger.error(f"❌ Ошибка проверки схемы БД: {e}")
            return "error"

    def create_metadata_tables(self, conn):
        """Создать таблицы для метаданных тестирования"""
        cursor = conn.cursor()

        # Таблица: предопределенные последовательности тестов
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS test_metadata
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           test_type
                           VARCHAR
                       (
                           20
                       ) NOT NULL,
                           stimulus_number INTEGER NOT NULL,
                           color VARCHAR
                       (
                           10
                       ) NOT NULL,
                           position VARCHAR
                       (
                           10
                       ) NOT NULL,
                           prestimulus_interval INTEGER NOT NULL,
                           circle_sequence TEXT,
                           shift_parameter INTEGER,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           UNIQUE
                       (
                           test_type,
                           stimulus_number
                       )
                           )
                       """)

        # Таблица: системные параметры тестирования
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS testing_system_parameters
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY,
                           parameter_name
                           VARCHAR
                       (
                           50
                       ) NOT NULL UNIQUE,
                           parameter_value VARCHAR
                       (
                           100
                       ) NOT NULL,
                           description TEXT,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                           )
                       """)

        logger.info("✅ Таблицы метаданных тестирования созданы")

    def populate_metadata_tables(self, conn):
        """Заполнить таблицы метаданных полными данными из core.test_metadata"""
        try:
            cursor = conn.cursor()

            # Очистить существующие данные
            cursor.execute("DELETE FROM test_metadata")
            cursor.execute("DELETE FROM testing_system_parameters")

            # Импортируем и используем полные данные из core.test_metadata
            from core.test_metadata import metadata_manager, SYSTEM_PARAMETERS

            # Используем системные параметры из core.test_metadata
            system_parameters = [
                ("MaxRedLight", "2000", "Максимальное количество красных стимулов"),
                ("MinRedLight", "135", "Минимальное количество красных стимулов"),
                ("ROTATE_PERIOD", "400", "Период вращения кругов (мс)"),
                ("POKAZ_COUNT", "36", "Количество показаний в тесте"),
                ("NoUchtPOKAZ_COUNT", "3", "Количество неучтенных показаний"),
                ("STIMULUS_DURATION", "1000", "Длительность стимула (мс)"),
                ("PRESTIMULUS_INTERVAL", "2000", "Интервал перед стимулом (мс)"),
                ("TOTAL_STIMULI", "36", "Общее количество стимулов в тесте"),
                ("CIRCLE_COUNT", "3", "Количество кругов в интерфейсе")
            ]

            # Вставить системные параметры
            for param_name, param_value, description in system_parameters:
                cursor.execute("""
                    INSERT OR REPLACE INTO testing_system_parameters 
                    (parameter_name, parameter_value, description)
                    VALUES (?, ?, ?)
                """, (param_name, param_value, description))

            # Вставить полные данные всех трех тестов из metadata_manager
            all_test_data = []
            test_types = ["simple", "color_red", "shift"]

            for test_type in test_types:
                test_meta = metadata_manager.get_test_metadata(test_type)
                if test_meta:
                    for stimulus in test_meta.stimuli:
                        all_test_data.append((
                            test_type,
                            stimulus.stimulus_number,
                            stimulus.color,
                            stimulus.position,
                            stimulus.prestimulus_interval,
                            stimulus.circle_sequence,
                            stimulus.shift_parameter
                        ))

            # Вставить все тестовые данные
            for test_data in all_test_data:
                cursor.execute("""
                    INSERT OR REPLACE INTO test_metadata 
                    (test_type, stimulus_number, color, position, prestimulus_interval, circle_sequence, shift_parameter)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, test_data)

            conn.commit()

            # Логируем детальную статистику
            logger.info(f"✅ Метаданные заполнены: {len(all_test_data)} стимулов, {len(system_parameters)} параметров")

            for test_type in test_types:
                cursor.execute("SELECT COUNT(*) FROM test_metadata WHERE test_type = ?", (test_type,))
                count = cursor.fetchone()[0]
                logger.info(f"   • {test_type}: {count} стимулов")

        except Exception as e:
            logger.error(f"❌ Ошибка заполнения метаданных: {e}")
            conn.rollback()
            raise

    def create_advanced_schema(self):
        """Создание расширенной схемы v2"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица для основных результатов анализа
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS analysis_results
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           patient_id
                           INTEGER
                           NOT
                           NULL,
                           session_id
                           INTEGER
                           NOT
                           NULL,
                           analysis_method
                           VARCHAR
                       (
                           50
                       ) NOT NULL,

                           -- Базовые показатели по позициям
                           left_v1 FLOAT, left_delta_v4 FLOAT, left_delta_v5_mt FLOAT,
                           center_v1 FLOAT, center_delta_v4 FLOAT, center_delta_v5_mt FLOAT,
                           right_v1 FLOAT, right_delta_v4 FLOAT, right_delta_v5_mt FLOAT,

                           -- Агрегированные показатели
                           overall_v1 FLOAT, overall_delta_v4 FLOAT, overall_delta_v5_mt FLOAT,

                           -- Метрики качества данных
                           data_quality_score FLOAT,
                           sample_sizes TEXT,

                           -- Метadata
                           analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY
                       (
                           patient_id
                       ) REFERENCES patients
                       (
                           id
                       ),
                           FOREIGN KEY
                       (
                           session_id
                       ) REFERENCES testing_sessions
                       (
                           id
                       )
                           )
                       """)

        # Таблица для анализа динамики
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS longitudinal_analysis
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           patient_id
                           INTEGER
                           NOT
                           NULL,
                           baseline_session_id
                           INTEGER
                           NOT
                           NULL,
                           followup_session_id
                           INTEGER
                           NOT
                           NULL,
                           time_interval_days
                           INTEGER,

                           -- Изменения по позициям
                           delta_left_v1
                           FLOAT,
                           delta_left_delta_v4
                           FLOAT,
                           delta_left_delta_v5_mt
                           FLOAT,
                           delta_center_v1
                           FLOAT,
                           delta_center_delta_v4
                           FLOAT,
                           delta_center_delta_v5_mt
                           FLOAT,
                           delta_right_v1
                           FLOAT,
                           delta_right_delta_v4
                           FLOAT,
                           delta_right_delta_v5_mt
                           FLOAT,

                           -- Статистическая значимость
                           statistical_significance
                           TEXT,
                           clinical_significance
                           BOOLEAN,
                           significance_notes
                           TEXT,

                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,

                           FOREIGN
                           KEY
                       (
                           patient_id
                       ) REFERENCES patients
                       (
                           id
                       ),
                           FOREIGN KEY
                       (
                           baseline_session_id
                       ) REFERENCES testing_sessions
                       (
                           id
                       ),
                           FOREIGN KEY
                       (
                           followup_session_id
                       ) REFERENCES testing_sessions
                       (
                           id
                       )
                           )
                       """)

        # Таблица для исследовательских инсайтов
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS research_insights
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           insight_type
                           VARCHAR
                       (
                           50
                       ) NOT NULL,
                           patient_group TEXT,
                           findings TEXT NOT NULL,
                           confidence_score FLOAT,
                           visualization_parameters TEXT,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                           )
                       """)

        # ⭐ НОВЫЕ ТАБЛИЦЫ: Метаданные тестирования
        self.create_metadata_tables(conn)

        # Индексы для производительности
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_patient ON analysis_results(patient_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_session ON analysis_results(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_method ON analysis_results(analysis_method)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_longitudinal_patient ON longitudinal_analysis(patient_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON research_insights(insight_type)")

        # Новые индексы для метаданных
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_test_type ON test_metadata(test_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_stimulus ON test_metadata(stimulus_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_params_name ON testing_system_parameters(parameter_name)")

        # Заполняем таблицы метаданных полными данными
        self.populate_metadata_tables(conn)

        conn.commit()
        conn.close()
        logger.info("✅ Расширенная схема БД v2 создана (включая полные метаданные)")

    def run_migration(self):
        """Запуск полной миграции на схему v2"""
        logger.info("🔄 Запуск миграции базы данных v2...")

        if not os.path.exists(self.db_path):
            logger.error("❌ База данных не найдена")
            return False

        try:
            # Проверяем текущую версию
            current_version = self.check_schema_version()
            logger.info(f"🔍 Текущая версия схемы: {current_version}")

            if current_version == "v2_metadata":
                logger.info("✅ База данных уже использует схему v2 с метаданными")
                return True

            # Создаем резервную копию
            logger.info("🔄 Создание резервной копии...")
            backup_path = self.backup_database()

            # Создаем новую схему
            self.create_advanced_schema()

            # Проверяем результат
            new_version = self.check_schema_version()
            if new_version == "v2_metadata":
                logger.info("🎉 Миграция на схему v2 с метаданными завершена успешно")
                return True
            else:
                logger.error("❌ Миграция завершилась, но схема не обновлена")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            return False


# Функция для удобного импорта
def run_database_migration_v2(db_path="neuro_data.db"):
    """Запуск миграции v2 (удобная функция для импорта)"""
    migrator = DatabaseMigrationV2(db_path)
    return migrator.run_migration()


def check_database_schema_version(db_path="neuro_data.db"):
    """Проверка версии схемы (удобная функция для импорта)"""
    migrator = DatabaseMigrationV2(db_path)
    return migrator.check_schema_version()


def backup_database(db_path="neuro_data.db"):
    """Создание резервной копии (удобная функция для импорта)"""
    migrator = DatabaseMigrationV2(db_path)
    return migrator.backup_database()


def update_test_metadata(db_path="neuro_data.db"):
    """Обновить метаданные тестирования в базе данных (полные данные)"""
    migrator = DatabaseMigrationV2(db_path)
    try:
        conn = sqlite3.connect(db_path)
        migrator.create_metadata_tables(conn)
        migrator.populate_metadata_tables(conn)
        conn.close()
        logger.info("✅ Метаданные тестирования обновлены (полные данные всех тестов)")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка обновления метаданных: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrator = DatabaseMigrationV2()
    success = migrator.run_migration()
    sys.exit(0 if success else 1)


# # utils/database_migration_v2.py
# import sqlite3
# import os
# import logging
# import sys
# from datetime import datetime
# import shutil
#
# logger = logging.getLogger(__name__)
#
#
# class DatabaseMigrationV2:
#     def __init__(self, db_path="neuro_data.db"):
#         self.db_path = db_path
#
#     def backup_database(self):
#         """Создание резервной копии базы данных"""
#         try:
#             if os.path.exists(self.db_path):
#                 backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#                 shutil.copy2(self.db_path, backup_path)
#                 logger.info(f"✅ Резервная копия создана: {backup_path}")
#                 return backup_path
#             return None
#         except Exception as e:
#             logger.error(f"❌ Ошибка создания резервной копии: {e}")
#             return None
#
#     def check_schema_version(self):
#         """Проверка версии схемы базы данных"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             # Проверяем существование таблицы analysis_results (новая схема v2)
#             cursor.execute("""
#                            SELECT name
#                            FROM sqlite_master
#                            WHERE type = 'table'
#                              AND name = 'analysis_results'
#                            """)
#             has_v2_schema = cursor.fetchone() is not None
#
#             # Проверяем существование таблиц метаданных (v2 с метаданными)
#             cursor.execute("""
#                            SELECT name
#                            FROM sqlite_master
#                            WHERE type = 'table'
#                              AND name = 'test_metadata'
#                            """)
#             has_metadata_schema = cursor.fetchone() is not None
#
#             # Проверяем существование старой схемы (v1)
#             cursor.execute("""
#                            SELECT name
#                            FROM sqlite_master
#                            WHERE type = 'table'
#                              AND name = 'users'
#                            """)
#             has_v1_schema = cursor.fetchone() is not None
#
#             conn.close()
#
#             if has_metadata_schema:
#                 return "v2_metadata"
#             elif has_v2_schema:
#                 return "v2"
#             elif has_v1_schema:
#                 return "v1"
#             else:
#                 return "none"
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка проверки схемы БД: {e}")
#             return "error"
#
#     def create_metadata_tables(self, conn):
#         """Создать таблицы для метаданных тестирования"""
#         cursor = conn.cursor()
#
#         # Таблица: предопределенные последовательности тестов
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS test_metadata
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            test_type
#                            VARCHAR
#                        (
#                            20
#                        ) NOT NULL,
#                            stimulus_number INTEGER NOT NULL,
#                            color VARCHAR
#                        (
#                            10
#                        ) NOT NULL,
#                            position VARCHAR
#                        (
#                            10
#                        ) NOT NULL,
#                            prestimulus_interval INTEGER NOT NULL,
#                            circle_sequence TEXT,
#                            shift_parameter INTEGER,
#                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            UNIQUE
#                        (
#                            test_type,
#                            stimulus_number
#                        )
#                            )
#                        """)
#
#         # Таблица: системные параметры тестирования
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS testing_system_parameters
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY,
#                            parameter_name
#                            VARCHAR
#                        (
#                            50
#                        ) NOT NULL UNIQUE,
#                            parameter_value VARCHAR
#                        (
#                            100
#                        ) NOT NULL,
#                            description TEXT,
#                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                            )
#                        """)
#
#         logger.info("✅ Таблицы метаданных тестирования созданы")
#
#     def populate_metadata_tables(self, conn):
#         """Заполнить таблицы метаданных начальными данными"""
#         try:
#             cursor = conn.cursor()
#
#             # Очистить существующие данные
#             cursor.execute("DELETE FROM test_metadata")
#             cursor.execute("DELETE FROM testing_system_parameters")
#
#             # Базовые системные параметры тестирования
#             system_parameters = [
#                 ("MaxRedLight", "5", "Максимальное количество красных стимулов"),
#                 ("MinRedLight", "2", "Минимальное количество красных стимулов"),
#                 ("ROTATE_PERIOD", "5000", "Период вращения кругов (мс)"),
#                 ("STIMULUS_DURATION", "1000", "Длительность стимула (мс)"),
#                 ("PRESTIMULUS_INTERVAL", "2000", "Интервал перед стимулом (мс)"),
#                 ("TOTAL_STIMULI", "15", "Общее количество стимулов в тесте"),
#                 ("CIRCLE_COUNT", "3", "Количество кругов в интерфейсе")
#             ]
#
#             # Вставить системные параметры
#             for param_name, param_value, description in system_parameters:
#                 cursor.execute("""
#                     INSERT OR REPLACE INTO testing_system_parameters
#                     (parameter_name, parameter_value, description)
#                     VALUES (?, ?, ?)
#                 """, (param_name, param_value, description))
#
#             # Базовые метаданные тестов
#             # Простой тест (simple)
#             simple_test_data = [
#                 ("simple", 1, "red", "left", 2000, "circle1,circle2,circle3", None),
#                 ("simple", 2, "green", "center", 2000, "circle1,circle2,circle3", None),
#                 ("simple", 3, "red", "right", 2000, "circle1,circle2,circle3", None),
#                 ("simple", 4, "green", "left", 2000, "circle1,circle2,circle3", None),
#                 ("simple", 5, "green", "center", 2000, "circle1,circle2,circle3", None),
#             ]
#
#             # Тест со смещением (shift)
#             shift_test_data = [
#                 ("shift", 1, "red", "left", 2000, "circle1,circle2,circle3", 1),
#                 ("shift", 2, "green", "center", 2000, "circle1,circle2,circle3", 2),
#                 ("shift", 3, "red", "right", 2000, "circle1,circle2,circle3", 1),
#                 ("shift", 4, "green", "left", 2000, "circle1,circle2,circle3", 3),
#                 ("shift", 5, "green", "center", 2000, "circle1,circle2,circle3", 2),
#             ]
#
#             # Вставить все тестовые данные
#             all_test_data = simple_test_data + shift_test_data
#
#             for test_data in all_test_data:
#                 cursor.execute("""
#                                INSERT INTO test_metadata
#                                (test_type, stimulus_number, color, position, prestimulus_interval, circle_sequence,
#                                 shift_parameter)
#                                VALUES (?, ?, ?, ?, ?, ?, ?)
#                                """, test_data)
#
#             conn.commit()
#             logger.info(f"✅ Метаданные заполнены: {len(all_test_data)} стимулов, {len(system_parameters)} параметров")
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка заполнения метаданных: {e}")
#             conn.rollback()
#             raise
#
#     def create_advanced_schema(self):
#         """Создание расширенной схемы v2"""
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#
#         # Таблица для основных результатов анализа
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS analysis_results
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            patient_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            analysis_method
#                            VARCHAR
#                        (
#                            50
#                        ) NOT NULL,
#
#                            -- Базовые показатели по позициям
#                            left_v1 FLOAT, left_delta_v4 FLOAT, left_delta_v5_mt FLOAT,
#                            center_v1 FLOAT, center_delta_v4 FLOAT, center_delta_v5_mt FLOAT,
#                            right_v1 FLOAT, right_delta_v4 FLOAT, right_delta_v5_mt FLOAT,
#
#                            -- Агрегированные показатели
#                            overall_v1 FLOAT, overall_delta_v4 FLOAT, overall_delta_v5_mt FLOAT,
#
#                            -- Метрики качества данных
#                            data_quality_score FLOAT,
#                            sample_sizes TEXT,
#
#                            -- Метadata
#                            analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            FOREIGN KEY
#                        (
#                            patient_id
#                        ) REFERENCES patients
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        )
#                            )
#                        """)
#
#         # Таблица для анализа динамики
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS longitudinal_analysis
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            patient_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            baseline_session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            followup_session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            time_interval_days
#                            INTEGER,
#
#                            -- Изменения по позициям
#                            delta_left_v1
#                            FLOAT,
#                            delta_left_delta_v4
#                            FLOAT,
#                            delta_left_delta_v5_mt
#                            FLOAT,
#                            delta_center_v1
#                            FLOAT,
#                            delta_center_delta_v4
#                            FLOAT,
#                            delta_center_delta_v5_mt
#                            FLOAT,
#                            delta_right_v1
#                            FLOAT,
#                            delta_right_delta_v4
#                            FLOAT,
#                            delta_right_delta_v5_mt
#                            FLOAT,
#
#                            -- Статистическая значимость
#                            statistical_significance
#                            TEXT,
#                            clinical_significance
#                            BOOLEAN,
#                            significance_notes
#                            TEXT,
#
#                            created_at
#                            TIMESTAMP
#                            DEFAULT
#                            CURRENT_TIMESTAMP,
#
#                            FOREIGN
#                            KEY
#                        (
#                            patient_id
#                        ) REFERENCES patients
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            baseline_session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            followup_session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        )
#                            )
#                        """)
#
#         # Таблица для исследовательских инсайтов
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS research_insights
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            insight_type
#                            VARCHAR
#                        (
#                            50
#                        ) NOT NULL,
#                            patient_group TEXT,
#                            findings TEXT NOT NULL,
#                            confidence_score FLOAT,
#                            visualization_parameters TEXT,
#                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                            )
#                        """)
#
#         # ⭐ НОВЫЕ ТАБЛИЦЫ: Метаданные тестирования
#         self.create_metadata_tables(conn)
#
#         # Индексы для производительности
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_patient ON analysis_results(patient_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_session ON analysis_results(session_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_method ON analysis_results(analysis_method)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_longitudinal_patient ON longitudinal_analysis(patient_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON research_insights(insight_type)")
#
#         # Новые индексы для метаданных
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_test_type ON test_metadata(test_type)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_stimulus ON test_metadata(stimulus_number)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_params_name ON testing_system_parameters(parameter_name)")
#
#         # Заполняем таблицы метаданных начальными данными
#         self.populate_metadata_tables(conn)
#
#         conn.commit()
#         conn.close()
#         logger.info("✅ Расширенная схема БД v2 создана (включая метаданные)")
#
#     def run_migration(self):
#         """Запуск полной миграции на схему v2"""
#         logger.info("🔄 Запуск миграции базы данных v2...")
#
#         if not os.path.exists(self.db_path):
#             logger.error("❌ База данных не найдена")
#             return False
#
#         try:
#             # Проверяем текущую версию
#             current_version = self.check_schema_version()
#             logger.info(f"🔍 Текущая версия схемы: {current_version}")
#
#             if current_version == "v2_metadata":
#                 logger.info("✅ База данных уже использует схему v2 с метаданными")
#                 return True
#
#             # Создаем резервную копию
#             logger.info("🔄 Создание резервной копии...")
#             backup_path = self.backup_database()
#
#             # Создаем новую схему
#             self.create_advanced_schema()
#
#             # Проверяем результат
#             new_version = self.check_schema_version()
#             if new_version == "v2_metadata":
#                 logger.info("🎉 Миграция на схему v2 с метаданными завершена успешно")
#                 return True
#             else:
#                 logger.error("❌ Миграция завершилась, но схема не обновлена")
#                 return False
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка миграции: {e}")
#             return False
#
#
# # Функция для удобного импорта
# def run_database_migration_v2(db_path="neuro_data.db"):
#     """Запуск миграции v2 (удобная функция для импорта)"""
#     migrator = DatabaseMigrationV2(db_path)
#     return migrator.run_migration()
#
#
# def check_database_schema_version(db_path="neuro_data.db"):
#     """Проверка версии схемы (удобная функция для импорта)"""
#     migrator = DatabaseMigrationV2(db_path)
#     return migrator.check_schema_version()
#
#
# def backup_database(db_path="neuro_data.db"):
#     """Создание резервной копии (удобная функция для импорта)"""
#     migrator = DatabaseMigrationV2(db_path)
#     return migrator.backup_database()
#
#
# def update_test_metadata(db_path="neuro_data.db"):
#     """Обновить метаданные тестирования в базе данных"""
#     migrator = DatabaseMigrationV2(db_path)
#     try:
#         conn = sqlite3.connect(db_path)
#         migrator.create_metadata_tables(conn)
#         migrator.populate_metadata_tables(conn)
#         conn.close()
#         logger.info("✅ Метаданные тестирования обновлены")
#         return True
#     except Exception as e:
#         logger.error(f"❌ Ошибка обновления метаданных: {e}")
#         return False
#
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     migrator = DatabaseMigrationV2()
#     success = migrator.run_migration()
#     sys.exit(0 if success else 1)


# # utils/database_migration_v2.py
# import sqlite3
# import os
# import logging
# from datetime import datetime
# import shutil
#
# logger = logging.getLogger(__name__)
#
#
# class DatabaseMigrationV2:
#     def __init__(self, db_path="neuro_data.db"):
#         self.db_path = db_path
#
#     def backup_database(self):
#         """Создание резервной копии базы данных"""
#         try:
#             if os.path.exists(self.db_path):
#                 backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#                 shutil.copy2(self.db_path, backup_path)
#                 logger.info(f"✅ Резервная копия создана: {backup_path}")
#                 return backup_path
#             return None
#         except Exception as e:
#             logger.error(f"❌ Ошибка создания резервной копии: {e}")
#             return None
#
#     def check_schema_version(self):
#         """Проверка версии схемы базы данных"""
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#
#             # Проверяем существование таблицы analysis_results (новая схема v2)
#             cursor.execute("""
#                            SELECT name
#                            FROM sqlite_master
#                            WHERE type = 'table'
#                              AND name = 'analysis_results'
#                            """)
#             has_v2_schema = cursor.fetchone() is not None
#
#             # Проверяем существование старой схемы (v1)
#             cursor.execute("""
#                            SELECT name
#                            FROM sqlite_master
#                            WHERE type = 'table'
#                              AND name = 'users'
#                            """)
#             has_v1_schema = cursor.fetchone() is not None
#
#             conn.close()
#
#             if has_v2_schema:
#                 return "v2"
#             elif has_v1_schema:
#                 return "v1"
#             else:
#                 return "none"
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка проверки схемы БД: {e}")
#             return "error"
#
#     def create_advanced_schema(self):
#         """Создание расширенной схемы v2"""
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#
#         # Таблица для основных результатов анализа
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS analysis_results
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            patient_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            analysis_method
#                            VARCHAR
#                        (
#                            50
#                        ) NOT NULL,
#
#                            -- Базовые показатели по позициям
#                            left_v1 FLOAT, left_delta_v4 FLOAT, left_delta_v5_mt FLOAT,
#                            center_v1 FLOAT, center_delta_v4 FLOAT, center_delta_v5_mt FLOAT,
#                            right_v1 FLOAT, right_delta_v4 FLOAT, right_delta_v5_mt FLOAT,
#
#                            -- Агрегированные показатели
#                            overall_v1 FLOAT, overall_delta_v4 FLOAT, overall_delta_v5_mt FLOAT,
#
#                            -- Метрики качества данных
#                            data_quality_score FLOAT,
#                            sample_sizes TEXT,
#
#                            -- Метadata
#                            analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            FOREIGN KEY
#                        (
#                            patient_id
#                        ) REFERENCES patients
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        )
#                            )
#                        """)
#
#         # Таблица для анализа динамики
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS longitudinal_analysis
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            patient_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            baseline_session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            followup_session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            time_interval_days
#                            INTEGER,
#
#                            -- Изменения по позициям
#                            delta_left_v1
#                            FLOAT,
#                            delta_left_delta_v4
#                            FLOAT,
#                            delta_left_delta_v5_mt
#                            FLOAT,
#                            delta_center_v1
#                            FLOAT,
#                            delta_center_delta_v4
#                            FLOAT,
#                            delta_center_delta_v5_mt
#                            FLOAT,
#                            delta_right_v1
#                            FLOAT,
#                            delta_right_delta_v4
#                            FLOAT,
#                            delta_right_delta_v5_mt
#                            FLOAT,
#
#                            -- Статистическая значимость
#                            statistical_significance
#                            TEXT,
#                            clinical_significance
#                            BOOLEAN,
#                            significance_notes
#                            TEXT,
#
#                            created_at
#                            TIMESTAMP
#                            DEFAULT
#                            CURRENT_TIMESTAMP,
#
#                            FOREIGN
#                            KEY
#                        (
#                            patient_id
#                        ) REFERENCES patients
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            baseline_session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            followup_session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        )
#                            )
#                        """)
#
#         # Таблица для исследовательских инсайтов
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS research_insights
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            insight_type
#                            VARCHAR
#                        (
#                            50
#                        ) NOT NULL,
#                            patient_group TEXT,
#                            findings TEXT NOT NULL,
#                            confidence_score FLOAT,
#                            visualization_parameters TEXT,
#                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                            )
#                        """)
#
#         # Индексы для производительности
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_patient ON analysis_results(patient_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_session ON analysis_results(session_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_method ON analysis_results(analysis_method)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_longitudinal_patient ON longitudinal_analysis(patient_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON research_insights(insight_type)")
#
#         conn.commit()
#         conn.close()
#         logger.info("✅ Расширенная схема БД v2 создана")
#
#     def run_migration(self):
#         """Запуск полной миграции на схему v2"""
#         logger.info("🔄 Запуск миграции базы данных v2...")
#
#         if not os.path.exists(self.db_path):
#             logger.error("❌ База данных не найдена")
#             return False
#
#         try:
#             # Проверяем текущую версию
#             current_version = self.check_schema_version()
#             logger.info(f"🔍 Текущая версия схемы: {current_version}")
#
#             if current_version == "v2":
#                 logger.info("✅ База данных уже использует схему v2")
#                 return True
#
#             # Создаем резервную копию
#             logger.info("🔄 Создание резервной копии...")
#             backup_path = self.backup_database()
#
#             # Создаем новую схему
#             self.create_advanced_schema()
#
#             # Проверяем результат
#             new_version = self.check_schema_version()
#             if new_version == "v2":
#                 logger.info("🎉 Миграция на схему v2 завершена успешно")
#                 return True
#             else:
#                 logger.error("❌ Миграция завершилась, но схема не обновлена")
#                 return False
#
#         except Exception as e:
#             logger.error(f"❌ Ошибка миграции: {e}")
#             return False
#
#
# # Функция для удобного импорта
# def run_database_migration_v2(db_path="neuro_data.db"):
#     """Запуск миграции v2 (удобная функция для импорта)"""
#     migrator = DatabaseMigrationV2(db_path)
#     return migrator.run_migration()
#
#
# def check_database_schema_version(db_path="neuro_data.db"):
#     """Проверка версии схемы (удобная функция для импорта)"""
#     migrator = DatabaseMigrationV2(db_path)
#     return migrator.check_schema_version()
#
#
# def backup_database(db_path="neuro_data.db"):
#     """Создание резервной копии (удобная функция для импорта)"""
#     migrator = DatabaseMigrationV2(db_path)
#     return migrator.backup_database()
#
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     migrator = DatabaseMigrationV2()
#     success = migrator.run_migration()
#     sys.exit(0 if success else 1)
#

# """
# Миграция базы данных для расширенной схемы хранения результатов анализа
# """
# import sqlite3
# import os
# from datetime import datetime
#
#
# class DatabaseMigrationV2:
#     def __init__(self, db_path="neuro_data.db"):
#         self.db_path = db_path
#
#     def create_advanced_schema(self):
#         """Создание расширенной схемы для хранения результатов анализа"""
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#
#         # Таблица для основных результатов анализа
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS analysis_results
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            patient_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            analysis_method
#                            VARCHAR
#                        (
#                            50
#                        ) NOT NULL,
#
#                            -- Базовые показатели по позициям
#                            left_v1 FLOAT,
#                            left_delta_v4 FLOAT,
#                            left_delta_v5_mt FLOAT,
#                            center_v1 FLOAT,
#                            center_delta_v4 FLOAT,
#                            center_delta_v5_mt FLOAT,
#                            right_v1 FLOAT,
#                            right_delta_v4 FLOAT,
#                            right_delta_v5_mt FLOAT,
#
#                            -- Агрегированные показатели
#                            overall_v1 FLOAT,
#                            overall_delta_v4 FLOAT,
#                            overall_delta_v5_mt FLOAT,
#
#                            -- Метрики качества данных
#                            data_quality_score FLOAT,
#                            sample_sizes TEXT, -- JSON: {'left': 12, 'center': 12, 'right': 12}
#
#                        -- Метadata
#                            analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            FOREIGN KEY
#                        (
#                            patient_id
#                        ) REFERENCES patients
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        )
#                            )
#                        """)
#
#         # Таблица для анализа динамики
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS longitudinal_analysis
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            patient_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            baseline_session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            followup_session_id
#                            INTEGER
#                            NOT
#                            NULL,
#                            time_interval_days
#                            INTEGER,
#
#                            -- Изменения по позициям
#                            delta_left_v1
#                            FLOAT,
#                            delta_left_delta_v4
#                            FLOAT,
#                            delta_left_delta_v5_mt
#                            FLOAT,
#                            delta_center_v1
#                            FLOAT,
#                            delta_center_delta_v4
#                            FLOAT,
#                            delta_center_delta_v5_mt
#                            FLOAT,
#                            delta_right_v1
#                            FLOAT,
#                            delta_right_delta_v4
#                            FLOAT,
#                            delta_right_delta_v5_mt
#                            FLOAT,
#
#                            -- Статистическая значимость
#                            statistical_significance
#                            TEXT, -- JSON
#                            clinical_significance
#                            BOOLEAN,
#                            significance_notes
#                            TEXT,
#
#                            created_at
#                            TIMESTAMP
#                            DEFAULT
#                            CURRENT_TIMESTAMP,
#
#                            FOREIGN
#                            KEY
#                        (
#                            patient_id
#                        ) REFERENCES patients
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            baseline_session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        ),
#                            FOREIGN KEY
#                        (
#                            followup_session_id
#                        ) REFERENCES testing_sessions
#                        (
#                            id
#                        )
#                            )
#                        """)
#
#         # Таблица для исследовательских инсайтов
#         cursor.execute("""
#                        CREATE TABLE IF NOT EXISTS research_insights
#                        (
#                            id
#                            INTEGER
#                            PRIMARY
#                            KEY
#                            AUTOINCREMENT,
#                            insight_type
#                            VARCHAR
#                        (
#                            50
#                        ) NOT NULL,
#                            patient_group TEXT, -- JSON фильтры
#                            findings TEXT NOT NULL, -- JSON с результатами
#                            confidence_score FLOAT,
#                            visualization_parameters TEXT, -- JSON
#                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                            )
#                        """)
#
#         # Индексы для производительности
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_patient ON analysis_results(patient_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_session ON analysis_results(session_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_method ON analysis_results(analysis_method)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_longitudinal_patient ON longitudinal_analysis(patient_id)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON research_insights(insight_type)")
#
#         conn.commit()
#         conn.close()
#         print("✅ Расширенная схема БД создана успешно")
#
#     def migrate_existing_data(self):
#         """Миграция существующих данных в новую схему (если нужно)"""
#         # Здесь можно добавить логику миграции существующих анализов
#         pass
#
#     def run_migration(self):
#         """Запуск полной миграции"""
#         print("🔄 Запуск миграции базы данных v2...")
#
#         if not os.path.exists(self.db_path):
#             print("❌ База данных не найдена")
#             return False
#
#         try:
#             self.create_advanced_schema()
#             self.migrate_existing_data()
#             print("✅ Миграция завершена успешно")
#             return True
#         except Exception as e:
#             print(f"❌ Ошибка миграции: {e}")
#             return False
#
#
# # Для запуска из командной строки
# if __name__ == "__main__":
#     migrator = DatabaseMigrationV2()
#     # migrator.run_migration()