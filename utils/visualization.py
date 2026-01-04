# utils/visualization.py
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional
import pandas as pd


class DataVisualizer:
    """Класс для визуализации данных"""

    @staticmethod
    def setup_plot_style():
        """Настройка стиля графиков"""
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    @staticmethod
    def create_age_distribution_plot(ages: List[int], save_path: Optional[str] = None):
        """Создание графика распределения возрастов"""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(ages, bins=20, alpha=0.7, edgecolor='black')
        ax.set_xlabel('Возраст')
        ax.set_ylabel('Количество')
        ax.set_title('Распределение возрастов пациентов')
        ax.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig