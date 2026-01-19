# **[Pattern] Time Series Forecasting Patterns – Reference Guide**

---

## **1. Overview**
Time Series Forecasting Patterns provide structured approaches for predicting future values in sequential data (e.g., sensor readings, financial trends, or web traffic). This pattern focuses on **identifying trends, seasonality, and anomalies** while enabling time-based predictions using machine learning or statistical models. Use cases include inventory planning, demand forecasting, and anomaly detection in IoT deployments.

Key scenarios:
- **Trend analysis** (detecting upward/downward patterns).
- **Seasonality detection** (repeating cycles, e.g., daily/weekly trends).
- **Anomaly flagging** (identifying outliers in streaming data).
- **Multi-step forecasting** (predicting future values over horizons).

This guide covers implementation strategies, schema design, and code examples for common forecasting patterns.

---

## **2. Schema Reference**
The following table outlines core entities and their fields for time series forecasting systems.

| **Entity**       | **Fields**                                                                 | **Description**                                                                 |
|------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **TimeSeries**   | `id (UUID)`, `name (string)`, `unit (string)`, `frequency (enum: daily/hrly/minly)`, `start_date (timestamp)`, `end_date (timestamp)` | Defines a time series dataset (e.g., weather stations, stock prices). |
| **DataPoint**    | `series_id (FK)`, `timestamp (timestamp)`, `value (float)`, `is_anomaly (bool)` | Individual data points with metadata (e.g., `is_anomaly` for error detection). |
| **ModelConfig**  | `id (UUID)`, `series_id (FK)`, `type (enum: ARIMA/Prophet/LSTM)`, `params (JSON)`, `last_trained (timestamp)` | Configuration for ML models (e.g., hyperparameters for Prophet). |
| **Forecast**     | `id (UUID)`, `series_id (FK)`, `model_id (FK)`, `start_date (timestamp)`, `end_date (timestamp)`, `predictions (JSON array)` | Stores model output (e.g., predicted values + confidence intervals). |
| **AlertRule**    | `id (UUID)`, `series_id (FK)`, `threshold (float)`, `condition (string)`, `status (enum: active/paused)` | Threshold-based alerts (e.g., "alert if value > 90th percentile"). |

**Example JSON for `DataPoint`:**
```json
{
  "series_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2023-10-01T12:00:00Z",
  "value": 42.5,
  "is_anomaly": false
}
```

---

## **3. Key Implementation Patterns**
### **3.1. Data Preprocessing**
Prepare time series data for modeling:
- **Resampling**: Aggregate hourly data to daily averages (e.g., `pandas.resample()`).
- **Missing Data**: Impute gaps using linear interpolation or forward-fill (`sklearn.impute`).
- **Normalization**: Scale values to `[0, 1]` using `MinMaxScaler`.

**Example (Python):**
```python
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Load data
df = pd.read_csv("sensor_data.csv", parse_dates=["timestamp"])

# Resample to daily
df_daily = df.set_index("timestamp").resample("D").mean()

# Normalize
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df_daily[["value"]])
```

---

### **3.2. Model Selection**
Choose a model based on requirements:

| **Model**       | **Use Case**                          | **Tools/Libraries**               |
|-----------------|---------------------------------------|-----------------------------------|
| **ARIMA**       | Univariate forecasting (e.g., sales)  | `statsmodels`                     |
| **Prophet**     | Handles seasonality + holidays        | `facebook/prophet`                |
| **LSTM**        | Deep learning for complex patterns    | `TensorFlow/Keras`                |
| **Exponential Smoothing** | Quick baseline (e.g., moving averages) | `sklearn.exponential_smoothing`   |

**Example (ARIMA in Python):**
```python
from statsmodels.tsa.arima.model import ARIMA

# Fit ARIMA(2,1,2)
model = ARIMA(df_daily["value"], order=(2, 1, 2))
results = model.fit()
forecast = results.forecast(steps=7)  # Predict next 7 days
```

---

### **3.3. Forecast Evaluation**
Validate predictions using metrics:
- **MAE (Mean Absolute Error)**: Average magnitude of errors.
- **RMSE (Root Mean Squared Error)**: Penalizes large errors.
- **MAPE (Mean Absolute Percentage Error)**: Percentage errors.

**Example:**
```python
from sklearn.metrics import mean_absolute_error

mae = mean_absolute_error(df_daily["value"], forecast)
print(f"MAE: {mae:.2f}")
```

---

### **3.4. Anomaly Detection**
Flag outliers using:
- **Z-Score**: Values > 3σ from mean.
- **Isolation Forest** (for non-linear patterns).

**Example (Isolation Forest):**
```python
from sklearn.ensemble import IsolationForest

clf = IsolationForest(contamination=0.01)  # Expect 1% anomalies
clf.fit(df_scaled)
df["is_anomaly"] = clf.predict(df_scaled) == -1
```

---

## **4. Query Examples**
### **4.1. Retrieve Forecast for a Time Series**
```sql
SELECT f.id, f.start_date, f.end_date, f.predictions
FROM Forecast f
JOIN ModelConfig m ON f.model_id = m.id
WHERE f.series_id = '550e8400-e29b-41d4-a716-446655440000'
AND m.type = 'Prophet';
```

### **4.2. Find Anomalies in Data (Time Range)**
```sql
SELECT dp.timestamp, dp.value
FROM DataPoint dp
WHERE dp.series_id = '550e8400-e29b-41d4-a716-446655440000'
AND dp.timestamp BETWEEN '2023-01-01' AND '2023-12-31'
AND dp.is_anomaly = TRUE
ORDER BY dp.timestamp DESC;
```

### **4.3. Update Model Configuration**
```python
# Python (updating via API or DB)
update_model_config = """
UPDATE ModelConfig
SET params = '{"seasonality": "weekly"}'
WHERE id = 'a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8'
"""
```

---

## **5. Error Handling & Edge Cases**
| **Issue**               | **Solution**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Missing data**        | Use forward-fill or interpolation.                                         |
| **High seasonality**    | Apply Fourier terms in ARIMA or Prophet’s seasonality settings.              |
| **Skewed distributions**| Log-transform data or use quantile regression.                             |
| **Model drift**         | Retrain models monthly (e.g., via Airflow).                               |
| **High cardinality**    | Aggregate rare categories (e.g., `GROUP BY YEAR(MONTH)`).                 |

---

## **6. Related Patterns**
1. **[Event-Driven Time Series]** – Integrate external events (e.g., holidays) into forecasts.
2. **[Dynamic Retraining]** – Automate model updates using MLOps pipelines (e.g., Kubeflow).
3. **[Real-Time Anomaly Detection]** – Stream data with Kafka + Flink for low-latency alerts.
4. **[Ensemble Forecasting]** – Combine multiple models (e.g., ARIMA + Prophet) for robustness.
5. **[Time-Series Cross-Validation]** – Use `TimeSeriesSplit` (scikit-learn) to avoid data leakage.

---
**See also:**
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [ARIMA in Statsmodels](https://www.statsmodels.org/stable/tsa.arima.html)