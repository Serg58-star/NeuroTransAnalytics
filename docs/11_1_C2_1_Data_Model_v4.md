# C2.1 — Логическая модель данных (Data Model v4)

## 1. Назначение документа

Документ описывает **логическую модель данных версии v4** проекта *NeuroTransAnalytics*.

Цель модели — формально определить сущности, их атрибуты и связи таким образом, чтобы:

* все сценарии анализа уровней **A0–B3** были воспроизводимы;
* все методические требования уровня **C1** были реализуемы без потерь;
* данные могли расширяться без изменения уже сохранённой структуры.

Документ **не описывает физическую реализацию** (форматы, СУБД) — это предмет C2.2.

---

## 2. Общие принципы логической модели

### 2.1. Принцип событийной первичности

Базовой единицей данных является **событие**, а не агрегат.

* каждое предъявление стимула — отдельное событие;
* каждая реакция — отдельное событие;
* агрегаты всегда вычисляются поверх событий.

---

### 2.2. Принцип раздельности дизайна и реакции

В модели:

* параметры **дизайна теста** хранятся отдельно;
* параметры **реакции** хранятся отдельно;
* любые связи между ними реализуются через идентификаторы событий.

---

### 2.3. Принцип версионности

Каждая логика расчёта и сценарий анализа имеют явную версию.

---

## 3. Основные сущности и их атрибуты

### 3.1. Subject

**Назначение:** анонимизированное описание испытуемого.

Атрибуты:

* subject_id (PK)
* sex
* age
* age_group (опционально)

---

### 3.2. TestSession

**Назначение:** единичный сеанс тестирования.

Атрибуты:

* session_id (PK)
* subject_id (FK)
* test_type
* phase (F1 / F2 / F3)
* session_datetime
* test_config_version

---

### 3.3. StimulusEvent

**Назначение:** единичное предъявление стимула.

Атрибуты:

* stimulus_event_id (PK)
* session_id (FK)
* stimulus_role (test / masking / intermediate)
* stimulus_color
* stimulus_location (left / center / right)
* stimulus_position_index
* psi_test
* psi_mask
* psi_transition
* background_id
* masking_pattern_id

---

### 3.4. ResponseEvent

**Назначение:** реакция на конкретный тестовый стимул.

Атрибуты:

* response_event_id (PK)
* stimulus_event_id (FK)
* rt
* validity_flag
* error_type

---

## 4. Производные сущности

### 4.1. ComponentTiming

**Назначение:** хранение компонентных временных показателей.

Атрибуты:

* component_timing_id (PK)
* stimulus_event_id (FK)
* delta_v1
* delta_v4
* delta_v5_mt
* computation_version
* filtering_params

---

### 4.2. AggregateMetrics

**Назначение:** агрегированные показатели.

Атрибуты:

* aggregate_id (PK)
* session_id (FK)
* aggregation_scope
* metric_name
* metric_value
* computation_version

---

## 5. Сущности дизайна теста

### 5.1. TestConfig

**Назначение:** описание конфигурации теста.

Атрибуты:

* test_config_id (PK)
* test_type
* color_set
* spatial_scheme
* psi_scheme
* masking_scheme
* background_scheme

---

### 5.2. BackgroundConfig

**Назначение:** параметры фона.

Атрибуты:

* background_id (PK)
* background_color
* background_dynamic_type
* background_contrast
* background_phase

---

### 5.3. MaskingPattern

**Назначение:** описание маскирующей последовательности.

Атрибуты:

* masking_pattern_id (PK)
* pattern_type
* pattern_description

---

## 6. Сценарный слой

### 6.1. ScenarioDefinition

Атрибуты:

* scenario_id (PK)
* scenario_code (A0.1, B1, C1.3, etc.)
* scenario_version
* scenario_description

---

### 6.2. ScenarioResult

Атрибуты:

* scenario_result_id (PK)
* scenario_id (FK)
* target_entity
* result_reference
* computation_version

---

## 7. Связи между сущностями (высокоуровнево)

* Subject 1—N TestSession
* TestSession 1—N StimulusEvent
* StimulusEvent 1—0..1 ResponseEvent
* StimulusEvent 1—0..1 ComponentTiming
* TestSession 1—N AggregateMetrics

---

## 8. Поддержка расширяемости

Модель допускает:

* добавление новых компонент времени;
* добавление новых типов стимулов;
* расширение параметров фона;
* добавление новых сценариев без изменения существующих таблиц.

---

## 9. Итоговая роль модели

Логическая модель v4 обеспечивает:

* полную трассируемость от стимула до сценарного вывода;
* методологическую чистоту (дизайн ≠ реакция);
* основу для физической реализации хранения (C2.2).
