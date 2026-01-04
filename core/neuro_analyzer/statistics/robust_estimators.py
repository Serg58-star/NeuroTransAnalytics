class RobustEstimators:
    """Робастные статистические оценки"""

    @staticmethod
    def median_absolute_deviation(data):
        """Median Absolute Deviation"""
        median = np.median(data)
        deviations = np.abs(data - median)
        return np.median(deviations) * 1.4826

    @staticmethod
    def trimmed_mean(data, proportion=0.1):
        """Усеченное среднее"""
        # Реализация усеченного среднего
        pass