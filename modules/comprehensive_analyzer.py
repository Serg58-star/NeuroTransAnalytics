# modules/comprehensive_analyzer.py
from typing import Dict, Any
import pandas as pd
from modules.demographic import DemographicAnalyzer
from modules.test_analyzer import TestAnalyzer


class ComprehensiveAnalyzer:
    """Комплексный анализатор данных"""

    def __init__(self, users_data: pd.DataFrame, boxbase_data: pd.DataFrame):
        self.users_data = users_data
        self.boxbase_data = boxbase_data
        self.demographic_analyzer = DemographicAnalyzer(users_data)
        self.test_analyzer = TestAnalyzer(boxbase_data)

    def analyze_all(self) -> Dict[str, Any]:
        """Проведение комплексного анализа"""
        return {
            'demographic': self.demographic_analyzer.analyze(),
            'simple_test': self.test_analyzer.analyze_simple_test(),
            'color_red_test': self.test_analyzer.analyze_color_red_test(),
            'shift_test': self.test_analyzer.analyze_shift_test(),
            'cross_analysis': self._cross_analysis()
        }

    def _cross_analysis(self) -> Dict[str, Any]:
        """Кросс-анализ демографических и тестовых данных"""
        # Объединение данных для анализа связей
        merged_data = pd.merge(
            self.boxbase_data,
            self.users_data,
            left_on='REG_ID',
            right_on='ID',
            how='inner'
        )

        analysis = {
            'age_vs_reaction_time': self._analyze_age_vs_reaction_time(merged_data),
            'gender_vs_reaction_time': self._analyze_gender_vs_reaction_time(merged_data)
        }

        return analysis

    def _analyze_age_vs_reaction_time(self, merged_data: pd.DataFrame) -> Dict[str, Any]:
        """Анализ связи возраста и времени реакции"""
        current_year = pd.Timestamp.now().year
        merged_data['Age'] = current_year - merged_data['YBorn'].dt.year

        # Расчет среднего времени реакции по тестам
        test_columns = [f'Tst{i}_{j}' for i in range(1, 4) for j in range(1, 37)]
        merged_data['MeanReactionTime'] = merged_data[test_columns].mean(axis=1)

        # Корреляция возраста и времени реакции
        correlation = merged_data['Age'].corr(merged_data['MeanReactionTime'])

        return {
            'correlation': float(correlation) if not pd.isna(correlation) else 0.0,
            'age_groups_reaction_time': self._calculate_age_group_reaction_times(merged_data)
        }

    def _analyze_gender_vs_reaction_time(self, merged_data: pd.DataFrame) -> Dict[str, Any]:
        """Анализ связи пола и времени реакции"""
        if 'Gender' not in merged_data.columns:
            return {}

        test_columns = [f'Tst{i}_{j}' for i in range(1, 4) for j in range(1, 37)]
        merged_data['MeanReactionTime'] = merged_data[test_columns].mean(axis=1)

        gender_stats = merged_data.groupby('Gender')['MeanReactionTime'].agg(['mean', 'std', 'count']).to_dict()

        return {
            'male_mean_reaction': gender_stats['mean'].get(1, 0),
            'female_mean_reaction': gender_stats['mean'].get(0, 0),
            'male_std': gender_stats['std'].get(1, 0),
            'female_std': gender_stats['std'].get(0, 0)
        }

    def _calculate_age_group_reaction_times(self, merged_data: pd.DataFrame) -> Dict[str, float]:
        """Расчет времени реакции по возрастным группам"""
        bins = [0, 18, 30, 45, 60, 100]
        labels = ['<18', '18-30', '30-45', '45-60', '60+']

        merged_data['AgeGroup'] = pd.cut(merged_data['Age'], bins=bins, labels=labels)
        age_group_stats = merged_data.groupby('AgeGroup')['MeanReactionTime'].mean()

        return age_group_stats.to_dict()