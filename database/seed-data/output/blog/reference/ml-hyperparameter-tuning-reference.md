# **[Pattern] Hyperparameter Tuning Patterns – Reference Guide**

---

## **Overview**
Hyperparameter tuning is the systematic optimization of model parameters that are **not learned during training** (e.g., learning rate, batch size, tree depth in decision trees) to maximize model performance. This reference outlines **structured tuning patterns**—best practices, automation strategies, and trade-off considerations—to accelerate experimental workflows in machine learning (ML) and deep learning (DL).

### **Core Objectives**
- **Efficiency:** Automate search to reduce manual iteration.
- **Generalization:** Avoid overfitting tuning parameters to validation data.
- **Reproducibility:** Standardize tuning workflows for collaborative teams.
- **Scalability:** Handle high-dimensional parameter spaces for complex models.

---
## **Schema Reference**

| **Component**               | **Description**                                                                 | **Key Parameters**                                                                 | **Supported Tools**                          |
|-----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|---------------------------------------------|
| **Search Strategy**         | Method for sampling hyperparameters from the space (e.g., grid, random, BOHB). | `strategy` (e.g., `"RandomSearch"`, `"BayesianOptimization"`), `n_iter`, `budget` | Optuna, Ray Tune, Hyperopt, Sklearn       |
| **Objective Function**      | Evaluates model performance (e.g., validation accuracy, AUC, RMSE).          | `metric` (e.g., `"accuracy"`, `"f1"`), `early_stopping` (bool)                   | All ML frameworks                           |
| **Hyperparameter Space**    | Defines the search space (e.g., ranges, distributions, categorical choices).  | `param_name`: `{type: "continuous", "categorical", "choice"}`, `low/hi`, `values` | Config files, Optuna samplers, PyTorch Lightning |
| **Resource Constraints**     | Limits compute budget (e.g., GPU hours, parallel jobs).                       | `max_trials`, `timeout_minutes`, `parallel_jobs`                                   | Slurm, Kubernetes, SageMaker                |
| **Reproducibility Controls**| Ensures consistency across runs (e.g., seeds, logging).                       | `random_seed`, `logging_dir`, `version_control`                                   | MLflow, DVC, Weights & Biases               |

---

## **Implementation Patterns**

### **1. Grid vs. Random Search**
| **Pattern**         | **Use Case**                          | **Pros**                                  | **Cons**                                  | **Example Code**                          |
|---------------------|---------------------------------------|-------------------------------------------|-------------------------------------------|-------------------------------------------|
| **Grid Search**     | Small parameter spaces (<10 parameters) | Exhaustive coverage; easy interpretation. | Inefficient for large spaces.             | ```python<br>from sklearn.model_selection import GridSearchCV<br>params = {'C': [0.1, 1, 10], 'kernel': ['linear', 'rbf']}<br>grid = GridSearchCV(model, params, cv=5)``` |
| **Random Search**   | High-dimensional spaces (e.g., >10 params) | Scales better; often outperforms grid.    | Less reproducible sampling.               | ```python<br>from skopt import gp_minimize<br>sampler = RandomSearch(params, n_calls=50)<br>sampler.run(objective_func)``` |

**Trade-off:** Random search often finds better hyperparameters faster for continuous spaces (Bergstra & Bengio, 2012).

---

### **2. Bayesian Optimization**
**Pattern:** Adaptive sampling using probabilistic models (e.g., Gaussian Processes, Tree-structured Parzen Estimators).
- **When to Use:** Expensive-to-evaluate models (e.g., deep neural networks) where few trials are feasible.
- **Key Libraries:** Optuna (`TPESampler`), Hyperopt (`tpe`), Ray Tune (`BayesianOptimizationSampler`).
- **Example (Optuna):**
  ```python
  import optuna
  def objective(trial):
      lr = trial.suggest_float('lr', 1e-5, 1e-2)
      model = build_model(lr=lr)
      return evaluate_model(model)
  study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler())
  study.optimize(objective, n_trials=100)
  ```

---
### **3. Evolutionary Algorithms**
**Pattern:** Mimics natural selection (e.g., genetic algorithms, evolutionary strategies).
- **When to Use:** Discrete or mixed parameter spaces (e.g., architecture search).
- **Example (Optuna + Genetic Algorithm):**
  ```python
  from optuna.pruners import MedianPruner
  study = optuna.create_study(direction='minimize', pruner=MedianPruner())
  study.optimize(objective, study_dir='./results')
  ```

---
### **4. Hyperband**
**Pattern:** Bandit-based early stopping to balance exploration/exploitation.
- **When to Use:** Large-scale distributed tuning (e.g., SageMaker, Ray Tune).
- **Example (Ray Tune):**
  ```python
  from ray.tune.schedulers import HyperbandScheduler
  scheduler = HyperbandScheduler(
      time_attr='training_iteration',
      max_t=100,
      grace_period=5,
      reduction_factor=3
  )
  ```

---
### **5. Population-Based Training (PBT)**
**Pattern:** Dynamically adjusts individual trials’ hyperparameters based on peers.
- **When to Use:** Online learning or continuous tuning (e.g., reinforcement learning).
- **Example (Ray Tune):**
  ```python
  from ray.tune.integration.pytorch import TuneReportCallback
  tuner = tune.Tuner(
      trainable_fn,
      tune_config=HyperBandConfig(
          time_attr='epoch',
          metric='val_loss',
          mode='min'
      ),
      run_config=AirConfig(stop={"training_iteration": 50}),
      param_space={"lr": tune.loguniform(1e-5, 1e-2)}
  )
  ```

---
## **Query Examples**

### **1. Find Optimal Learning Rate for a CNN**
```python
# Optuna Example
def objective(trial):
    lr = trial.suggest_float("lr", 1e-5, 1e-2, log=True)
    model = CNN(lr=lr)
    model.fit(train_loader, val_loader)
    return model.evaluate(val_loader)

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50)
print(f"Best LR: {study.best_params['lr']}")
```

### **2. Distributed Random Search with Ray Tune**
```python
from ray import tune
from ray.tune.schedulers import AsyncHyperBandScheduler

def train_model(config):
    model = RandomForestClassifier(**config)
    model.fit(X_train, y_train)
    return {"accuracy": model.score(X_val, y_val)}

search_space = {
    "n_estimators": tune.choice([50, 100, 200]),
    "max_depth": tune.randint(3, 20),
    "learning_rate": tune.uniform(0.01, 0.2)
}

analysis = tune.run(
    train_model,
    config=search_space,
    scheduler=AsyncHyperBandScheduler(),
    num_samples=100,
    resources_per_trial={"cpu": 4, "gpu": 0}
)
```

### **3. Hyperparameter Logging with MLflow**
```python
import mlflow.sklearn

with mlflow.start_run():
    params = {"C": 0.1, "kernel": "rbf"}
    model = GridSearchCV(SVR(), params, cv=3)
    model.fit(X_train, y_train)
    mlflow.log_params(params)
    mlflow.log_metrics({"val_score": model.best_score_})
```

---
## **Advanced Techniques**

### **1. Early Stopping**
- **Pattern:** Abort poor-performing trials early to save resources.
- **Tools:** Optuna (`pruner`), Ray Tune (`stop`), TensorFlow `EarlyStopping`.
- **Example (Optuna):**
  ```python
  pruner = optuna.pruners.MedianPruner(n_warmup_steps=5)
  study = optuna.create_study(pruner=pruner)
  ```

### **2. Multi-Objective Tuning**
- **Pattern:** Optimize for multiple metrics (e.g., accuracy *and* inference speed).
- **Tools:** Optuna (`direction='minimize'` + multi-objective objective), Pareto fronts.
- **Example:**
  ```python
  def objective(trial):
      config = {
          "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128]),
          "dropout": trial.suggest_float("dropout", 0.0, 0.5)
      }
      model = build_model(**config)
      loss, accuracy = evaluate(model)
      return {"loss": loss, "accuracy": accuracy}  # Pareto optimization
  ```

### **3. Transfer Learning Tuning**
- **Pattern:** Fine-tune pre-trained models (e.g., BERT, ResNet) with limited tuning.
- **Strategy:** Freeze early layers; tune only dense heads/learning rate.
- **Example (PyTorch Lightning):**
  ```python
  from pytorch_lightning import Trainer
  trainer = Trainer(
      max_epochs=10,
      accelerator="gpu",
      callbacks=[ModelCheckpoint(monitor="val_loss")]
  )
  model = MyModel.load_from_checkpoint("pretrained.ckpt")
  trainer.fit(model, train_dataloader, val_dataloader)
  ```

---
## **Requirements & Constraints**

| **Constraint**               | **Mitigation Strategy**                                                                 | **Tools**                          |
|------------------------------|---------------------------------------------------------------------------------------|------------------------------------|
| **Compute Budget**           | Use pruners (Optuna) or schedulers (Ray Tune) to stop early.                          | Optuna, Hyperband                  |
| **Parameter Dependencies**   | Define conditional spaces (e.g., `if lr < 0.01 then use "adam" optimizer`).            | Optuna `suggest_*` methods         |
| **Reproducibility**          | Set seeds, log configs, and version-control datasets.                                  | MLflow, DVC, `torch.manual_seed()` |
| **Distributed Tuning**       | Partition trials across clusters (e.g., Slurm, Kubernetes).                            | Ray Tune, SageMaker Distributed    |
| **Bias in Validation**       | Use cross-validation or time-based splits to avoid leakage.                            | Sklearn `cross_val_score`          |

---
## **Related Patterns**
1. **[Model Selection Patterns]**
   - Compare architectures (e.g., CNN vs. Transformer) alongside hyperparameter tuning.
2. **[Feature Engineering Patterns]**
   - Optimize preprocessing (e.g., scaling, embeddings) concurrently with hyperparameters.
3. **[Distributed Training Patterns]**
   - Scale tuning jobs across GPUs/TPUs (e.g., Horovod, PyTorch DDP).
4. **[Automated ML (AutoML) Pipelines]**
   - Integrate tuning with feature selection, architecture search (e.g., AutoGluon, H2O).
5. **[Explainability Patterns]**
   - Analyze tuning results for interpretability (e.g., SHAP values for hyperparameter importance).

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Overfitting to Validation Data** | Tuning parameters are treated as free hyperparameters.                        | Use nested cross-validation or separate holdout sets.                        |
| **Slow Convergence**               | Pruner too aggressive or small search space.                                   | Increase `n_trials`, adjust `pruner` tolerance, or use Bayesian methods.     |
| **Reproducibility Failures**       | Random seeds not set or environment drift.                                    | Pin versions (`pip freeze`), set `torch.manual_seed()`, log hyperparameters. |
| **Resource Wastage**               | Trials run to completion despite early signs of failure.                       | Implement `early_stopping` or `pruning` callbacks.                          |

---
## **References**
1. Bergstra, J., & Bengio, Y. (2012). *Random Search for Hyper-Parameter Optimization*.
2. Snoek, J., Larochelle, H., & Adams, R. (2012). *Practical Bayesian Optimization of Machine Learning Algorithms*.
3. Optuna Documentation: [https://optuna.org](https://optuna.org)
4. Ray Tune: [https://docs.ray.io/en/latest/tune/index.html](https://docs.ray.io/en/latest/tune/index.html)