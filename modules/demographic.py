# modules/demographic.py
import pandas as pd
from typing import Dict, Any
from datetime import datetime


class DemographicAnalyzer:
    """Анализатор демографических данных"""

    def __init__(self, users_data: pd.DataFrame):
        self.users_data = users_data

    def analyze(self) -> Dict[str, Any]:
        """Проведение демографического анализа"""
        analysis = {
            'basic_statistics': self._calculate_basic_stats(),
            'age_distribution': self._calculate_age_distribution(),
            'gender_distribution': self._calculate_gender_distribution(),
            'registration_trends': self._analyze_registration_trends()
        }

        return analysis

    def _calculate_basic_stats(self) -> Dict[str, Any]:
        """Расчет базовой статистики"""
        current_year = datetime.now().year
        ages = current_year - self.users_data['YBorn'].dt.year

        return {
            'total_patients': len(self.users_data),
            'mean_age': float(ages.mean()),
            'age_std': float(ages.std()),
            'min_age': int(ages.min()),
            'max_age': int(ages.max()),
            'active_patients': int(self.users_data['Active'].sum()) if 'Active' in self.users_data.columns else 0
        }

    def _calculate_age_distribution(self) -> Dict[str, int]:
        """Распределение по возрастным группам"""
        current_year = datetime.now().year
        ages = current_year - self.users_data['YBorn'].dt.year

        bins = [0, 18, 30, 45, 60, 100]
        labels = ['<18', '18-30', '30-45', '45-60', '60+']

        age_groups = pd.cut(ages, bins=bins, labels=labels)
        return age_groups.value_counts().to_dict()

    def _calculate_gender_distribution(self) -> Dict[str, int]:
        """Распределение по полу"""
        if 'Gender' not in self.users_data.columns:
            return {}

        gender_counts = self.users_data['Gender'].value_counts()
        return {
            'male': int(gender_counts.get(1, 0)),
            'female': int(gender_counts.get(0, 0))
        }

    def _analyze_registration_trends(self) -> Dict[str, Any]:
        """Анализ трендов регистрации"""
        if 'RegDate' not in self.users_data.columns:
            return {}

        reg_dates = self.users_data['RegDate']
        return {
            'first_registration': reg_dates.min().strftime('%Y-%m-%d'),
            'last_registration': reg_dates.max().strftime('%Y-%m-%d'),
            'registration_by_year': reg_dates.dt.year.value_counts().to_dict()
        }


