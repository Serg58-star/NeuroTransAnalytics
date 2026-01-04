# core/neuro_analyzer.py
import json
import sqlite3
import numpy as np
from datetime import datetime  # ДОБАВЛЯЕМ ИМПОРТ
from typing import Dict, Any


class NeurotransmitterAnalyzer:
    def __init__(self, db_path='neuro_data.db'):
        self.db_path = db_path

    def calculate_all_metrics(self):
        """Расчет всех метрик для немаркированных тестов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Находим тесты без расчетов
                cursor = conn.execute(
                    "SELECT id, test_type, raw_aggregates FROM visual_tests WHERE calculated_metrics IS NULL"
                )

                processed_count = 0
                for test_id, test_type, raw_aggregates in cursor:
                    try:
                        aggregates = json.loads(raw_aggregates)
                        metrics = self._calculate_basic_metrics(aggregates, test_type)

                        # Сохраняем расчеты
                        conn.execute(
                            "UPDATE visual_tests SET calculated_metrics = ?, is_processed = TRUE, processed_at = ? WHERE id = ?",
                            (json.dumps(metrics), datetime.now().isoformat(), test_id)
                        )
                        processed_count += 1
                    except Exception as e:
                        print(f"⚠️ Ошибка расчета метрик для теста {test_id}: {e}")

                print(f"✅ Рассчитано метрик для {processed_count} тестов")

        except Exception as e:
            print(f"❌ Ошибка в calculate_all_metrics: {e}")
            import traceback
            traceback.print_exc()

    def _calculate_basic_metrics(self, aggregates: Dict, test_type: str) -> Dict[str, Any]:
        """Расчет базовых нейромедиаторных метрик"""
        try:
            result = aggregates.get('result', 0)

            metrics = {
                'v1_latency': result,
                'std_deviation': aggregates.get('std_dev', 0),
                'early_responses': aggregates.get('early_responses', 0),
                'late_responses': aggregates.get('late_responses', 0),
                'has_motor_correction': False,
                'calculation_timestamp': datetime.now().isoformat(),
                'test_type': test_type
            }

            return metrics

        except Exception as e:
            print(f"❌ Ошибка в _calculate_basic_metrics: {e}")
            return {'error': str(e), 'calculation_timestamp': datetime.now().isoformat()}

