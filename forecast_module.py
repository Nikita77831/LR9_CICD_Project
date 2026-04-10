"""Модуль прогнозирования временных рядов."""
import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd

class ForecastMethod(Enum):
    """Методы прогнозирования."""
    SIMPLE_AVERAGE = "simple_average"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"

@dataclass
class ForecastResult:
    """Результат прогнозирования."""
    method: ForecastMethod
    forecast_values: List[float]
    confidence_lower: List[float]
    confidence_upper: List[float]
    mape: Optional[float] = None
    rmse: Optional[float] = None

class TimeSeriesForecaster:
    """Класс для прогнозирования временных рядов."""
    def __init__(self, data: List[float],
                 timestamps: Optional[List[str]] = None,
                 data_source: Optional[str] = None):
        self.data = np.array(data, dtype=float)
        self.timestamps = timestamps or [f"t{i}" for i in range(len(data))]
        self.data_source = data_source
        if len(self.data) < 3:
            raise ValueError("Для прогнозирования нужно минимум 3 точки")

    @classmethod
    def from_csv(cls, filepath: str) -> 'TimeSeriesForecaster':
        """Загрузка данных из CSV."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} not found")
        df = pd.read_csv(filepath)
        if 'value' not in df.columns:
            raise ValueError("CSV must contain 'value' column")
        data = df['value'].tolist()
        return cls(data, data_source=filepath)

    def simple_average_forecast(self, horizon: int = 5) -> ForecastResult:
        """Прогноз простым средним."""
        mean_value = np.mean(self.data)
        forecast = [mean_value] * horizon
        std = np.std(self.data)
        return ForecastResult(
            method=ForecastMethod.SIMPLE_AVERAGE,
            forecast_values=forecast,
            confidence_lower=[mean_value - 1.96 * std] * horizon,
            confidence_upper=[mean_value + 1.96 * std] * horizon
        )

    def moving_average_forecast(self, window: int = 3,
                                horizon: int = 5) -> ForecastResult:
        """Прогноз скользящим средним."""
        if window > len(self.data):
            window = len(self.data)
        last_values = self.data[-window:]
        ma = np.mean(last_values)
        std = np.std(last_values)
        return ForecastResult(
            method=ForecastMethod.MOVING_AVERAGE,
            forecast_values=[ma] * horizon,
            confidence_lower=[ma - 1.96 * std] * horizon,
            confidence_upper=[ma + 1.96 * std] * horizon
        )

    def exponential_smoothing_forecast(self, alpha: float = 0.3,
                                       horizon: int = 5) -> ForecastResult:
        """Экспоненциальное сглаживание."""
        if not 0 < alpha < 1:
            raise ValueError("alpha должен быть между 0 и 1")
        smoothed = [self.data[0]]
        for i in range(1, len(self.data)):
            smoothed.append(alpha * self.data[i] +
                            (1 - alpha) * smoothed[-1])
        std_error = (np.std(self.data[1:] - np.array(smoothed[:-1]))
                     if len(self.data) > 1
                     else np.std(self.data) * 0.1)
        return ForecastResult(
            method=ForecastMethod.EXPONENTIAL_SMOOTHING,
            forecast_values=[smoothed[-1]] * horizon,
            confidence_lower=[smoothed[-1] - 1.96 * std_error] * horizon,
            confidence_upper=[smoothed[-1] + 1.96 * std_error] * horizon
        )

    def linear_regression_forecast(self, horizon: int = 5) -> ForecastResult:
        """Прогноз линейной регрессией."""
        x = np.arange(len(self.data))
        y = self.data
        x_mean, y_mean = np.mean(x), np.mean(y)
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        future_x = np.arange(len(self.data), len(self.data) + horizon)
        forecast = slope * future_x + intercept
        y_pred = slope * x + intercept
        std_residuals = np.std(y - y_pred)
        return ForecastResult(
            method=ForecastMethod.LINEAR_REGRESSION,
            forecast_values=forecast.tolist(),
            confidence_lower=(forecast - 1.96 * std_residuals).tolist(),
            confidence_upper=(forecast + 1.96 * std_residuals).tolist()
        )

    def calculate_metrics(self, actual: List[float],
                          predicted: List[float]) -> Tuple[float, float]:
        """Расчет метрик RMSE и MAPE."""
        actual, predicted = np.array(actual), np.array(predicted)
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        mask = actual != 0
        mape = (np.mean(np.abs((actual[mask] - predicted[mask]) /
                  actual[mask])) * 100 if np.any(mask) else float('inf'))
        return rmse, mape

    def compare_methods(self, horizon: int = 5) -> Dict[ForecastMethod,
                                                        ForecastResult]:
        """Сравнение всех методов."""
        results = {}
        if len(self.data) > horizon + 5:
            train = self.data[:-horizon]
            test = self.data[-horizon:]
            temp = TimeSeriesForecaster(train.tolist())
            methods = [
                (ForecastMethod.SIMPLE_AVERAGE, temp.simple_average_forecast),
                (ForecastMethod.MOVING_AVERAGE, temp.moving_average_forecast),
                (ForecastMethod.EXPONENTIAL_SMOOTHING,
                 temp.exponential_smoothing_forecast),
                (ForecastMethod.LINEAR_REGRESSION,
                 temp.linear_regression_forecast)
            ]
            for method, func in methods:
                res = func(horizon=horizon)
                rmse, mape = self.calculate_metrics(test, res.forecast_values)
                res.rmse, res.mape = rmse, mape
                results[method] = res
        return results

    def get_best_method(self, horizon: int = 5) -> Optional[ForecastMethod]:
        """Определение лучшего метода по RMSE."""
        results = self.compare_methods(horizon)
        if not results:
            return None
        best = min(results.items(),
                   key=lambda x: x[1].rmse if x[1].rmse is not None else float('inf'))
        return best[0]