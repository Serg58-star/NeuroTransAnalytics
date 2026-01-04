# Рабочий, а не исследовательский анализатор
class TraditionalNeuroAnalyzer(BaseNeuroAnalyzer):
    def analyze_patient_session(self, session_data):
        """Анализ одной сессии тестирования пациента"""
        # Реальная логика расчета V1, ΔV4, ΔV5/MT
        results = {}

        # Для каждого поля зрения
        for position in ['left', 'center', 'right']:
            v1 = self.analyze_simple_test(session_data, position)
            color = self.analyze_color_test(session_data, position)
            shift = self.analyze_shift_test(session_data, position)

            results[position] = {
                'v1_median': v1['median'],
                'delta_v4': color['median'] - v1['median'],
                'delta_v5_mt': shift['median'] - v1['median']
            }

        return results