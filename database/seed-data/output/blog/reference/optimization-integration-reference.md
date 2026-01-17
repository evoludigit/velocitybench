**[Pattern] Optimization Integration – Reference Guide**

---

### **Overview**
The **Optimization Integration** pattern enables seamless integration of optimization algorithms (e.g., machine learning, linear programming, or metaheuristics) with business logic, data pipelines, and applications. This ensures real-time or batch-driven decision-making (e.g., resource allocation, scheduling, or cost minimization) is dynamically adjusted based on constraints, goals, and evolving data. The pattern facilitates modular design, where optimization models are decoupled from core business workflows but tightly coupled to triggers (e.g., API calls, scheduled jobs, or event-driven hooks). Key use cases include **supply chain optimization**, **ad revenue bidding**, **inventory forecasting**, and **financial portfolio management**.

---

### **Key Concepts**
| Concept                     | Description                                                                                                                                                                                                                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Optimization Model**      | A mathematical definition of the problem (objective function + constraints) solved by an algorithm (e.g., linear programming, genetic algorithms). Models are stored as reusable assets (e.g., JSON/YAML configs or Python scripts).           |
| **Trigger Mechanism**       | Defines when optimization is invoked: **API-based** (real-time), **scheduler** (periodic), or **event-driven** (e.g., database trigger).                                                                                                           |
| **Data Pipeline**           | Ensures optimization algorithms receive clean, preprocessed data (e.g., feature engineering, normalization). Integrates with data lakes, databases, or Kafka streams.                                                                              |
| **Result Handler**          | Processes optimization outputs (e.g., parsed JSON, updated DB records, or generated reports). Includes validation and fallback logic for invalid solutions.                                                                                            |
| **Constraint Registry**     | Centralized rules (e.g., "capacity < 80%") enforced during optimization. Supports dynamic updates and versioning.                                                                                                                              |
| **Performance Monitor**     | Tracks metrics like runtime, solution quality, and algorithm convergence. Logs are used for tuning and alerting (e.g., failed optimizations or degraded performance).                                                                         |

---

### **Schema Reference**
#### **1. Optimization Model Schema**
```json
{
  "model": {
    "name": "string"                          // Unique identifier (e.g., "warehouse_allocation").
    "type": "enum: [LP, MIP, Heuristic]",     // Problem type.
    "objective": {
      "function": "string",                   // e.g., "maximize_profit".
      "parameters": [                              // Variables (e.g., "demand", "cost").
        {"name": "string", "data_source": "string"}
      ]
    },
    "constraints": [                             // Hard/soft rules.
      {
        "type": "enum: [hard, soft]",
        "condition": "string",                   // e.g., "total_weight <= 5000kg".
        "priority": "number"                     // Soft constraint weight (0–1).
      }
    ],
    "algorithm": {
      "name": "string",                         // e.g., "Gurobi", "SimulatedAnnealing".
      "config": "object"                        // Algorithm-specific settings (e.g., {"max_iter": 1000}).
    },
    "data_sources": [                            // Input data references.
      {"name": "string", "schema": "string"}    // e.g., {"name": "customer_orders", "schema": "orders.parquet"}
    ]
  }
}
```

#### **2. Trigger Configuration Schema**
```json
{
  "trigger": {
    "type": "enum: [api, scheduler, event]",
    "metadata": {
      "api": {
        "endpoint": "string",                 // e.g., "/optimize/supply_chain".
        "method": "enum: [GET, POST]"
      },
      "scheduler": {
        "interval": "string",                 // e.g., "PT1H" (ISO 8601).
        "timezone": "string"
      },
      "event": {
        "source": "string",                   // e.g., "database:orders_inserted".
        "condition": "string"                 // e.g., "order_value > 10000".
      }
    }
  }
}
```

#### **3. Result Handler Schema**
```json
{
  "handler": {
    "type": "enum: [database, api, file, noop]",
    "config": {
      "database": {
        "table": "string",                    // Target table (e.g., "optimization_results").
        "columns": ["string"]                  // e.g., ["solution", "runtime_ms"].
      },
      "api": {
        "endpoint": "string",                 // e.g., "/update/shipping_routes".
        "payload_mapping": "object"           // { "new_route": "solution.routes[0].id" }.
      }
    },
    "fallback": {
      "strategy": "enum: [skip, use_default, alert]",  // Action if optimization fails.
      "threshold": "number"                      // e.g., 3 consecutive failures.
    }
  }
}
```

---

### **Implementation Steps**
1. **Define the Model**
   - Store the optimization problem in a config file (e.g., `models/supply_chain.json`).
   - Example:
     ```json
     {
       "model": {
         "name": "supply_chain",
         "type": "MIP",
         "objective": { "function": "minimize_total_cost", "parameters": [{"name": "transport_cost"}] },
         "constraints": [
           { "type": "hard", "condition": "inventory >= demand" }
         ]
       }
     }
     ```

2. **Integrate with Trigger**
   - **API Trigger**: Deploy an endpoint (e.g., `/optimize`) to accept requests with payload:
     ```json
     { "constraints": { "max_weight": 5000 }, "demand": [120, 80] }
     ```
   - **Scheduler**: Use a cron job (e.g., `0 * * * *`) to poll the optimization service.

3. **Data Pipeline**
   - Preprocess data before passing to the optimizer. Example (Python):
     ```python
     def preprocess_data(raw_data):
         return {k: np.array(v) for k, v in raw_data.items()}
     ```

4. **Execute Optimization**
   - Invoke the algorithm (e.g., via a library like `ortools` or `Pyomo`):
     ```python
     from ortools.linear_solver import pywraplp

     solver = pywraplp.Solver.CreateSolver("SCIP")
     # Solve model...
     solution = solver.solution()
     ```

5. **Handle Results**
   - Parse and persist results. Example (database update):
     ```sql
     INSERT INTO optimization_results (model, solution, status)
     VALUES ('supply_chain', '{"routes": [...]}', 'SUCCESS');
     ```

6. **Monitor Performance**
   - Log metrics to a time-series DB (e.g., Prometheus) or analytics platform:
     ```json
     { "model": "supply_chain", "runtime_ms": 450, "status": "OPTIMAL" }
     ```

---

### **Query Examples**
#### **1. API Trigger (Real-Time)**
- **Request**:
  ```bash
  POST /optimize/supply_chain
  Content-Type: application/json

  {
    "demand": [120, 80],
    "constraints": { "max_weight": 5000 }
  }
  ```
- **Response**:
  ```json
  {
    "status": "SUCCESS",
    "solution": {
      "routes": [
        {"warehouse": "A", "quantity": 100},
        {"warehouse": "B", "quantity": 100}
      ],
      "total_cost": 4500
    }
  }
  ```

#### **2. Scheduled Optimization (Batch)**
- **Cron Job**:
  ```bash
  0 3 * * * python3 /opt/optimize/runs/daily_inventory.py
  ```
- **Script** (`runs/daily_inventory.py`):
  ```python
  from integration.optimizer import run_optimization

  run_optimization(
      model="inventory_forecast",
      data_source="s3://data/inventory.csv",
      handler="post_to_api"
  )
  ```

#### **3. Event-Driven (Database Trigger)**
- **Database Rule** (PostgreSQL):
  ```sql
  CREATE OR REPLACE FUNCTION optimize_order()
  RETURNS TRIGGER AS $$
  BEGIN
    IF NEW.order_value > 10000 THEN
      PERFORM osc.optimize_order(NEW.id);
    END IF;
    RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trigger_optimize_order
  AFTER INSERT ON orders
  FOR EACH ROW EXECUTE FUNCTION optimize_order();
  ```

---

### **Error Handling**
| Scenario                     | Action                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------|
| **Invalid Input Data**       | Return `400 Bad Request` with `errors: { "demand": "must be > 0" }`.                        |
| **Optimization Timeout**     | Log warning; fall back to cached solution or default values.                               |
| **Constraint Violation**     | Return `422 Unprocessable` with details (e.g., `constraints: [{"name": "weight", "violated": true}]`). |
| **Algorithm Failure**        | Retry once; alert if repeated (e.g., Slack notification).                                  |

---

### **Performance Considerations**
- **Cold Start Mitigation**: Use warm-up calls for scheduled triggers or lazy-load algorithms.
- **Model Versioning**: Tag models with versions to roll back if performance degrades.
- **Parallelization**: Distribute independent optimizations across workers (e.g., Kubernetes pods).

---

### **Related Patterns**
1. **Event-Driven Architecture (EDA)**
   - *How it connects*: Optimization triggers can be event-driven (e.g., Kafka topics for real-time updates).
   - *Reference*: [Event-Driven Architecture Pattern](link).

2. **Micro-Batch Processing**
   - *How it connects*: Scheduled optimizations can batch related requests (e.g., daily price optimization).
   - *Reference*: [Lambda Architecture](link).

3. **Feature Store**
   - *How it connects*: Centralized feature storage ensures optimization models use consistent, up-to-date inputs.
   - *Reference*: [Feature Store Pattern](link).

4. **Canary Deployments**
   - *How it connects*: Gradually roll out new optimization models to mitigate risk in production.
   - *Reference*: [Canary Release Pattern](link).

5. **Circuit Breaker**
   - *How it connects*: Prevent cascading failures if the optimization service degrades.
   - *Reference*: [Circuit Breaker Pattern](link).

---
**Last Updated**: [Date]
**Version**: 1.2