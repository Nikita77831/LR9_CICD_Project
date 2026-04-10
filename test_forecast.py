"""Тесты модуля прогнозирования."""
import unittest
import numpy as np
from forecast_module import TimeSeriesForecaster, ForecastMethod, ForecastResult

class TestTimeSeriesForecaster(unittest.TestCase):
    """Тесты для класса TimeSeriesForecaster."""
    def setUp(self):
        self.linear_data = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
        self.constant_data = [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
        self.forecaster = TimeSeriesForecaster(self.linear_data)

    def test_initialization(self):
        self.assertEqual(len(TimeSeriesForecaster([1, 2, 3]).data), 3)
        with self.assertRaises(ValueError):
            TimeSeriesForecaster([1, 2])

    def test_simple_average_forecast(self):
        res = self.forecaster.simple_average_forecast(horizon=3)
        self.assertEqual(len(res.forecast_values), 3)
        self.assertAlmostEqual(res.forecast_values[0],
                               np.mean(self.linear_data))

    def test_linear_regression_forecast(self):
        res = self.forecaster.linear_regression_forecast(horizon=3)
        self.assertAlmostEqual(res.forecast_values[0],
                               self.linear_data[-1] + 2, delta=0.1)

    def test_calculate_metrics(self):
        rmse, _ = self.forecaster.calculate_metrics(
            [10, 12, 14], [11, 13, 13])
        self.assertAlmostEqual(rmse, 1.0)

class TestForecastResult(unittest.TestCase):
    """Тесты для ForecastResult."""
    def test_creation(self):
        res = ForecastResult(
            ForecastMethod.SIMPLE_AVERAGE, [10], [9], [11], rmse=1.0)
        self.assertEqual(res.method, ForecastMethod.SIMPLE_AVERAGE)
        self.assertEqual(res.rmse, 1.0)