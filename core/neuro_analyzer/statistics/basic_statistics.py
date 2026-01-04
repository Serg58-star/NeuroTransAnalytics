import numpy as np
from scipy import stats


class BasicStatistics:
    """Базовые статистические функции"""

    @staticmethod
    def median(data):
        return float(np.median(data))

    @staticmethod
    def percentile(data, p):
        return float(np.percentile(data, p))

    @staticmethod
    def interquartile_range(data):
        q75, q25 = np.percentile(data, [75, 25])
        return q75 - q25