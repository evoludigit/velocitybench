# **[Pattern] Hybrid Optimization Reference Guide**

---

## **1. Overview**
Hybrid Optimization is a design pattern that combines **deterministic (exact) and stochastic (approximate) optimization techniques** to solve complex problems where neither method alone achieves optimal performance. This approach leverages:
- **Deterministic solvers** (e.g., Linear Programming, Mixed-Integer Programming) for structured, low-dimensional subproblems.
- **Stochastic methods** (e.g., Genetic Algorithms, Simulated Annealing, Reinforcement Learning) for high-dimensional, noisy, or dynamic environments.
- **Metaheuristics** (e.g., Tabu Search, Ant Colony Optimization) to explore global optima efficiently.
- **Hybridized OR-tools** (e.g., Google OR-Tools + TensorFlow) for integrating solvers with machine learning.

Common use cases include:
- **Supply Chain Optimization** (demand forecasting + route planning).
- **Resource Allocation** (budget constraints + uncertainty modeling).
- **Autonomous Systems** (path planning + reinforcement learning).
- **FinTech** (portfolio optimization + Monte Carlo simulations).

The pattern balances **solution quality** (via deterministic guarantees) and **computational efficiency** (via stochastic search).

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**               | **Description**                                                                                                                                                                                                 | **Example Tools/Libraries**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| **Deterministic Solver**    | Solves constrained subproblems exactly (e.g., linear/MIP).                                                                                                                                                   | [PuLP](https://pypi.org/project/PuLP/), [Gurobi](https://www.gurobi.com/), [CVXPY](https://www.cvxpy.org/) |
| **Stochastic Optimizer**    | Explores solution space probabilistically for global optima.                                                                                                                                                 | [DEAP](https://deap.readthedocs.io/), [PySwarms](https://pyswarm.readthedocs.io/), [TensorFlow Probability](https://www.tensorflow.org/probability) |
| **Hybrid Interface**        | Orchestrates communication between solvers (e.g., solves MIP relaxations, then refines with GA).                                                                                                         | Custom wrappers, [Pyomo](https://www.pyomo.org/), [OR-Tools](https://developers.google.com/optimization) |
| **Evaluation Metric**        | Defines success (e.g., objective function value, runtime, feasibility).                                                                                                                                     | Custom scripts or [Metis](https://github.com/facebookresearch/metis) (for multi-objective) |
| **Fallback Mechanism**      | Switches to deterministic mode if stochastic results degrade (e.g., timeout, infeasibility).                                                                                                                  | Early-stopping logic, [Ray Tune](https://docs.ray.io/en/latest/tune/index.html) for A/B testing |

---

### **2.2 Hybridization Strategies**
| **Strategy**                | **When to Use**                                                                                                                                                                                                 | **Pros**                                                                                     | **Cons**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Deterministic First**     | Low-dimensional, structured problems (e.g., knapsack + local search).                                                                                                                                       | Guaranteed feasibility for subproblems.                                                      | Stochastic phase may get stuck in local optima.                                             |
| **Stochastic First**        | High-dimensional, noisy problems (e.g., hyperparameter tuning).                                                                                                                                             | Better global exploration.                                                                   | Computationally expensive; no feasibility guarantees.                                      |
| **Cooperative Hybrid**      | Dynamic environments (e.g., reinforcement learning + MPC).                                                                                                                                                 | Adapts to changes; combines strengths of both methods.                                      | Complex coordination required.                                                              |
| **Sequential**              | Multi-stage problems (e.g., train a surrogate model, then optimize with MIP).                                                                                                                                 | Reduces search space for deterministic solver.                                               | Latency between stages may hurt real-time systems.                                           |
| **Parallel**                | Distributed optimization (e.g., federated learning + global MIP).                                                                                                                                          | Scales horizontally.                                                                         | Communication overhead.                                                                      |
| **Metaheuristic-Guided**    | Combinatorial optimization (e.g., traveling salesman + genetic algorithm).                                                                                                                                | Avoids poor MIP relaxations.                                                                | May fail for NP-hard problems without proper tuning.                                        |

---

### **2.3 Hybrid Workflow Example**
1. **Preprocessing**:
   - Use a **stochastic method** (e.g., Monte Carlo) to sample constraints/parameters.
   - Generate a **deterministic relaxation** (e.g., LP/MIP) of the problem.
2. **Deterministic Phase**:
   - Solve the relaxed problem **exactly** (e.g., with Gurobi).
   - Extract **feasible solutions** or bounds for the stochastic phase.
3. **Stochastic Refinement**:
   - Run a **genetic algorithm** to perturb solutions near the deterministic optimum.
   - Apply **local search** (e.g., hill climbing) to refine candidates.
4. **Postprocessing**:
   - Validate solutions against original constraints.
   - Fall back to deterministic mode if stochastic results violate feasibility.

---
## **3. Schema Reference**
Below is a **simplified schema** for a hybrid optimization pipeline in Python (adaptable to other languages).

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                                                                 |
|-------------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `problem`               | `dict`         | Problem definition (objective, constraints, variables).                                                                                                                                                     | `{"type": "MIP", "objective": "maximize profit", "constraints": {"capacity": 100}}` |
| `deterministic_solver`  | `str`          | Solver backend (e.g., `"Gurobi"`, `"PuLP"`).                                                                                                                                                               | `"Gurobi"`                                                                          |
| `stochastic_method`     | `str`          | Optimization heuristic (e.g., `"GA"`, `"SA"`, `"RL"`).                                                                                                                                                     | `"DEAP_GA"`                                                                          |
| `population_size`       | `int`          | Number of stochastic candidates per iteration.                                                                                                                                                            | `100`                                                                               |
| `max_iterations`        | `int`          | Maximum iterations for stochastic phase.                                                                                                                                                                     | `50`                                                                                 |
| `fallback_threshold`    | `float`        | Feasibility score threshold to trigger deterministic fallback.                                                                                                                                    | `0.95` (95% feasibility)                                                            |
| `output_format`         | `str`          | Output format (e.g., `"CSV"`, `"JSON"`, `"Parquet"`).                                                                                                                                                         | `"JSON"`                                                                            |
| `logging`               | `dict`         | Debugging/logging configuration.                                                                                                                                                                       | `{"level": "INFO", "file": "hybrid.log"}`                                           |

---
## **4. Query Examples**
### **4.1 Basic Hybrid Optimization (Python + PuLP + DEAP)**
```python
import pulp
from deap import base, creator, tools, algorithms

# 1. Define deterministic problem (PuLP)
prob = pulp.LpProblem("Knapsack", pulp.LP_MAXIMIZE)
items = [("A", 5, 10), ("B", 3, 15), ("C", 2, 20)]  # (name, weight, value)
x = {n: pulp.LpVariable(n, cat="Integer") for n, _, _ in items}
prob += pulp.lpSum(x[n] * v for n, _, v in items), "Profit"
prob += pulp.lpSum(x[n] * w for n, w, _ in items) <= 10, "Capacity"
status = prob.solve()
optimal_solution = {n: pulp.value(v) for n, v in x.items()}

# 2. Stochastic refinement (DEAP)
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

def evaluate(individual):
    # Perturb the deterministic solution
    perturbed = {n: int(round(v + 0.1 * (0.2 - 0.1 * np.random.rand())))
                 for n, v in optimal_solution.items()}
    # Re-solve with adjusted weights
    temp_prob = pulp.LpProblem("Perturbed", pulp.LP_MAXIMIZE)
    temp_x = {n: pulp.LpVariable(n, cat="Integer") for n in perturbed}
    temp_prob += sum(temp_x[n] * v * (1 + 0.1 * np.random.rand())
                    for n, _, v in items), "Profit"
    temp_prob += sum(temp_x[n] * w for n, w, _ in items) <= 10, "Capacity"
    temp_prob.solve()
    return (pulp.value(temp_prob.objective),)

toolbox = base.Toolbox()
toolbox.register("attr_int", lambda: random.randint(0, 2))
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_int, n=len(items))
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("mate", tools.cxBlend, alpha=0.5)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate)

population = toolbox.population(n=50)
algorithms.eaSimple(population, toolbox, cxpb=0.5, mutpb=0.2, ngen=20, verbose=True)
best_individual = tools.selBest(population, k=1)[0]
print("Best solution:", dict(zip(items, best_individual)))
```

---
### **4.2 Hybrid Optimization with OR-Tools (Reinforcement Learning + MIP)**
```python
from ortools.linear_solver import pywraplp
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# 1. Define MIP model (OR-Tools)
solver = pywraplp.Solver.CreateSolver('SCIP')
x = [solver.IntVar(0, 10, f'x_{i}') for i in range(3)]
solver.Add(sum(x) <= 10)
solver.Maximize(3*x[0] + 2*x[1] + x[2])
status = solver.Solve()
mip_solution = [x[i].solution_value() for x in x]

# 2. Train a surrogate model to predict perturbations
model = Sequential([
    Dense(64, activation='relu', input_shape=(3,)),
    Dense(1, activation='linear')
])
model.compile(optimizer='adam', loss='mse')

# Generate synthetic training data (perturbed MIP solutions)
X_train = np.random.uniform(0, 10, (1000, 3))
y_train = np.array([sum(x) for x in X_train])  # Example: minimize sum(x)

model.fit(X_train, y_train, epochs=10)

# 3. Use RL to explore perturbations
import tensorflow as tf
env = custom_env()  # Assume this wraps the MIP problem
policy = tf.keras.models.Sequential([...])  # Your RL agent
for _ in range(1000):
    state = env.reset()
    while not env.done():
        action = policy.predict(state[np.newaxis])
        next_state, reward, done = env.step(action)
        state = next_state
```

---
### **4.3 Cloud-Native Hybrid Optimization (Ray + TensorFlow)**
```python
import ray
from ray import tune
from ray.tune.schedulers import ASHAScheduler

@ray.remote
def hybrid_optimize(config):
    # Deterministic phase (Gurobi)
    prob = create_gurobi_model(config["constraints"])
    solver = prob.solve()

    # Stochastic phase (TensorFlow)
    def objective(x):
        return tf.reduce_mean(tf.keras.backend.function(
            input_tensor=x, output_tensor=compute_objective(x))(x))

    optimizer = tf.optimizers.Adam(learning_rate=config["lr"])
    x = tf.Variable(tf.random.uniform([config["dim"]]))
    for _ in range(config["epochs"]):
        with tf.GradientTape() as tape:
            loss = -objective(x)
        grad = tape.gradient(loss, x)
        optimizer.apply_gradients([(grad, x)])
    return float(x.numpy())

# Distributed tuning
ray.init()
analysis = tune.run(
    hybrid_optimize,
    config={
        "constraints": tune.choice([{"type": "LP", "dim": 10}, {"type": "MIP", "dim": 20}]),
        "lr": tune.loguniform(1e-4, 1e-2),
        "epochs": tune.choice([10, 50]),
    },
    scheduler=ASHAScheduler(metric="loss", mode="min"),
    num_samples=20,
)
print(analysis.best_config)
```

---
## **5. Query Examples: Solver-Specific**
### **5.1 Hybrid Optimization with Gurobi + Genetic Algorithm**
```python
import gurobipy as gp
from pymoo.algorithms.soo.nonconvex.ga import GA

# 1. Gurobi for deterministic relaxation
m = gp.Model("hybrid")
x = m.addMVar(3, lb=0, ub=10, vtype=gp.GRB_CONTINUOUS)
m.setObjective(x[0] + 2*x[1] + 3*x[2], gp.GRB.MAXIMIZE)
m.addConstr(x[0] + x[1] + x[2] <= 10)
m.optimize()
deterministic_solution = tuple(x.x)

# 2. Genetic Algorithm for stochastic refinement
problem = {
    "x": deterministic_solution,
    "fitness": lambda x: evaluate(x)  # Your custom fitness function
}
algorithm = GA(pop_size=50)
result = algorithm.run(problem)
print("Best GA solution:", result.F)
```

---
### **5.2 Hybrid Optimization with CBQP (Convex Quadratic Programming) + Particle Swarm**
```python
from cvxpy import Variable, Problem, QuadForm
from pyswarm import pso

# 1. Convex QP (CVXPY)
x = Variable(3)
objective = QuadForm([0.5, -0.5, 0], [0.5, -0.5, 0], x)
constraints = [x[0] + x[1] + x[2] <= 10, x >= 0]
prob = Problem(Minimize(objective), constraints)
prob.solve()
qp_solution = x.value

# 2. Particle Swarm Optimization (PySwarms)
def f(x):
    return 0.5 * (x[0] - x[1])**2 + (x[0] - x[2])**2 + (x[1] - x[2])**2  # Example objective

bounds = [(0, 10), (0, 10), (0, 10)]
x_opt, _ = pso(f, bounds, swarmsize=20, maxiter=100)
print("PSO solution:", x_opt)
```

---

## **6. Related Patterns**
| **Pattern**                  | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Deterministic Solving]**   | Solves problems exactly using techniques like linear programming, mixed-integer programming, or network flows.                                                                                        | Problems with small/structured dimensions and known constraints.                                     |
| **[Stochastic Search]**       | Explores solution spaces using probabilistic methods (e.g., genetic algorithms, simulated annealing, reinforcement learning).                                                                             | High-dimensional, noisy, or dynamic problems where exact solutions are intractable.                |
| **[Greedy Algorithms]**       | Makes locally optimal choices iteratively to solve optimization problems.                                                                                                                                | Problems with clear greedy heuristics (e.g., Huffman coding, Dijkstra’s shortest path).          |
| **[Approximation Algorithms]**| Provides near-optimal solutions for NP-hard problems with provable bounds (e.g., 2-approximation for knapsack).                                                                                       | When exact solutions are unnecessary, and worst-case guarantees are needed.                        |
| **[Divide and Conquer]**      | Breaks problems into smaller subproblems, solves them recursively, and combines results.                                                                                                              | Problems with optimal substructure (e.g., merge sort, dynamic programming).                         |
| **[Metaheuristics]**         | High-level strategies (e.g., Tabu Search, Ant Colony Optimization) to guide local search.                                                                                                                 | Problems with many local optima or complex fitness landscapes.                                      |
| **[Reinforcement Learning]**  | Optimizes decision-making via trial-and-error interaction with an environment.                                                                                                                       | Sequential decision problems (e.g., robotics, game AI, resource allocation).                      |
| **[Federated Optimization]**  | Distributed optimization across decentralized agents (e.g., federated learning + MIP).                                                                                                               | Large-scale, privacy-sensitive problems (e.g., healthcare, IoT).                                    |
| **[Surrogate Modeling]**      | Uses machine learning to approximate expensive-to-evaluate objective functions (e.g., Gaussian Processes, Neural Networks).                                                                              | Problems with black-box objectives (e.g., CFD simulations, quantum chemistry).                     |
| **[Constraint Programming]**  | Models and solves problems with constraints using backtracking (e.g., Choco, IBM CPLEX).                                                                                                               | Discrete, combinatorial problems (e.g., scheduling, routing).                                       |

---

## **7. Best Practices**
1. **Problem Decomposition**:
   - Use deterministic solvers for **low-dimensional, structured** subproblems.
   - Reserve stochastic methods for **high-dimensional, uncertain** components.
2. **Hybrid Interface Design**:
   - Standardize input/output formats (e.g., JSON, Parquet) between solvers.
   - Use **message brokers** (e.g., Kafka, Ray) for distributed coordination.
3. **Fallback Mechanisms**:
   - Monitor **feasibility** and **objective value** to detect stochastic failure.
