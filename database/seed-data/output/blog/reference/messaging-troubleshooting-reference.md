**[Pattern] Messaging Troubleshooting Reference Guide**

---

### **Overview**
Messaging systems are critical for distributed applications, enabling communication between services, components, and external systems. However, issues like **delivery failures, latency spikes, duplicate messages, or connection drops** can disrupt operations. This guide provides a structured troubleshooting framework to diagnose, log, and resolve common messaging system problems. It covers **protocol-specific checks (e.g., HTTP, gRPC, Kafka), infrastructure issues (e.g., network, brokers), and application-layer problems (e.g., retries, circuit breakers)**. Use this as a diagnostic workflow when messages fail to reach their destination or behave unexpectedly.

---

### **Key Concepts & Implementation Details**
Messaging systems rely on **producers, consumers, brokers/intermediaries, and transport protocols**. Below are foundational components to troubleshoot:

| **Concept**               | **Description**                                                                 | **Troubleshooting Focus**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Producer**              | System/service that sends messages.                                            | Check payload formatting, authentication, rate limits, and connection health.            |
| **Consumer**              | System/service that receives and processes messages.                          | Validate error handling, backpressure mechanisms, and dependency issues.                  |
| **Broker/Intermediary**   | Middleware (e.g., Kafka, RabbitMQ, AWS SQS) that routes messages.              | Monitor broker health (CPU, memory, disk), partitions, and topic/subscription configs.   |
| **Transport Protocol**    | Underlying mechanism (e.g., TCP, HTTP, MQTT) for message exchange.              | Test network connectivity, protocol timeouts, and encryption.                            |
| **Message Flow**          | End-to-end sequence from send to receive (e.g., publish → broker → consume).     | Trace flow using logging, timestamps, and correlation IDs.                               |
| **Delivery Guarantees**   | Features like **at-least-once**, **exactly-once**, or **fire-and-forget** delivery. | Audit retries, idempotency, and deduplication logic.                                     |
| **Tracking/Observability**| Metrics, logs, and traces to monitor message lifecycle.                       | Check tools like Prometheus, Jaeger, or broker-specific dashboards.                    |

---

### **Troubleshooting Schema**
Below is a **decision-tree schema** to prioritize investigations. Start at the **top of the flow** (Producer → Broker → Consumer) and drill down based on symptoms.

```plaintext
┌───────────────────────┐
│ **Symptom**           │
└───────────────────────┘
            │
            ▼
┌───────────────────────┐
│ **Is the producer    │
│ sending messages?**   │
└───────────────────────┘
            │
            ├─ **No**
            │   └─ Check: Connection, auth, payload validation, circuit breakers.
            │
            └─ **Yes**
                │
                ▼
┌───────────────────────┐
│ **Are messages      │
│ reaching the broker?**│
└───────────────────────┘
            │
            ├─ **No**
            │   └─ Check: Firewall rules, network latency, broker endpoints, quotas.
            │
            └─ **Yes**
                │
                ▼
┌───────────────────────┐
│ **Are messages       │
│ being consumed?**     │
└───────────────────────┘
            │
            ├─ **No**
            │   └─ Check: Consumer health, subscription configs, backpressure.
            │
            └─ **Yes (but delayed/failed)**
                │
                ▼
┌───────────────────────┐
│ **Presumed Cause**    │
└───────────────────────┘
            │
            ├─ **Duplicate messages**
            │   └─ Investigate: Idempotency, dedupe keys, retry logic.
            │
            ├─ **Message corruption**
            │   └─ Check: Serialization (e.g., Protobuf, JSON), TLS integrity.
            │
            └─ **Broker overload**
                └─ Monitor: Queue lengths, partition leaders, garbage collection.
```

---

### **Query Examples**
Use these **CLI/command-line queries** and **tool-based checks** to debug issues. Adjust syntax for your broker (e.g., Kafka, RabbitMQ).

#### **1. Broker Health Checks**
| **Tool/Command**               | **Purpose**                                  | **Example**                                                                 |
|---------------------------------|---------------------------------------------|-----------------------------------------------------------------------------|
| **Kafka `kafka-broker-api-versions`** | Verify broker API compatibility.         | `kafka-broker-api-versions.sh --bootstrap-server <BROKER:PORT>`            |
| **RabbitMQ `rabbitmqctl status`** | Check cluster/memory/node stats.          | `rabbitmqctl status` (local) or SSH into node.                              |
| **AWS SQS `GetQueueAttributes`** | Inspect queue metrics (ApproximateAgeOfOldestMessage). | ```bash<br>aws sqs get-queue-attributes --queue-url <URL> --attribute-names All<br>``` |
| **Prometheus Query**            | Alert on high message lag.                 | `rate(kafka_consumer_lag_sum[5m]) > 1000`                                   |

#### **2. Message Flow Tracing**
| **Tool/Command**               | **Purpose**                                  | **Example**                                                                 |
|---------------------------------|---------------------------------------------|-----------------------------------------------------------------------------|
| **Kafka `kafka-console-consumer`** | Peek at messages in a topic.          | `kafka-console-consumer --topic <TOPIC> --bootstrap-server <BROKER> --from-beginning` |
| **gRPC `grpc_cli`**             | Inspect gRPC stream state.                | `grpc_cli listen <HOST:PORT>` or `grpc_cli call <SERVICE>.<METHOD>`         |
| **OpenTelemetry Traces**        | Correlate messages across services.       | Filter traces by `span.kind=producer` or `span.kind=consumer`.             |
| **ELK Stack (Elasticsearch)**   | Search logs for message IDs/correlation IDs. | ```json<br>"query": {<br>  "match": { "message.id": "<ID>" }<br>}<br>```     |

#### **3. Consumer-Side Diagnostics**
| **Tool/Command**               | **Purpose**                                  | **Example**                                                                 |
|---------------------------------|---------------------------------------------|-----------------------------------------------------------------------------|
| **Consumer Group Lag**          | Compare committed offsets vs. latest offset. | Kafka: `kafka-consumer-groups --describe --group <GROUP>`                   |
| **RabbitMQ `rabbitmqctl list_queues`** | Check queue depth/backlog.       | ```bash<br>rabbitmqctl list_queues name messages_ready messages_unacknowledged<br>``` |
| **Java `FlightRecorder`**       | Profile consumer JVM issues.                | Attach to JVM: `jcmd <PID> JFR.start name=consumer_profile settings=profile` |

#### **4. Producer-Side Diagnostics**
| **Tool/Command**               | **Purpose**                                  | **Example**                                                                 |
|---------------------------------|---------------------------------------------|-----------------------------------------------------------------------------|
| **HTTP Status Codes**           | Validate API responses.                     | `curl -v -X POST <ENDPOINT>` (check `HTTP 5xx` or timeouts).                  |
| **gRPC Error Codes**            | Decode gRPC status.                         | ```bash<br>grpcurl -plaintext <HOST:PORT> <SERVICE>.<METHOD> 2>/dev/null | jq<br>``` |
| **Rate Limiting Checks**        | Test against quotas.                        | Simulate load: `ab -n 1000 -c 100 <ENDPOINT>` (ApacheBench).                |

---

### **Common Issues & Mitigations**
| **Issue**                          | **Root Cause**                              | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------|------------------------------------------------------------------------------|
| **Messages not delivered**          | Broker offline, ACL misconfig, or quota     | Verify broker health; adjust `permissions` or `resource-limit`.              |
| **High latency**                    | Backpressure, slow consumer, or network     | Scale consumers; optimize serialization (e.g., Protobuf > JSON).            |
| **Duplicate messages**              | At-least-once delivery + retries          | Implement idempotent consumers (e.g., deduplicate by `message_id`).         |
| **Consumer crashes**                | Unhandled exceptions in handler           | Add dead-letter queues (DLQ) for failed messages.                           |
| **Broker partition rebalancing**   | Leader election during high load          | Monitor `kafka-consumer-groups --describe`; adjust `partition.count`.       |
| **TLS handshake failures**          | Certificate expiry or CA mismatch          | Update certs or trust stores; use `openssl s_client` to debug.               |

---

### **Related Patterns**
To complement messaging troubleshooting, refer to these patterns for broader observability and resilience:

| **Pattern Name**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Circuit Breaker]**           | Prevent cascading failures by halting requests to failing services.            | When consumers rely on unstable downstream services.                           |
| **[Retry with Backoff]**        | Handle transient errors with exponential retry logic.                          | For idempotent producers (e.g., Kafka producers).                               |
| **[Distributed Tracing]**       | Trace requests across microservices via correlation IDs.                       | Debug cross-service message flows (e.g., gRPC → Kafka → REST).                 |
| **[Dead Letter Queue]**         | Route failed messages to a queue for manual review.                            | When messages cannot be automatically reprocessed.                             |
| **[Rate Limiting]**             | Throttle producers/consumers to avoid broker overload.                         | During peak traffic or Denial-of-Service risk.                                |
| **[Idempotent Producer]**       | Ensure duplicate messages don’t cause side effects.                           | For eventual consistency or retry-heavy systems.                              |

---

### **Next Steps**
1. **Instrumentation**: Add correlation IDs to messages for end-to-end tracing.
2. **Alerting**: Set up proactively (e.g., Prometheus alerts for `kafka_consumer_lag` > 1000).
3. **Testing**: Simulate failures (e.g., kill brokers) with tools like **Chaos Mesh** or **Gremlin**.
4. **Documentation**: Archive known issues (e.g., "High CPU causes partition rebalancing").