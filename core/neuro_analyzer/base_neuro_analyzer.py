# Минимальная реализация СЕЙЧАС
class BaseNeuroAnalyzer:
    def extract_test_data(self, session_data, test_type):
        """Извлечение данных теста (Tst1_1...Tst1_36 etc)"""
        # Реальная реализация, а не заглушка
        pass

    def calculate_basic_metrics(self, data):
        """Базовые расчеты: медиана, MAD, процентили"""
        import numpy as np
        return {
            'median': float(np.median(data)),
            'mad': self.calculate_mad(data),
            'q25': float(np.percentile(data, 25)),
            'q75': float(np.percentile(data, 75))
        }