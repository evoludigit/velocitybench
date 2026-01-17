# **[Pattern] Service Discovery & Load Balancing Reference Guide**

---
## **1. Overview**
Service Discovery & Load Balancing is a critical pattern in microservices architectures that ensures resilient and efficient communication between distributed services. With multiple instances of a service dynamically scaling, clients need a way to discover healthy, reachable instances, while load balancers distribute incoming requests to prevent overload and improve performance.

This guide covers:
- **Service Discovery**: How clients dynamically locate service instances (e.g., via registries like Eureka, Consul, or Kubernetes Service Endpoints).
- **Load Balancing**: Algorithms for distributing client requests across available instances (e.g., round-robin, least connections, or client-side vs. server-side).

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**               | **Purpose**                                                                                     | **Examples**                          |
|-----------------------------|------------------------------------------------------------------------------------------------|---------------------------------------|
| **Service Registry**        | Centralized database tracking service instances (IP, port, health status).                     | Eureka, Consul, Zookeeper, Kubernetes Services |
| **Discovery Client**        | Library embedded in microservices to query the registry for available instances.               | Spring Cloud Netflix EurekaClient     |
| **Load Balancer**           | Mechanism to route requests to healthy instances (client-side or server-side).              | Nginx, HAProxy, AWS ALB, Ribbon, Netflix Ribbon |
| **Health Checks**           | Mechanism to monitor instance liveness/readiness (e.g., HTTP `/health` endpoints).           | Spring Actuator, Prometheus Probes    |

---

### **2.2 Service Discovery Workflow**
1. **Registration**: New service instances register their metadata (host, port, endpoints) with the registry.
2. **Discovery Query**: Clients query the registry to retrieve a list of active instances.
3. **Load Balancing**: Requests are distributed among healthy instances based on a chosen algorithm.

**Example Workflow**:
```
Client → [Load Balancer] → [Registry Query] → [Eureka/Consul] → [Health Checks] → [Service Instance]
```

---

### **2.3 Load Balancing Algorithms**
| **Algorithm**               | **Description**                                                                              | **Use Case**                          |
|-----------------------------|----------------------------------------------------------------------------------------------|---------------------------------------|
| **Round-Robin**             | Sequentially distributes requests (simple, default in many client libraries).              | Low-latency, stateless services       |
| **Least Connections**       | Routes requests to the instance with the fewest active connections.                       | CPU-intensive workloads              |
| **IP Hash**                 | Uses client IP to route requests to the same instance (consistency).                        | Session affinity                       |
| **Random**                  | Randomly selects an instance (avoids overloading one instance).                            | Stateless workloads                   |
| **Weighted Round-Robin**    | Assigns weights to instances (e.g., based on capacity).                                   | Multi-region or tiered services      |

---

## **3. Schema Reference**
Below are common data structures used in service discovery and load balancing.

### **3.1 Service Registry Schema (Example)**
```json
{
  "services": {
    "order-service": [
      {
        "id": "order-service-1",
        "host": "10.0.0.1",
        "port": 8080,
        "health": "UP",
        "metadata": {
          "zone": "us-west-1",
          "version": "v2.3"
        }
      },
      {
        "id": "order-service-2",
        "host": "10.0.0.2",
        "port": 8080,
        "health": "DOWN",
        "metadata": {}
      }
    ]
  }
}
```

### **3.2 Load Balancer Configuration (Example)**
```yaml
# Nginx Load Balancer Config (Round-Robin)
upstream order-service {
  least_conn;
  server 10.0.0.1:8080;
  server 10.0.0.3:8080;
}

server {
  location /orders/ {
    proxy_pass http://order-service;
  }
}
```

---

## **4. Query Examples**
### **4.1 Discovery Query (REST API)**
Fetch healthy instances of `order-service` from a registry:
```bash
GET http://consul-agent:8500/v1/catalog/service/order-service?passing
```
**Response**:
```json
[
  { "ServiceID": "order-service-1", "ServiceAddress": "10.0.0.1", "ServicePort": 8080 },
  { "ServiceID": "order-service-3", "ServiceAddress": "10.0.0.4", "ServicePort": 8080 }
]
```

### **4.2 Health Check (HTTP)**
```bash
GET http://order-service-1:8080/actuator/health
```
**Response (OK)**:
```json
{"status": "UP"}
```

---

## **5. Implementation Steps**
### **5.1 Client-Side Load Balancing (e.g., Spring Cloud)**
1. **Add Dependency**:
   ```xml
   <!-- For Eureka Discovery -->
   <dependency>
     <groupId>org.springframework.cloud</groupId>
     <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
   </dependency>
   ```
2. **Configure `application.yml`**:
   ```yaml
   eureka:
     client:
       serviceUrl:
         defaultZone: http://eureka-server:8761/eureka/
   ```
3. **Annotate Service**:
   ```java
   @EnableDiscoveryClient
   @SpringBootApplication
   public class OrderServiceApplication {}
   ```
4. **Use `@LoadBalanced` Feign Client**:
   ```java
   @FeignClient(name = "order-service")
   public interface OrderClient {
     @GetMapping("/orders/{id}")
     Order getOrder(@PathVariable String id);
   }
   ```

### **5.2 Server-Side Load Balancing (e.g., Nginx)**
1. **Add Ingress Controller**:
   ```nginx
   events {
     worker_connections 1024;
   }
   http {
     upstream order-service {
       least_conn;
       server order-service-1:8080;
       server order-service-2:8080;
     }
     server {
       listen 80;
       location /orders/ {
         proxy_pass http://order-service/;
       }
     }
   }
   ```

---

## **6. Query Examples for Common Tools**
### **6.1 Consul CLI**
List services:
```bash
consul services
```
Query service instances:
```bash
consul catalog service order-service
```

### **6.2 Kubernetes (Kube-DNS)**
```bash
kubectl get endpoints order-service
# Output:
NAME            ENDPOINTS
order-service   10.244.1.2:8080,10.244.2.3:8080
```

---

## **7. Best Practices**
| **Best Practice**                          | **Why It Matters**                                                                       |
|---------------------------------------------|-----------------------------------------------------------------------------------------|
| **Health Checks**                          | Fail fast: exclude unhealthy instances (TTL-based removal).                             |
| **Client-Side vs. Server-Side LB**         | Client-side: better for dynamic scaling; Server-side: better for TLS termination.       |
| **Circuit Breakers**                       | Avoid cascading failures (e.g., Hystrix, Resilience4j).                                |
| **Avoid Hardcoding IPs**                   | Use DNS/SRVs or service meshes (Istio, Linkerd) for dynamic resolution.                |
| **Minimize Registry Load**                | Use local caching (e.g., Spring Cloud’s `CacheRefreshFrequency`).                       |

---

## **8. Troubleshooting**
| **Issue**                          | **Solution**                                                                          |
|------------------------------------|---------------------------------------------------------------------------------------|
| **Stale Instances in Registry**    | Increase TTL or use heartbeat checks.                                                  |
| **High Latency in Discovery**      | Use local caching (e.g., `consul-template` for Consul).                               |
| **503 Errors (Service Unavailable)**| Check health check thresholds or increase LB timeouts.                                 |
| **Thundering Herd Problem**        | Implement backoff retries or queue-based load balancing.                               |

---

## **9. Related Patterns**
| **Pattern**                          | **Description**                                                                       |
|--------------------------------------|---------------------------------------------------------------------------------------|
| **[Resilience] Circuit Breaker**    | Prevents cascading failures (e.g., Hystrix, Resilience4j).                            |
| **[Observability] Distributed Tracing** | Tracks requests across services (e.g., OpenTelemetry, Jaeger).                   |
| **[Configuration] Dynamic Config**   | Externalizes config (e.g., Spring Cloud Config, Consul Config).                       |
| **[Security] API Gateway**           | Centralizes auth/rate-limiting (e.g., Kong, Apigee).                                |
| **[Resilience] Retry Mechanisms**   | Retries failed requests with exponential backoff.                                     |

---
**Final Notes**:
- For **stateful services**, prefer server-side LB or session persistence (e.g., `ip_hash` in Nginx).
- Monitor **registry health** (e.g., Prometheus alerts for failed registrations).
- In **Kubernetes**, use `Service` + `Ingress` or Istio for auto-discovery and LB.

---
This guide provides a structured, scannable reference for implementing Service Discovery & Load Balancing. Adjust examples based on your tech stack (e.g., replace Eureka with Kubernetes for cloud-native deployments).