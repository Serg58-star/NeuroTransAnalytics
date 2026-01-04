# modules/test_analyzer.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from core.test_metadata import TestMetadata


class TestAnalyzer:
    """Анализатор тестовых данных"""

    def __init__(self, boxbase_data: pd.DataFrame):
        self.boxbase_data = boxbase_data
        self.metadata = TestMetadata()

    def analyze_simple_test(self) -> Dict[str, Any]:
        """Анализ простого теста"""
        test_columns = [f'Tst1_{i}' for i in range(1, 37)]
        reaction_times = self.boxbase_data[test_columns]

        analysis = {
            'basic_stats': self._calculate_basic_stats(reaction_times),
            'by_color': self._analyze_by_color('simple', reaction_times),
            'by_position': self._analyze_by_position('simple', reaction_times),
            'by_interval': self._analyze_by_interval('simple', reaction_times),
            'errors': self._analyze_errors('simple')
        }

        return analysis

    def analyze_color_red_test(self) -> Dict[str, Any]:
        """Анализ теста с красным стимулом"""
        test_columns = [f'Tst2_{i}' for i in range(1, 37)]
        reaction_times = self.boxbase_data[test_columns]

        analysis = {
            'basic_stats': self._calculate_basic_stats(reaction_times),
            'by_sequence': self._analyze_by_sequence('color_red', reaction_times),
            'errors': self._analyze_errors('color_red')
        }

        return analysis

    def analyze_shift_test(self) -> Dict[str, Any]:
        """Анализ теста со смещением"""
        test_columns = [f'Tst3_{i}' for i in range(1, 37)]
        reaction_times = self.boxbase_data[test_columns]

        analysis = {
            'basic_stats': self._calculate_basic_stats(reaction_times),
            'by_shift_type': self._analyze_by_shift_type(reaction_times),
            'errors': self._analyze_errors('shift')
        }

        return analysis

    def _calculate_basic_stats(self, reaction_times: pd.DataFrame) -> Dict[str, float]:
        """Расчет базовой статистики"""
        return {
            'mean_reaction_time': float(reaction_times.mean().mean()),
            'std_reaction_time': float(reaction_times.std().mean()),
            'min_reaction_time': float(reaction_times.min().min()),
            'max_reaction_time': float(reaction_times.max().max()),
            'median_reaction_time': float(reaction_times.median().median())
        }

    def _analyze_by_color(self, test_type: str, reaction_times: pd.DataFrame) -> Dict[str, Any]:
        """Анализ по цветам стимулов"""
        color_stats = {}

        for stimulus_id in range(1, 37):
            color = self.metadata.get_stimulus_info(test_type, stimulus_id).color
            reaction_time = reaction_times[f'Tst{self._get_test_number(test_type)}_{stimulus_id}']

            if color not in color_stats:
                color_stats[color] = []

            color_stats[color].extend(reaction_time.dropna().tolist())

        # Расчет статистики по цветам
        result = {}
        for color, times in color_stats.items():
            if times:
                result[color] = {
                    'mean': np.mean(times),
                    'std': np.std(times),
                    'count': len(times)
                }

        return result

    def _analyze_by_position(self, test_type: str, reaction_times: pd.DataFrame) -> Dict[str, Any]:
        """Анализ по позициям стимулов"""
        position_stats = {}

        for stimulus_id in range(1, 37):
            position = self.metadata.get_stimulus_info(test_type, stimulus_id).position
            reaction_time = reaction_times[f'Tst{self._get_test_number(test_type)}_{stimulus_id}']

            if position not in position_stats:
                position_stats[position] = []

            position_stats[position].extend(reaction_time.dropna().tolist())

        # Расчет статистики по позициям
        result = {}
        for position, times in position_stats.items():
            if times:
                result[position] = {
                    'mean': np.mean(times),
                    'std': np.std(times),
                    'count': len(times)
                }

        return result

    def _analyze_by_interval(self, test_type: str, reaction_times: pd.DataFrame) -> Dict[str, Any]:
        """Анализ по предстимульным интервалам"""
        interval_stats = {}

        for stimulus_id in range(1, 37):
            interval = self.metadata.get_stimulus_info(test_type, stimulus_id).pre_stimulus_interval
            reaction_time = reaction_times[f'Tst{self._get_test_number(test_type)}_{stimulus_id}']

            interval_key = f"{interval}ms"
            if interval_key not in interval_stats:
                interval_stats[interval_key] = []

            interval_stats[interval_key].extend(reaction_time.dropna().tolist())

        # Расчет статистики по интервалам
        result = {}
        for interval, times in interval_stats.items():
            if times:
                result[interval] = {
                    'mean': np.mean(times),
                    'std': np.std(times),
                    'count': len(times)
                }

        return result

    def _analyze_errors(self, test_type: str) -> Dict[str, Any]:
        """Анализ ошибок"""
        test_num = self._get_test_number(test_type)

        return {
            'premature_responses': self.boxbase_data[f'RANO_POKAZ_{test_num}'].sum(),
            'late_responses': self.boxbase_data[f'POZDNO_POKAZ_{test_num}'].sum(),
            'total_errors': self.boxbase_data[f'RANO_POKAZ_{test_num}'].sum() +
                            self.boxbase_data[f'POZDNO_POKAZ_{test_num}'].sum()
        }

    def _get_test_number(self, test_type: str) -> int:
        """Получить номер теста"""
        return {'simple': 1, 'color_red': 2, 'shift': 3}[test_type]