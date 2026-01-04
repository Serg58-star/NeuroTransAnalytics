class MethodComparisonEngine:
    """Сравнивает различные методы анализа на одних и тех же данных"""

    def compare_analysis_methods(self, data, methods_dict):
        """Сравнивает несколько методов анализа"""
        results = {}

        for method_name, method_func in methods_dict.items():
            try:
                results[method_name] = {
                    'results': method_func(data),
                    'metadata': self.assess_method_characteristics(method_func, data),
                    'reliability_indicators': self.calculate_reliability_metrics(method_func, data)
                }
            except Exception as e:
                results[method_name] = {'error': str(e)}

        return self.rank_methods(results)

    def assess_method_characteristics(self, method, data):
        """Оценивает характеристики метода"""
        return {
            'min_sample_size': getattr(method, 'min_sample_size', 'unknown'),
            'assumptions': getattr(method, 'assumptions', []),
            'sensitivity_to_outliers': self.estimate_outlier_sensitivity(method, data),
            'computational_complexity': 'low'  # placeholder
        }