# **[Ensemble Methods Patterns] Reference Guide**

---

## **Overview**
Ensemble methods combine multiple machine learning models (e.g., classifiers, regressors) to improve robustness, accuracy, and generalization over individual models. This pattern leverages **diversity in weak learners** (e.g., decision trees, neural networks) to mitigate overfitting and bias. Common strategies include **bagging** (e.g., Random Forest), **boosting** (e.g., XGBoost, AdaBoost), and **voting/stacking** (e.g., bagging with voting classifiers).

Ensemble methods are widely used for structured data but have extensions for time series and unstructured data (e.g., deep ensemble models). Key trade-offs include computational cost (due to parallel training) and interpretability (black-box nature of aggregated models). This guide covers pattern definitions, implementation schemas, query examples, and integrations with other techniques.

---

## **Schema Reference**
### **1. Core Schema: EnsembleConfiguration**
Defines the core parameters for ensemble methods.

| **Property**               | **Type**            | **Description**                                                                 | **Required** | **Example Values**                     |
|----------------------------|---------------------|-------------------------------------------------------------------------------|--------------|-----------------------------------------|
| `ensemble_type`            | `string` (enum)     | Type of ensemble strategy (bagging, boosting, voting, stacking).              | ✅ Yes        | `"bagging"`, `"boosting"`, `"voting"`   |
| `base_models`              | `array[ModelConfig]`| List of weak learners (e.g., `{"model_type": "decision_tree", "params": {...}}`) | ✅ Yes        | `[{...}, {...}]`                        |
| `sampling_strategy`        | `string`            | Sampling method for bagging (e.g., "bootstrap", "random_subsampling").         | (Conditional)| `"bootstrap"`                          |
| `learning_rate`            | `float`             | Step size shrinkage for boosting (0.01–0.3 typically).                         | (Conditional)| `0.1`                                  |
| `n_estimators`             | `integer`           | Number of weak learners in the ensemble.                                     | ✅ Yes        | `100`                                  |
| `max_depth`                | `integer`           | Maximum depth of individual trees (for tree-based ensembles).                 | (Conditional)| `5`                                    |
| `random_state`             | `integer`           | Seed for reproducibility.                                                     | ✅ Yes        | `42`                                   |
| `cross_validation`         | `object`            | CV settings for hyperparameter tuning (e.g., `{"fold_count": 5, "strategy": "kfold"}`). | ❌ No       | `{"fold_count": 3}`                   |
| `metric`                   | `string` (enum)     | Evaluation metric (e.g., `"accuracy"`, `"f1_macro"`, `"rmse"`).              | ❌ No        | `"roc_auc"`                            |

---

### **2. ModelConfig Schema**
Describes individual weak learners in the ensemble.

| **Property**               | **Type**            | **Description**                                                                 | **Required** | **Example Values**                     |
|----------------------------|---------------------|-------------------------------------------------------------------------------|--------------|-----------------------------------------|
| `model_type`               | `string` (enum)     | Type of weak learner (e.g., `"decision_tree"`, `"logistic_regression"`, `"svm"`, `"neural_net"`). | ✅ Yes        | `"random_forest"`                      |
| `params`                   | `object`            | Model-specific hyperparameters (e.g., `{"cv": 10, "max_features": 0.5}`).     | ✅ Yes        | `{"min_samples_leaf": 5}`              |
| `feature_importance`       | `boolean`           | Whether to track feature importance for interpretability.                     | ❌ No        | `true`                                 |

---

### **3. BoostingSchema**
Boosting-specific parameters (applies to `ensemble_type: "boosting"`).

| **Property**               | **Type**            | **Description**                                                                 | **Required** | **Example Values**                     |
|----------------------------|---------------------|-------------------------------------------------------------------------------|--------------|-----------------------------------------|
| `boosting_algorithm`       | `string` (enum)     | Boosting variant (e.g., `"ada_boost"`, `"gradient_boost"`, `"xgboost"`).     | ✅ Yes        | `"xgboost"`                            |
| `loss_function`            | `string`            | Loss function (e.g., `"log_loss"`, `"squared_error"`, `"hinge"`).              | ❌ No        | `"logistic"`                           |
| `early_stopping_rounds`    | `integer`           | Rounds to wait before early stopping validation loss isn’t improving.         | ❌ No        | `10`                                   |

---

### **4. VotingSchema**
Voting ensemble-specific parameters (applies to `ensemble_type: "voting"`).

| **Property**               | **Type**            | **Description**                                                                 | **Required** | **Example Values**                     |
|----------------------------|---------------------|-------------------------------------------------------------------------------|--------------|-----------------------------------------|
| `voting_strategy`          | `string` (enum)     | Voting method (e.g., `"hard"`, `"soft"`).                                      | ✅ Yes        | `"soft"`                               |
| `classifier_weights`       | `array[float]`      | Weights for each classifier (normalized to sum=1).                           | ❌ No        | `[0.3, 0.7]`                           |

---

### **5. StackingSchema**
Stacking ensemble-specific parameters (applies to `ensemble_type: "stacking"`).

| **Property**               | **Type**            | **Description**                                                                 | **Required** | **Example Values**                     |
|----------------------------|---------------------|-------------------------------------------------------------------------------|--------------|-----------------------------------------|
| `meta_model`               | `ModelConfig`       | The final model trained on base-model predictions (e.g., `"logistic_regression"`). | ✅ Yes        | `{ "model_type": "logistic_regression" }` |
| `train_split_ratio`        | `float`             | Ratio of data to use for training the meta-model (0–1).                        | ❌ No        | `0.7`                                  |

---

### **6. OutputSchema**
Structure of the ensemble model's output.

| **Property**               | **Type**            | **Description**                                                                 | **Example**                              |
|----------------------------|---------------------|-------------------------------------------------------------------------------|------------------------------------------|
| `predictions`              | `array[float]`      | Predicted probabilities/scores for each sample.                               | `[0.85, 0.15, 0.72]`                     |
| `feature_importance`       | `array[object]`     | Feature importance scores (if applicable).                                      | `[{"feature": "age", "score": 0.45}]`   |
| `model_metrics`            | `object`            | Performance metrics (e.g., `"accuracy": 0.95`, `"auc": 0.87}`).               | `{"roc_auc": 0.92}`                     |
| `training_time`            | `float`             | Total training time in seconds.                                                | `42.5`                                   |

---

## **Query Examples**
### **1. Initialize a Random Forest Ensemble**
```python
ensemble_config = {
  "ensemble_type": "bagging",
  "base_models": [
    {"model_type": "decision_tree", "params": {"max_depth": 3}},
    {"model_type": "decision_tree", "params": {"max_depth": 5}}
  ],
  "n_estimators": 50,
  "random_state": 42,
  "sampling_strategy": "bootstrap"
}
model = EnsembleModel(ensemble_config).fit(X_train, y_train)
```

**Output:**
```json
{
  "model_metrics": {"accuracy": 0.91},
  "training_time": 12.3
}
```

---

### **2. Boosting with XGBoost**
```python
boosting_config = {
  "ensemble_type": "boosting",
  "base_models": [{
    "model_type": "xgboost",
    "params": {"learning_rate": 0.05, "max_depth": 4}
  }],
  "n_estimators": 200,
  "boosting_algorithm": "xgboost",
  "early_stopping_rounds": 10
}
model.fit(X_train, y_train)
```

**Output:**
```json
{
  "predictions": [0.95, 0.8, 0.72],
  "feature_importance": [
    {"feature": "income", "score": 0.6},
    {"feature": "age", "score": 0.4}
  ]
}
```

---

### **3. Voting Classifier**
```python
voting_config = {
  "ensemble_type": "voting",
  "base_models": [
    {"model_type": "logistic_regression"},
    {"model_type": "svm", "params": {"kernel": "rbf"}}
  ],
  "voting_strategy": "soft",
  "classifier_weights": [0.25, 0.75]
}
model = EnsembleModel(voting_config).fit(X_train, y_train)
```

**Output:**
```json
{
  "model_metrics": {"f1_macro": 0.85},
  "predictions": [0.87, 0.12]
}
```

---

### **4. Stacking Ensemble**
```python
stacking_config = {
  "ensemble_type": "stacking",
  "base_models": [
    {"model_type": "decision_tree"},
    {"model_type": "k_nearest_neighbors", "params": {"n_neighbors": 3}}
  ],
  "meta_model": {"model_type": "random_forest", "params": {"n_estimators": 10}},
  "train_split_ratio": 0.6
}
model.fit(X_train, y_train)
```

**Output:**
```json
{
  "predictions": [0.89, 0.91],
  "model_metrics": {"roc_auc": 0.93}
}
```

---

## **Implementation Details**
### **1. Key Concepts**
- **Diversity**: Weak learners contribute unique perspectives to reduce variance (e.g., different splits in bagging).
- **Aggregation**: Combining predictions via averaging (bagging), weighted voting (boosting), or meta-model training (stacking).
- **Bias-Variance Trade-off**: Ensembles reduce bias by combining models but may increase variance (mitigated via regularization or pruning).

### **2. Algorithm Selection**
| **Pattern**       | **Use Case**                          | **Pros**                              | **Cons**                              |
|-------------------|---------------------------------------|---------------------------------------|---------------------------------------|
| **Bagging**       | High-variance models (e.g., decision trees). | Reduces overfitting; parallelizable. | Slower than single models.           |
| **Boosting**      | Sequential improvement (e.g., XGBoost). | High accuracy; handles imbalanced data. | Prone to overfitting if not tuned.   |
| **Voting**        | Heterogeneous models (e.g., SVM + LR). | Robust to model weaknesses.          | Requires diverse base models.         |
| **Stacking**      | Complex relationships (meta-learning). | Highest accuracy potential.           | Computationally expensive.            |

### **3. Hyperparameter Tuning**
- **Bagging**: Adjust `n_estimators`, `max_depth`, and `sampling_strategy`.
- **Boosting**: Tune `learning_rate`, `n_estimators`, and `max_depth`.
- **Stacking**: Optimize meta-model parameters and `train_split_ratio`.

**Example Tuning with Optuna:**
```python
def objective(trial):
    config = {
        "boosting_algorithm": "xgboost",
        "learning_rate": trial.suggest_float("lr", 0.01, 0.3),
        "n_estimators": trial.suggest_int("n_est", 50, 500)
    }
    return cross_val_score(config, X, y, cv=3).mean()
study.optimize(objective, n_trials=100)
```

### **4. Scalability**
- **Parallelization**: Use `n_jobs=-1` (e.g., in `RandomForestClassifier`) to train models concurrently.
- **Approximate Methods**: For large datasets, use subsampling or online learning (e.g., `HistGradientBoostingRegressor`).

### **5. Interpretability**
- **Feature Importance**: Extract from base models (e.g., Gini importance in decision trees).
- **SHAP Values**: Post-process ensemble predictions for explainability.
- **Model-Agnostic Tools**: Use SHAP or LIME to analyze aggregated contributions.

### **6. Edge Cases**
- **Imbalanced Data**: Use class weights (e.g., `class_weight="balanced"`), oversampling, or boosting algorithms like XGBoost.
- **High-Dimensional Data**: Apply dimensionality reduction (PCA) or feature selection before ensembling.
- **Cold Start**: For streaming data, leverage online ensembles (e.g., `PartialFit` in sklearn).

---

## **Related Patterns**
1. **[Model Aggregation Patterns]**
   - Explores techniques like **bagging**, **boosting**, and **stacking** in isolation (e.g., how `RandomForest` differs from `GradientBoosting`).
   - *Key Link*: Defines base patterns used within ensemble configurations.

2. **[Hyperparameter Optimization]**
   - Covers methods like **GridSearchCV**, **RandomizedSearch**, and **Bayesian optimization** for tuning ensemble parameters.
   - *Key Link*: Optimizes `n_estimators`, `learning_rate`, etc., in ensemble configurations.

3. **[Feature Engineering for Ensembles]**
   - Discusses how to preprocess data (e.g., scaling, encoding) to improve ensemble performance.
   - *Example*: Normalize inputs for gradient boosting or encode categoricals for tree-based models.

4. **[Online Learning]**
   - Extends ensemble methods to streaming data (e.g., **online bagging** or **incremental boosting**).
   - *Key Link*: Use `SGDClassifier` with `partial_fit` for adaptive ensembles.

5. **[Ensemble Debugging]**
   - Techniques for diagnosing underperforming ensembles (e.g., **feature importance analysis**, **error analysis**).
   - *Tools*: Matshplotlib for plotting errors per weak learner.

---
## **References**
- Breiman, L. (2001). *Bagging Predictors*. **Machine Learning**.
- Friedman, J. (2001). *Greedy Function Approximation*. **Annals of Statistics**.
- Zou, H., & Hastie, T. (2005). *RegLog: Regularization Paths for Logistic Regression*.
- Scikit-learn Documentation: [Ensemble Methods](https://scikit-learn.org/stable/modules/ensemble.html).

---
**Last Updated**: [Date]
**Version**: 1.2