# **[Pattern] MLops Patterns Reference Guide**

## **Overview**
MLOps (Machine Learning Operations) patterns standardize how machine learning workflows are developed, deployed, and maintained to ensure scalability, reproducibility, and collaboration. This guide outlines best-practice patterns for building, training, and monitoring ML models in production. Key focus areas include **data versioning, model training pipelines, CI/CD for ML, A/B testing, and model monitoring**.

### **Core Problem**
Traditional DevOps practices often fail for ML projects due to:
- Non-deterministic model training (dependency on data, hyperparameters).
- Lack of versioning for datasets and models.
- High operational overhead in model deployment and monitoring.

### **Key Benefits**
✔ **Reproducibility** – Ensure consistent model training across environments.
✔ **Scalability** – Automate workflows for large datasets and teams.
✔ **Observability** – Track model performance and data drift in production.
✔ **Collaboration** – Standardize workflows for ML engineers, data scientists, and DevOps.

---

## **Schema Reference**

| **Pattern**               | **Description**                                                                                     | **Key Components**                                                                                     | **Tools/Libraries**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Data Versioning**       | Track and version datasets to ensure reproducibility.                                                | Data lake, metadata store, version control (e.g., DVC, Delta Lake).                                   | [Apache Delta Lake](https://delta.io/), [MLflow](https://mlflow.org/), [DVC](https://dvc.org/)           |
| **Model Training Pipeline** | Automate training, hyperparameter tuning, and model registration.                                  | Jupyter notebooks, Spark MLlib, TensorFlow Pipelines (TFX).                                            | [TFX](https://www.tensorflow.org/tfx), [Kubeflow](https://www.kubeflow.org/), [Ray Tune](https://docs.ray.io/en/latest/tune/index.html) |
| **CI/CD for ML**          | Automate testing, validation, and deployment of ML models.                                          | Git, Kubernetes, containerization (Docker), CI/CD pipelines (GitHub Actions, Argo Workflows).        | [GitHub Actions](https://github.com/features/actions), [Argo Workflows](https://argoproj.github.io/argo-workflows/) |
| **Feature Store**         | Centralize feature engineering for consistency across ML tasks.                                     | Feature tables, metadata storage, online/offline access.                                             | [Feast](https://feast.dev/), [Hopsworks](https://www.hopsworks.ai/), [Tecton](https://tecton.ai/)       |
| **Model Deployment**      | Deploy models as scalable, low-latency APIs or batch services.                                      | REST APIs, gRPC, serverless (AWS Lambda), Kubernetes (KServe).                                      | [FastAPI](https://fastapi.tiangolo.com/), [KServe](https://github.com/kserve/kserve), [AWS SageMaker](https://aws.amazon.com/sagemaker/) |
| **A/B Testing**           | Compare model variants in production to measure impact.                                             | Traffic splitting, monitoring, analytics (Prometheus, Grafana).                                      | [Google Optimize](https://optimize.google.com/), [VWO](https://www.vwo.com/), [LaunchDarkly](https://launchdarkly.com/) |
| **Model Monitoring**      | Detect performance degradation, data drift, and concept drift.                                      | Logging, metrics, alerting (Prometheus, MLflow Model Monitor).                                       | [MLflow Model Monitor](https://mlflow.org/docs/latest/model-monitor/index.html), [Evidently](https://www.evidly.ai/) |
| **Experiment Tracking**   | Log experiments for reproducibility and hyperparameter optimization.                               | Metadata storage, visualization (MLflow, Weights & Biases).                                           | [MLflow](https://mlflow.org/), [Weights & Biases](https://wandb.ai/), [TensorBoard](https://www.tensorflow.org/tensorboard) |
| **Model Registry**        | Catalog and manage models in production (versioning, approvals, rollbacks).                         | Metadata store, governance policies.                                                                   | [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry/index.html), [ModelHub](https://www.modelhubs.com/) |

---

## **Implementation Details**

### **1. Data Versioning**
- **Purpose**: Ensure datasets used in training are reproducible and traceable.
- **Key Steps**:
  1. Store raw/processed data in a **data lake** (e.g., S3, Delta Lake).
  2. Track metadata (e.g., checksums, splits) in a **metadata store** (e.g., MLflow, DVC).
  3. Use **DVC (Data Version Control)** to link datasets to code versions.
- **Example Workflow**:
  ```python
  import dvc.repo
  repo = dvc.repo.DVCRepo(".")
  repo.dvc.add("data/raw/train.csv", "data/processed/train_v1.dvc")
  repo.dvc.commit("Added v1 of training data")
  ```

### **2. Model Training Pipeline (TFX Example)**
- **Purpose**: Automate training with data validation, hyperparameter tuning, and model registration.
- **Key Steps**:
  1. Define a **TFX pipeline** (`Pipeline`) with components:
     - `CsvExampleGen` (load data)
     - `ExampleValidator` (check data quality)
     - `Transformer` (feature engineering)
     - `Trainer` (train model)
     - `Evaluator` (log metrics)
     - `Push` (register to MLflow)
  2. Deploy pipeline on **Kubeflow** or **Airflow**.
- **Example Pipeline**:
  ```python
  from tfx.orchestration import pipeline
  from tfx.components import CsvExampleGen, ExampleValidator, Trainer, Evaluator, Push

  def create_pipeline():
      return pipeline.Pipeline(
          pipeline_name="train_pipeline",
          pipeline_root="./pipeline_root",
          components=[
              CsvExampleGen(input_base="gs://bucket/data"),
              ExampleValidator(examples=example_gen.outputs["examples"]),
              Trainer(
                  examples=example_gen.outputs["examples"],
                  transform_graph=transform.outputs["transform_graph"],
                  schema=example_gen.outputs["schema"],
              ),
              Evaluator(
                  examples=example_gen.outputs["examples"],
                  model=trainer.outputs["model"],
              ),
              Push(model=trainer.outputs["model"], server_uri="http://mlflow-server:5000"),
          ]
      )
  ```

### **3. CI/CD for ML**
- **Purpose**: Automate testing, validation, and deployment of models.
- **Key Steps**:
  1. **Test Model**: Run unit tests (e.g., `pytest`) and validation scripts.
  2. **Build Container**: Package model + dependencies in a **Docker image**.
  3. **Deploy**: Use **Kubernetes (KServe)** or **serverless (AWS Lambda)**.
  4. **Rollback**: Implement canary deployments or traffic shifting.
- **Example GitHub Actions Workflow**:
  ```yaml
  name: ML Model CI/CD
  on: [push]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - run: pip install -r requirements.txt
        - run: pytest tests/
    build-and-deploy:
      needs: test
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - run: docker build -t my-model:latest .
        - run: kubectl apply -f k8s/deployment.yaml
  ```

### **4. Feature Store (Feast Example)**
- **Purpose**: Centralize feature engineering for consistency.
- **Key Steps**:
  1. Define **feature repositories** (e.g., user demographics, transaction history).
  2. Use **online/offline stores** for low-latency access.
  3. Sync features with training data.
- **Example Feast Setup**:
  ```python
  from feast import FeatureStore

  feature_store = FeatureStore(repo_path=".")
  feature_store.apply([UserDemographics, TransactionHistory])
  online_store = feature_store.get_online_store()
  features = online_store.get_feature_vector(
      feature_refs=["user_demographics:age", "transaction_history:spend"],
      entity_rows=[{"user_id": "123"}]
  )
  ```

### **5. Model Deployment (FastAPI + Docker)**
- **Purpose**: Deploy models as scalable APIs.
- **Key Steps**:
  1. Serialize model (e.g., `joblib`, `pkl`).
  2. Build **FastAPI** endpoint.
  3. Containerize with **Docker**.
  4. Deploy to **Kubernetes** or **AWS ECS**.
- **Example FastAPI App**:
  ```python
  from fastapi import FastAPI
  import pickle

  app = FastAPI()
  model = pickle.load(open("model.pkl", "rb"))

  @app.post("/predict")
  def predict(data: dict):
      prediction = model.predict([data["features"]])
      return {"prediction": prediction.tolist()}
  ```
- **Dockerfile**:
  ```dockerfile
  FROM python:3.9-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

### **6. Model Monitoring (MLflow Model Monitor)**
- **Purpose**: Detect performance drift and data skewness.
- **Key Steps**:
  1. Schedule **periodic monitoring** (e.g., daily).
  2. Compare **prediction distributions** (e.g., KL divergence).
  3. Alert on **threshold breaches** (e.g., accuracy drop >5%).
- **Example Setup**:
  ```python
  from mlflow.models import ModelMonitor

  monitor = ModelMonitor(
      model_uri="models:/my_model/Production",
      monitor_path="data/monitoring.csv",
      scheduler=schedulers.DailyScheduler(run_frequency=1),
      alert_threshold=0.05,
  )
  monitor.run()
  ```

### **7. Experiment Tracking (MLflow)**
- **Purpose**: Log hyperparameters, metrics, and artifacts.
- **Key Steps**:
  1. Track experiments with **MLflow**:
     ```python
     import mlflow

     with mlflow.start_run():
         mlflow.log_param("learning_rate", 0.01)
         mlflow.log_metric("accuracy", 0.95)
         mlflow.log_artifact("model.pkl")
     ```
  2. Reproduce runs using **MLflow “Run ID”**.

---

## **Query Examples**

### **1. Querying Data Versioning (DVC)**
```bash
# List tracked datasets
dvc status

# Revert to a specific data version
dvc checkout data/processed/train_v1.dvc
```

### **2. Querying Model Registry (MLflow)**
```bash
# List registered models
mlflow search models --filter "tags.mlflow.runName = 'prod_model'"

# Transition model to "Production"
mlflow transition-models --name "my_model" --stage "Production" --archive-versions
```

### **3. Querying Feature Store (Feast)**
```python
from feast import FeatureStore

feature_store = FeatureStore(repo_path=".")
feature_store.get_online_store().get_online_features(
    feature_refs=["user_demographics:age"],
    entity_rows=[{"user_id": "123"}]
)
```

### **4. Querying Model Monitoring (Prometheus)**
```bash
# Check prediction latency (PromQL)
histogram_quantile(0.95, sum(rate(model_latency_bucket[5m])) by (le))
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Blue-Green Deployment** | Deploy two identical environments and switch traffic abruptly.                                      | Low-risk model updates (e.g., A/B testing framework).                                                  |
| **Canary Deployment**     | Gradually shift traffic to a new model version.                                                     | High-risk updates (e.g., production models).                                                           |
| **Feature Flags**         | Dynamically enable/disable model features without redeploying.                                      | Experimenting with new model inputs or outputs.                                                          |
| **Model Retraining**      | Automatically retrain models on new data when performance degrades.                                 | Time-sensitive applications (e.g., fraud detection).                                                    |
| **Data Pipeline as Code** | Version-control data pipelines (e.g., with Airflow DAGs).                                          | Reproducible ETL workflows.                                                                              |
| **Model Explainability**  | Use SHAP/LIME to interpret model predictions.                                                       | Regulatory compliance (e.g., healthcare, finance).                                                     |
| **Multi-Model Ensembles** | Combine predictions from multiple models (e.g., weighted voting).                                    | Improving robustness (e.g., ensemble of CNN + transformer models).                                       |

---

## **Best Practices**
1. **Start Small**: Adopt MLOps patterns incrementally (e.g., begin with experiment tracking).
2. **Automate Early**: Use CI/CD for model testing from day one.
3. **Monitor Continuously**: Set up drift detection for production models.
4. **Document**: Use tools like **MLflow Metadata Store** or **SkiptheDisco** for workflow docs.
5. **Security**: Enforce model governance (e.g., MLflow Model Registry roles).

---
**Next Steps**:
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [TFX Guide](https://www.tensorflow.org/tfx/guide)
- [Kubeflow Documentation](https://www.kubeflow.org/docs/)