---
# **[Pattern] Parallel Processing Reference Guide**
*Maximize efficiency by concurrently executing tasks using threads, processes, or distributed resources.*

---

## **Overview**
The **Parallel Processing** pattern leverages concurrent execution to distribute workloads across multiple threads, processes, or machines. By dividing tasks into smaller units, this pattern reduces processing time, improves throughput, and optimizes resource utilization. It is widely applied in CPU-bound tasks (e.g., data processing, simulations) and I/O-bound workloads (e.g., web scraping, batch jobs).

Key considerations include:
- **Thread vs. Process Choice**: Threads share memory (faster IPC) but are limited by the Global Interpreter Lock (GIL) in Python. Processes run independently (better isolation) but incur higher overhead.
- **Granularity**: Coarse-grained tasks (e.g., batch jobs) benefit from fewer processes; fine-grained tasks (e.g., real-time analytics) may need threads.
- **Synchronization**: Avoid race conditions with locks, semaphores, or message queues.
- **Scalability**: Horizontal scaling (distributed tasks) requires frameworks like Dask or Apache Spark for large-scale deployments.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                     | **Use Case Examples**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Task Granularity**        | Size of individual units (e.g., single operation vs. entire file).                                 | *Fine*: Per-row data processing; *Coarse*: Parallelizing AI model training phases.                           |
| **Concurrency Model**       | Thread Pool, Process Pool, Async I/O, or Distributed Systems.                                       | Thread Pool for CPU-heavy tasks; Async I/O for I/O-bound APIs.                                             |
| **Data Partitioning**       | Splitting input data (e.g., vertical slices, fixed-size chunks).                                   | Sharding database queries or splitting video frames for edge detection.                                   |
| **Synchronization Primitive** | Locks, Barriers, or Queue-based (e.g., `multiprocessing.Queue` in Python).                        | Locks for shared memory; Barriers for phased parallelism (e.g., matrix multiplication).                    |
| **Load Balancing**          | Dynamic task assignment (e.g., round-robin, work-stealing).                                        | Distributed task queues in Hadoop or Kubernetes pods.                                                    |
| **Fault Tolerance**         | Retries, checkpoints, or redundant tasks (e.g., MapReduce).                                        | Reprocessing failed batch jobs or replicating critical pipelines.                                         |
| **Dependency Management**   | Chaining tasks (e.g., DAGs in Airflow) or event-based triggers.                                    | Pipeline: ETL → ML → Visualization.                                                                    |
| **Monitoring**              | Metrics (latency, throughput), logging, and resource tracking.                                     | Prometheus for thread pool saturation; GCP Cloud Logging for distributed jobs.                           |

---

## **Implementation Details**

### **1. Thread-Based Parallelism**
**Use Case**: Lightweight tasks with shared memory (e.g., in-memory computations).
**Python Example** (Thread Pool):
```python
from concurrent.futures import ThreadPoolExecutor

def process_data(item):
    return f"Processed: {item}"

data = ["A", "B", "C"]
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_data, data))
# Output: ['Processed: A', 'Processed: B', 'Processed: C']
```
**Key Notes**:
- **Limitations**: GIL restricts true parallelism in Python. Use `multiprocessing` for CPU-bound tasks.
- **Overhead**: Thread creation is cheap but context-switching adds latency.

---

### **2. Process-Based Parallelism**
**Use Case**: CPU-intensive tasks (e.g., numerical simulations).
**Python Example** (Process Pool):
```python
from multiprocessing import Pool

def compute_square(n):
    return n * n

with Pool(4) as p:  # 4 processes
    results = p.map(compute_square, [1, 2, 3, 4])
# Output: [1, 4, 9, 16]
```
**Key Notes**:
- **Memory Isolation**: Each process has its own memory space (no GIL).
- **Inter-Process Communication (IPC)**: Use `Queue`, `Pipe`, or shared memory (e.g., `multiprocessing.shared_memory`).

---

### **3. Async I/O**
**Use Case**: High-latency operations (e.g., HTTP requests, DB queries).
**Python Example** (Async/Await):
```python
import asyncio

async def fetch_data(url):
    return f"Data from {url}"

async def main():
    urls = ["url1", "url2"]
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
# Output: ["Data from url1", "Data from url2"]
```
**Key Notes**:
- **Event Loop**: Single thread handles thousands of I/O tasks non-blockingly.
- **Libraries**: `aiohttp`, `asyncpg` for async HTTP/DB operations.

---

### **4. Distributed Parallelism**
**Use Case**: Large-scale data processing (e.g., >100GB datasets).
**Tools**:
- **PySpark**: Cluster-based parallelism (RDDs/DataFrames).
  ```python
  from pyspark.sql import SparkSession
  spark = SparkSession.builder.appName("Parallel").getOrCreate()
  df = spark.read.csv("data.csv").repartition(4)  # Parallelize reads
  ```
- **Dask**: Scalable Python (pandas/SciPy-like APIs).
  ```python
  import dask.dataframe as dd
  ddf = dd.read_csv("large.csv")  # Lazy evaluation
  result = ddf.groupby("col").mean().compute()  # Executes in parallel
  ```

**Key Notes**:
- **Cluster Management**: Requires orchestration (e.g., YARN, Kubernetes).
- **Fault Tolerance**: Spark/Dask handle node failures via replication.

---

## **Query Examples**

### **Thread Pool Optimization**
```python
# Batch processing with ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor, as_completed

def expensive_operation(x):
    time.sleep(2)  # Simulate I/O
    return x * x

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(expensive_operation, i) for i in range(10)]
    for future in as_completed(futures):
        print(future.result())  # Output: 0, 1, 4, 9, ..., 81
```

### **Process Pool with Shared Data**
```python
from multiprocessing import Pool, Manager

def update_dict(d, key, val):
    d[key] = val

if __name__ == "__main__":
    with Manager() as manager:
        shared_dict = manager.dict()
        with Pool(3) as p:
            p.starmap(update_dict, [(shared_dict, "a", 1), (shared_dict, "b", 2)])
        print(shared_dict)  # Output: {'a': 1, 'b': 2}
```

### **Async I/O with Timeout**
```python
import asyncio

async def async_request(url):
    try:
        await asyncio.wait_for(fetch(url), timeout=5.0)  # 5-second timeout
    except asyncio.TimeoutError:
        return "Timeout"

async def main():
    tasks = [async_request(f"http://example{i}.com") for i in range(3)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

---

## **Best Practices**
| **Practice**               | **Guidance**                                                                                     |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| **Granularity**             | Keep tasks >100ms to amortize overhead; avoid >10ms (too much scheduling).                      |
| **Resource Limits**         | Cap threads/processes to avoid CPU throttling (e.g., `max_workers=CPU_count + 1`).               |
| **Memory**                  | Use processes for large datasets; threads for shared memory (e.g., NumPy arrays).               |
| **Error Handling**          | Isolate failures (e.g., retry failed tasks in a queue).                                         |
| **Monitoring**              | Track parallelism metrics (e.g., `psutil` for CPU/memory).                                     |
| **Testing**                 | Stress-test with synthetic loads (e.g., `locust` for I/O-bound systems).                        |

---

## **Anti-Patterns**
1. **Overhead Ignored**: Spawning too many threads/processes without profiling.
2. **Unbounded Queues**: Blocking workers with infinite task backlogs.
3. **Shared State**: Race conditions in threads (use locks or process isolation).
4. **Ignoring Dependencies**: Parallelizing independent tasks; chaining requires DAGs.
5. **Global State**: Avoid `global` variables in threads/processes (use `Manager` or IPC).

---

## **Related Patterns**
| **Pattern**                 | **Relationship**                                                                                 | **Example Use Case**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **[Pipeline](Pipeline_Pattern.md)** | Parallel Processing enables parallel stages in a Pipeline (e.g., Spark RDD transformations).  | ETL pipeline: Preprocess → Transform → Load.                                                              |
| **[Observer](Observer_Pattern.md)** | Distributed systems use Observers for event-driven parallelism (e.g., Kafka consumers).        | Real-time analytics: Parallel topic partitions processed by multiple consumers.                            |
| **[MapReduce](MapReduce_Pattern.md)** | Distributed parallelism for large-scale data processing.                                         | Word count on 1PB datasets across a cluster.                                                             |
| **[Event Sourcing](Event_Sourcing_Pattern.md)** | Parallel reprocessing of events (e.g., CQRS with event logs).                                   | Order processing: Parallel validation of orders from event streams.                                     |
| **[Bulkhead](Bulkhead_Pattern.md)** | Limits parallelism per component to prevent cascading failures.                                 | Microservices: Cap parallel API calls per instance to avoid overload.                                  |

---

## **Tools & Libraries**
| **Category**               | **Tools**                                                                                         | **Language/Ecosystem**                                                                                  |
|-----------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Threading**              | `concurrent.futures`, `threading`                                                                 | Python                                                                                                    |
| **Processes**              | `multiprocessing`, `joblib`                                                                       | Python                                                                                                    |
| **Async I/O**              | `asyncio`, `aiohttp`, `uvicorn`                                                                   | Python                                                                                                    |
| **Distributed**            | PySpark, Dask, Celery, Ray                                                                         | Python/Java/Scala                                                                                       |
| **Cluster Mgmt**           | Kubernetes, YARN, Mesos                                                                          | General                                                                                                   |
| **Load Testing**           | Locust, JMeter, Gatling                                                                            | General                                                                                                   |

---
**See Also**:
- [Python `concurrent.futures` Docs](https://docs.python.org/3/library/concurrent.futures.html)
- [Spark Parallel Programming Guide](https://spark.apache.org/docs/latest/programming-guide.html)
- [Ray for Distributed Python](https://docs.ray.io/en/latest/)