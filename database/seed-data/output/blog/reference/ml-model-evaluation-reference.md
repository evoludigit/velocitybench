---

# **[Pattern] Model Evaluation Patterns – Reference Guide**

---

## **Overview**
This pattern outlines best practices for systematically evaluating machine learning models to ensure their reliability, performance, and compliance with business requirements. Effective model evaluation prevents deployment failures, optimizes resource use, and builds stakeholder trust. Common practices include splitting data into training/validation/test sets, cross-validation, performance metrics (e.g., accuracy, precision, ROC-AUC), and sensitivity analysis for edge cases. This pattern ensures consistency, transparency, and reproducibility in model assessment—critical for production-grade AI/ML systems.

---

## **Implementation Details**

### **Key Concepts**
| Term | Definition |
|------|------------|
| **Training Set** | Data used to optimize model parameters (e.g., weights in neural networks). Do not use this for evaluation. |
| **Validation Set** | Subset of training data (or held-out data) to tune hyperparameters and detect overfitting. |
| **Test Set** | Unseen data reserved for final evaluation. Must **never** be used to inform model decisions. |
| **Cross-Validation** | Technique (e.g., k-fold) to maximize data utilization by iteratively training/validating on shuffled splits. |
| **Performance Metrics** | Quantitative measures to compare models (e.g., accuracy, precision/recall for classification; RMSE for regression). |
| **Bias-Variance Tradeoff** | Balancing model complexity: High bias (underfitting) vs. high variance (overfitting). |
| **Edge Case Testing** | Evaluating model robustness on rare, adversarial, or noisy inputs. |
| **Explainability** | Methods (e.g., SHAP, LIME) to interpret model decisions and detect bias. |
| **Continual Evaluation** | Monitoring model drift and retraining pipelines post-deployment. |

---

## **Schema Reference**

### **Evaluation Pipeline Schema**
| Step | Components | Tools/Libraries |
|------|------------|----------------|
| **1. Data Splitting** | - Train/validation/test splits (e.g., 60/20/20) <br> - Stratification for imbalanced data | `sklearn.model_selection.train_test_split`, `pandas` |
| **2. Baseline Model** | - Logistic regression, decision trees, or random forests for initial comparison | `sklearn.linear_model`, `sklearn.tree` |
| **3. Hyperparameter Tuning** | - Grid/Random search, Bayesian optimization | `sklearn.model_selection.GridSearchCV`, `hyperopt`, `Optuna` |
| **4. Performance Metrics** | - Accuracy, precision/recall, F1, ROC-AUC (classification) <br> - RMSE, MAE, R² (regression) | `sklearn.metrics`, `tensorflow.metrics` |
| **5. Error Analysis** | - Confusion matrix, precision/recall tradeoff curves <br> - Feature importance plots | `matplotlib`, `seaborn`, `eli5` |
| **6. Edge Case Testing** | - Synthetic data augmentation <br> - Adversarial examples (e.g., FGSM attacks) | `tensorflow_attack`, `capstone` |
| **7. Explainability** | - SHAP/LIME values <br> - Attention weights (transformers) | `shap`, `lime`, `captum` |
| **8. Continual Evaluation** | - A/B testing <br> - Drift detection (e.g., Kolmogorov-Smirnov test) | `statsmodels`, `alibi-detect` |

---

## **Query Examples**
### **1. Basic Model Evaluation (Classification)**
```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
```
**Output:**
```
              precision  recall  f1-score   support
           0       0.92      0.89      0.91       100
           1       0.88      0.90      0.89       120
    accuracy                           0.89       220
   macro avg       0.90      0.89      0.90       220
weighted avg       0.90      0.89      0.90       220
```

---

### **2. Cross-Validation for Robustness**
```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
print(f"Mean ROC-AUC: {scores.mean():.3f} ± {scores.std():.3f}")
```
**Output:**
```
Mean ROC-AUC: 0.912 ± 0.021
```

---

### **3. Edge Case Detection (Adversarial Examples)**
```python
import tensorflow as tf
from tensorflow_attack import AdversarialExampleGenerator

generator = AdversarialExampleGenerator(
    model,
    input_shape=(1, X_train.shape[1]),
    clip_min=0.0,
    clip_max=1.0,
    attack="FGSM"
)
adversarial_input, adversarial_output = generator.perturb(X_train[0:1])
print(f"Original pred: {model.predict(X_train[0:1])}")
print(f"Adversarial pred: {model.predict(adversarial_input)}")
```

---

### **4. Explainability with SHAP**
```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test[:100])
shap.summary_plot(shap_values, X_test[:100])
```
**Output:** A force plot or summary bar chart showing feature contributions.

---

## **Related Patterns**
| Pattern | Description | Use Case |
|---------|-------------|----------|
| **[Data Versioning](https://ml-ops.github.io/patterns/data-versioning/)** | Track dataset changes to ensure reproducibility in evaluation. | Audit trail for model performance drift. |
| **[Feature Store](https://ml-ops.github.io/patterns/feature-store/)** | Centralized feature management to avoid inconsistencies in evaluation. | Real-time feature serving for testing. |
| **[Model Registry](https://ml-ops.github.io/patterns/model-registry/)** | Catalog evaluated models with metadata (e.g., hyperparameters, metrics). | Standardized model comparison. |
| **[A/B Testing](https://ml-ops.github.io/patterns/ab-testing/)** | Deploy candidate models side-by-side to compare real-world performance. | Production confidence in model switching. |
| **[Drift Detection](https://ml-past.github.io/patterns/drift-detection/)** | Monitor data/model drift post-deployment to trigger re-evaluation. | Maintain model reliability over time. |
| **[Canary Releases](https://ml-ops.github.io/patterns/canary-releases/)** | Gradually roll out models to a subset of users for stress testing. | Reduce risk of widespread failures. |

---

## **Best Practices**
1. **Avoid Data Leakage**: Ensure no test/validation data influences training (e.g., time-based splits for temporal data).
2. **Stratify Splits**: Maintain class distribution in splits for imbalanced datasets.
3. **Use Multiple Metrics**: Avoid relying solely on accuracy (e.g., precision/recall for imbalanced data).
4. **Automate Evaluation**: Integrate pipelines (e.g., MLflow, Kubeflow) to log metrics and artifacts.
5. **Document Assumptions**: Record data preprocessing steps, evaluation constraints, and limitations.
6. **Iterative Refinement**: Treat evaluation as a feedback loop—retrain and re-evaluate as needed.

---
**Last Updated:** [Insert Date]
**Version:** 1.2