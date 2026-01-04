# statistics/small_sample_methods.py
class SmallSampleMethods:
    @staticmethod
    def assess_sample_adequacy(data):
        """Оценка адекватности размера выборки"""
        n = len(data)
        if n >= 8:
            return "достаточно"
        elif n >= 6:
            return "ограниченно"
        elif n >= 4:
            return "минимально"  # НОВЫЙ УРОВЕНЬ
        else:
            return "недостаточно"

    @staticmethod
    def analyze_very_small_sample(data, min_n=4):
        """Специальные методы для очень малых выборок (n=4)"""
        n = len(data)
        if n < min_n:
            return None

        # Для n=4 используем особые подходы:
        results = {
            'median': np.median(data),
            'range': np.ptp(data),  # Размах вместо стандартного отклонения
            'midrange': (np.min(data) + np.max(data)) / 2,
            'sample_size': n,
            'reliability': 'low' if n == 4 else 'medium'
        }

        # Дополнительные метрики для n=4
        if n == 4:
            results['data_quality_indicators'] = {
                'has_outliers': SmallSampleMethods.detect_outliers_small_n(data),
                'variability_ratio': np.ptp(data) / np.median(data) if np.median(data) != 0 else float('inf')
            }

        return results