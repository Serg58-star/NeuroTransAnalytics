class ValidationFramework:
    """Оценивает надежность методов и генерирует рекомендации"""

    def generate_test_design_recommendations(self, comparison_results):
        """Генерирует рекомендации по дизайну будущих тестов"""
        recommendations = []

        # Анализ надежности методов для n=4
        n4_reliability = self.assess_n4_methods_reliability(comparison_results)

        if n4_reliability['overall_score'] < 0.7:
            recommendations.append({
                'type': 'test_design_change',
                'current': '4 попытки на цвет/позицию',
                'recommended': '6+ попыток на цвет/позицию',
                'rationale': f"Низкая надежность методов для n=4: {n4_reliability['overall_score']:.2f}",
                'impact_assessment': {
                    'test_duration_increase': '33% (36→48 попыток)',
                    'fatigue_risk': 'умеренное увеличение',
                    'data_reliability_gain': 'значительное улучшение'
                }
            })

        return recommendations

    def assess_n4_methods_reliability(self, results):
        """Оценивает надежность методов для n=4"""
        metrics = []
        for method_name, method_results in results.items():
            if 'n4' in method_name:
                metrics.append({
                    'method': method_name,
                    'consistency': self.calculate_method_consistency(method_results),
                    'sensitivity': self.estimate_sensitivity(method_results),
                    'stability': self.assess_stability(method_results)
                })

        return self.aggregate_reliability_metrics(metrics)