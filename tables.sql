raw_legacy_data|CREATE TABLE raw_legacy_data
                             (
                                 id           INTEGER PRIMARY KEY AUTOINCREMENT,
                                 source_table TEXT,
                                 original_id  INTEGER,
                                 raw_data     JSON,
                                 imported_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
sqlite_sequence|CREATE TABLE sqlite_sequence(name,seq)
patients|CREATE TABLE patients
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
testing_sessions|CREATE TABLE testing_sessions
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
visual_tests|CREATE TABLE visual_tests
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
motor_tests|CREATE TABLE motor_tests
                             (
                                 id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                                 session_id         INTEGER,
                                 test_type          TEXT,
                                 raw_data           JSON,
                                 calculated_metrics JSON,
                                 created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
test_relationships|CREATE TABLE test_relationships
                             (
                                 id                INTEGER PRIMARY KEY AUTOINCREMENT,
                                 visual_test_id    INTEGER,
                                 motor_test_id     INTEGER,
                                 relationship_type TEXT,
                                 created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
neurotransmitter_profiles|CREATE TABLE neurotransmitter_profiles
                             (
                                 id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                                 patient_id                INTEGER,
                                 session_id                INTEGER,
                                 glutamate_gaba_score      REAL,
                                 acetylcholine_score       REAL,
                                 dopamine_score            REAL,
                                 serotonin_modulation      REAL,
                                 norepinephrine_modulation REAL,
                                 profile_type              TEXT,
                                 created_at                DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
analysis_results|CREATE TABLE analysis_results
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
longitudinal_analysis|CREATE TABLE longitudinal_analysis
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
research_insights|CREATE TABLE research_insights
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
test_metadata|CREATE TABLE test_metadata
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
testing_system_parameters|CREATE TABLE testing_system_parameters
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
users|CREATE TABLE "users" (
"ID" INTEGER,
  "FName" TEXT,
  "SName" TEXT,
  "LName" TEXT,
  "YBorn" TIMESTAMP,
  "RegDate" TIMESTAMP,
  "Active" INTEGER,
  "Gender" INTEGER
)
boxbase|CREATE TABLE "boxbase" (
"cnt" INTEGER,
  "CurrentDate" TIMESTAMP,
  "CurrentTime" TEXT,
  "REG_ID" INTEGER,
  "AD1" INTEGER,
  "AD2" INTEGER,
  "VidSost" INTEGER,
  "VidSost_txt" INTEGER,
  "Tst1_1" INTEGER,
  "Tst1_2" INTEGER,
  "Tst1_3" INTEGER,
  "Tst1_4" INTEGER,
  "Tst1_5" INTEGER,
  "Tst1_6" INTEGER,
  "Tst1_7" INTEGER,
  "Tst1_8" INTEGER,
  "Tst1_9" INTEGER,
  "Tst1_10" INTEGER,
  "Tst1_11" INTEGER,
  "Tst1_12" INTEGER,
  "Tst1_13" INTEGER,
  "Tst1_14" INTEGER,
  "Tst1_15" INTEGER,
  "Tst1_16" INTEGER,
  "Tst1_17" INTEGER,
  "Tst1_18" INTEGER,
  "Tst1_19" INTEGER,
  "Tst1_20" INTEGER,
  "Tst1_21" INTEGER,
  "Tst1_22" INTEGER,
  "Tst1_23" INTEGER,
  "Tst1_24" INTEGER,
  "Tst1_25" INTEGER,
  "Tst1_26" INTEGER,
  "Tst1_27" INTEGER,
  "Tst1_28" INTEGER,
  "Tst1_29" INTEGER,
  "Tst1_30" INTEGER,
  "Tst1_31" INTEGER,
  "Tst1_32" INTEGER,
  "Tst1_33" INTEGER,
  "Tst1_34" INTEGER,
  "Tst1_35" INTEGER,
  "Tst1_36" INTEGER,
  "RANO_POKAZ_1" INTEGER,
  "POZDNO_POKAZ_1" INTEGER,
  "result_1" INTEGER,
  "SrKvadrOtkl_1" INTEGER,
  "Tst2_1" INTEGER,
  "Tst2_2" INTEGER,
  "Tst2_3" INTEGER,
  "Tst2_4" INTEGER,
  "Tst2_5" INTEGER,
  "Tst2_6" INTEGER,
  "Tst2_7" INTEGER,
  "Tst2_8" INTEGER,
  "Tst2_9" INTEGER,
  "Tst2_10" INTEGER,
  "Tst2_11" INTEGER,
  "Tst2_12" INTEGER,
  "Tst2_13" INTEGER,
  "Tst2_14" INTEGER,
  "Tst2_15" INTEGER,
  "Tst2_16" INTEGER,
  "Tst2_17" INTEGER,
  "Tst2_18" INTEGER,
  "Tst2_19" INTEGER,
  "Tst2_20" INTEGER,
  "Tst2_21" INTEGER,
  "Tst2_22" INTEGER,
  "Tst2_23" INTEGER,
  "Tst2_24" INTEGER,
  "Tst2_25" INTEGER,
  "Tst2_26" INTEGER,
  "Tst2_27" INTEGER,
  "Tst2_28" INTEGER,
  "Tst2_29" INTEGER,
  "Tst2_30" INTEGER,
  "Tst2_31" INTEGER,
  "Tst2_32" INTEGER,
  "Tst2_33" INTEGER,
  "Tst2_34" INTEGER,
  "Tst2_35" INTEGER,
  "Tst2_36" INTEGER,
  "RANO_POKAZ_2" INTEGER,
  "POZDNO_POKAZ_2" INTEGER,
  "result_2" INTEGER,
  "SrKvadrOtkl_2" INTEGER,
  "ID" INTEGER,
  "Tst3_1" INTEGER,
  "Tst3_2" INTEGER,
  "Tst3_3" INTEGER,
  "Tst3_4" INTEGER,
  "Tst3_5" INTEGER,
  "Tst3_6" INTEGER,
  "Tst3_7" INTEGER,
  "Tst3_8" INTEGER,
  "Tst3_9" INTEGER,
  "Tst3_10" INTEGER,
  "Tst3_11" INTEGER,
  "Tst3_12" INTEGER,
  "Tst3_13" INTEGER,
  "Tst3_14" INTEGER,
  "Tst3_15" INTEGER,
  "Tst3_16" INTEGER,
  "Tst3_17" INTEGER,
  "Tst3_18" INTEGER,
  "Tst3_19" INTEGER,
  "Tst3_20" INTEGER,
  "Tst3_21" INTEGER,
  "Tst3_22" INTEGER,
  "Tst3_23" INTEGER,
  "Tst3_24" INTEGER,
  "Tst3_25" INTEGER,
  "Tst3_26" INTEGER,
  "Tst3_27" INTEGER,
  "Tst3_28" INTEGER,
  "Tst3_29" INTEGER,
  "Tst3_30" INTEGER,
  "Tst3_31" INTEGER,
  "Tst3_32" INTEGER,
  "Tst3_33" INTEGER,
  "Tst3_34" INTEGER,
  "Tst3_35" INTEGER,
  "Tst3_36" INTEGER,
  "RANO_POKAZ_3" INTEGER,
  "POZDNO_POKAZ_3" INTEGER,
  "result_3" INTEGER,
  "SrKvadrOtkl_3" INTEGER,
  "Active" INTEGER
)
