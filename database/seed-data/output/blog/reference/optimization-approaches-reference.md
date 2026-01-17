**[Pattern] Optimization Approaches – Reference Guide**

---

### **1. Overview**
The **Optimization Approaches** pattern structures how systems evaluate and refine processes to achieve better performance, efficiency, or resource allocation. This pattern is commonly used in **machine learning (ML), algorithmic design, DevOps, infrastructure provisioning, and business workflows** where iterative adaptation is key.

Key use cases:
- **ML Model Training**: Hyperparameter tuning (e.g., grid search, Bayesian optimization) to optimize accuracy/latency.
- **Cloud Cost Reduction**: Dynamic resource scaling (e.g., Kubernetes HPA) to minimize spend.
- **Supply Chain**: Route optimization for logistics (e.g., genetic algorithms).
- **A/B Testing**: Automated experiment prioritization based on projected impact.

This guide covers **core approaches**, their trade-offs, and implementation details for common frameworks (e.g., TensorFlow, Kubernetes, or custom scripts).

---

### **2. Schema Reference**
Below is a categorized table of optimization approaches, their **input parameters**, **outputs**, and **key constraints**.

| **Category**          | **Approach**               | **Inputs**                          | **Outputs**                          | **Constraints**                                                                 | **Best For**                          |
|-----------------------|----------------------------|--------------------------------------|--------------------------------------|----------------------------------------------------------------------------------|---------------------------------------|
| **Deterministic**     | **Grid Search**            | Hyperparameter ranges (e.g., `lr=[0.001, 0.1]`) | Best-performing combination         | High computational cost; exhaustive                                           | Small search spaces                   |
|                       | **Random Search**          | Same as Grid Search                  | Best-performing combination         | Faster than Grid Search but still brute-force                                 | Medium-sized spaces                   |
| **Probabilistic**     | **Bayesian Optimization**  | Surrogate model (e.g., Gaussian Process), acquisition function (e.g., EI) | Optimal hyperparameters + uncertainty bounds | Requires initial random samples; complex setup                               | Expensive-to-evaluate objectives      |
|                       | **Genetic Algorithms**     | Population size, crossover/mutation rates, fitness function | Optimized "genome" (e.g., route plan) | Slow convergence; sensitive to initialization                              | Combinatorial problems (e.g., scheduling) |
| **Gradient-Based**    | **Stochastic Gradient Descent (SGD)** | Loss function, learning rate (`α`), momentum (`β`) | Trained model weights                | Requires differentiable loss; sensitive to `α` and batch size                   | Large-scale ML (e.g., deep learning)  |
|                       | **Adam (Adaptive Moment Estimation)** | Same as SGD + betas (`β₁`, `β₂`)     | Trained model weights                | Handles sparse gradients better than SGD; adaptive learning rates                 | Default ML optimization               |
| **Metaheuristics**    | **Simulated Annealing**    | Initial solution, cooling schedule   | Near-global optimum                  | Risk of local optima; parameter tuning required                               | Discrete optimization problems        |
|                       | **Particle Swarm Optimization (PSO)** | Swarm size, velocity/inertia params | Optimized solution (e.g., control params) | Parallelizable but complex to tune                                         | Multi-objective optimization           |
| **Hybrid**            | **AutoML (e.g., AutoKeras)** | Dataset, resource constraints       | Optimized model architecture/params  | High resource usage; black-box output                                       | Non-experts automating ML pipelines    |
| **Reinforcement Learning (RL)** | **Proximal Policy Optimization (PPO)** | Policy network, reward function      | Trained policy (e.g., robot control) | Requires RL environment; unstable training                                | Sequential decision-making tasks       |

---

### **3. Query Examples**
#### **3.1 Grid Search in Python (Scikit-Learn)**
```python
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

params = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5]
}

model = RandomForestClassifier()
grid_search = GridSearchCV(model, params, cv=5).fit(X_train, y_train)
print("Best params:", grid_search.best_params_)
```
**Output**:
```plaintext
Best params: {'n_estimators': 100, 'max_depth': 10, 'min_samples_split': 2}
```

#### **3.2 Bayesian Optimization (Hyperopt)**
```python
from hyperopt import fmin, tpe, hp
import numpy as np

def objective(params):
    lr = params['lr']
    model = train_model(X_train, y_train, lr=lr)
    return -cross_val_score(model, X_test, y_test, cv=3).mean()

space = hp.uniform('lr', 0.001, 0.1)
best = fmin(objective, space, algo=tpe.suggest, max_evals=50)
print("Best learning rate:", np.exp(best['lr']))
```
**Output**:
```plaintext
Best learning rate: 0.0054
```

#### **3.3 Kubernetes Horizontal Pod Autoscaler (HPA)**
```yaml
# hpa-config.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```
**Apply**:
```bash
kubectl apply -f hpa-config.yaml
```

---

### **4. Implementation Details**
#### **4.1 Core Concepts**
- **Objective Function**: The metric to optimize (e.g., validation accuracy, cost per request).
- **Search Space**: Defines possible parameter values (discrete/continuous).
- **Acquisition Function**: Guides probabilistic methods (e.g., Expected Improvement in Bayesian Optimization).
- **Termination Criteria**: Stopping conditions (e.g., `max_iter`, tolerance threshold).

#### **4.2 Trade-offs**
| **Approach**          | **Pros**                          | **Cons**                          | **When to Use**                  |
|-----------------------|-----------------------------------|-----------------------------------|-----------------------------------|
| **Grid Search**       | Exhaustive; guarantees optimality  | Slow for high-dimensional spaces   | Small, discrete spaces            |
| **Bayesian Optimization** | Efficient for expensive objectives | Requires surrogate modeling       | Black-box functions (e.g., API calls) |
| **SGD/Adam**          | Fast convergence; scales well     | Needs manual tuning               | Large datasets                    |
| **Genetic Algorithms** | Handles non-convex spaces         | Slow; stochastic results           | NP-hard problems                  |

#### **4.3 Frameworks & Libraries**
| **Tool**              | **Optimization Approaches**               | **Best For**                          |
|-----------------------|--------------------------------------------|---------------------------------------|
| **Scikit-Learn**      | GridSearchCV, RandomizedSearchCV          | Classic ML hyperparameter tuning      |
| **Hyperopt**          | Bayesian Optimization                     | Expensive objectives                  |
| **Optuna**           | TPE, CMA-ES, Random Search                | Hyperparameter optimization (ML/RL)   |
| **TensorFlow/Keras**  | Keras Tuner (Bayesian, Hyperband)         | Neural network architecture search    |
| **Kubernetes**       | HPA, Vertical Pod Autoscaler              | Cloud infrastructure optimization     |

---

### **5. Related Patterns**
1. **[Adaptive Learning Rates](link-to-pattern)**
   - Complements gradient-based optimization with dynamic `α` updates (e.g., Adam, RMSprop).
2. **[A/B Testing](link-to-pattern)**
   - Uses statistical significance to validate optimization gains in production.
3. **[Caching](link-to-pattern)**
   - Reduces recomputation cost in iterative optimization loops (e.g., memoization in Bayesian methods).
4. **[Resource Quotas](link-to-pattern)**
   - Constrains optimization budgets (e.g., Kubernetes `ResourceQuota` for HPA limits).
5. **[Distributed Training](link-to-pattern)**
   - Parallelizes optimization (e.g., Horovod for SGD across GPUs).

---
### **6. Key Considerations**
- **Dimensionality**: High-dimensional spaces (e.g., >10 hyperparameters) favor **Bayesian methods** or **AutoML**.
- **Noise**: For noisy objectives (e.g., online systems), use **robust algorithms** like TPE (Optuna) or **ensemble methods**.
- **Cost vs. Accuracy**: Trade off computational budget (e.g., `max_evals` in Hyperopt) against precision.
- **Reproducibility**: Set random seeds (e.g., `random_state` in Scikit-Learn) or deterministic samplers (e.g., `shuffle=False` in Optuna).

---
### **7. Example Workflow: Optimizing a CNN in Keras Tuner**
```python
import keras_tuner as kt

def build_model(hp):
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Conv2D(
        filters=hp.Int('conv1_filters', min_value=32, max_value=256, step=32),
        kernel_size=(3, 3),
        activation='relu',
        input_shape=(28, 28, 1)
    ))
    model.add(tf.keras.layers.MaxPooling2D((2, 2)))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(
        units=hp.Int('dense_units', min_value=32, max_value=256, step=32),
        activation='relu'
    ))
    model.add(tf.keras.layers.Dense(10, activation='softmax'))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            hp.Choice('learning_rate', [1e-2, 1e-3, 1e-4])
        ),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

tuner = kt.BayesianOptimization(
    build_model,
    objective='val_accuracy',
    max_trials=20,
    directory='keras_tuner_logs',
    project_name='mnist'
)
tuner.search(X_train, y_train, epochs=10, validation_data=(X_val, y_val))
best_model = tuner.get_best_models(num_models=1)[0]
```

---
**Note**: For production, validate optimized models with **cross-validation** or **holdout sets** to avoid overfitting to the search process.