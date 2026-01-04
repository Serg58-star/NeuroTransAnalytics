# utils/statistics.py
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any


class StatisticsCalculator:
    """Калькулятор статистических показателей"""

    @staticmethod
    def calculate_basic_stats(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Расчет базовой статистики для колонки"""
        if column not in df.columns:
            return {}

        data = df[column].dropna()
        if len(data) == 0:
            return {}

        return {
            'count': len(data),
            'mean': float(data.mean()),
            'std': float(data.std()),
            'min': float(data.min()),
            'max': float(data.max()),
            'median': float(data.median()),
            'q1': float(data.quantile(0.25)),
            'q3': float(data.quantile(0.75))
        }

    @staticmethod
    def calculate_correlations(df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """Расчет корреляций между колонками"""
        numeric_df = df[columns].select_dtypes(include=[np.number])
        return numeric_df.corr()