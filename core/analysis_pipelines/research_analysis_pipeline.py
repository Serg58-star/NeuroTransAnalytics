def research_analysis_pipeline(patient_data):
    """Полный исследовательский анализ для пациента"""

    # 1. Анализ всеми методами
    all_results = {}

    for position in ['left', 'center', 'right']:
        for color in ['red', 'green', 'blue']:
            color_data = extract_color_position_data(patient_data, color, position)

            if len(color_data) == 4:
                # Сравниваем ВСЕ методы для n=4
                comparison = MethodComparisonEngine().compare_analysis_methods(
                    color_data, N4_METHODS
                )
                all_results[f"{color}_{position}"] = comparison

            elif len(color_data) >= 6:
                # Сравниваем стандартные методы
                comparison = MethodComparisonEngine().compare_analysis_methods(
                    color_data, STANDARD_METHODS
                )
                all_results[f"{color}_{position}"] = comparison

    # 2. Генерация рекомендаций
    recommendations = ValidationFramework().generate_test_design_recommendations(all_results)

    # 3. Сводный отчет
    return {
        'detailed_analyses': all_results,
        'method_reliability_assessment': assess_overall_method_reliability(all_results),
        'test_design_recommendations': recommendations,
        'research_insights': extract_research_insights(all_results)
    }