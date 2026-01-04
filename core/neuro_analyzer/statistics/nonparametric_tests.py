from scipy.stats import wilcoxon, mannwhitneyu


class NonparametricTests:
    """Непараметрические статистические тесты"""

    @staticmethod
    def wilcoxon_signed_rank(x, y):
        """Тест Вилкоксона для парных выборок"""
        statistic, p_value = wilcoxon(x, y)
        return {'statistic': statistic, 'p_value': p_value}

    @staticmethod
    def permutation_test(x, y, n_permutations=1000):
        """Перестановочный тест для малых выборок"""
        # Реализация перестановочного теста
        pass