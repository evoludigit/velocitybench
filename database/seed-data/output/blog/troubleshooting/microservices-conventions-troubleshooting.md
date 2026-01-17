# **Debugging Microservices Conventions: A Troubleshooting Guide**

## **Introduction**
Microservices architectures rely on **conventions** (e.g., API design, service discovery, logging, and data consistency) to ensure scalability, modularity, and maintainability. However, deviations from these conventions—whether intentional or accidental—can lead to **latency spikes, cascading failures, debugging nightmares, and inconsistent behavior**.

This guide covers **common symptoms, root causes, fixes, debugging techniques, and prevention strategies** for microservices misconfigurations.

---

## **Symptom Checklist**
Before diving into debugging, confirm the following symptoms:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| **High Latency in API Calls** | Endpoints respond slowly or time out (`5XX`, `429 Too Many Requests`) | Poor user experience, degraded performance |
| **Service Discovery Failures** | Services fail to register/discover each other (`EUREKA not found`, `K8S PodNotFound`) | Inability to route traffic, downtime |
| **Inconsistent Data** | Transactional data mismatches across services (e.g., `Order` vs. `Inventory`) | Financial losses, incorrect state |
| **Log Corruption or Overload** | Logs are unreadable, missing, or overwhelm the system (`grep` fails, ELK overload) | Unable to trace incidents |
| **"Service Unavailable" Errors** | `503` errors despite healthy underlying services | Cascading failures |
| **Network Timeouts** | Inter-service calls hang (`java.net.SocketTimeoutException`) | Deadlocks, retries, and instability |
| **Metric Mismatch** | Prometheus/Grafana shows inconsistent traffic/memory usage per service | Misleading monitoring |
| **Config Drift** | Services run with mismatched settings (e.g., different DB URLs) | Runtime failures |

---

## **Common Issues & Fixes**

### **1. Service Discovery Failures**
**Symptom:** `Cannot connect to service <X>` despite healthy pods/containers.

#### **Root Causes:**
- **Misconfigured service names** (e.g., `ORDER-SERVICE` vs. `order-service`).
- **DNS resolution issues** (e.g., `kube-dns` not serving requests).
- **Network policies blocking inter-service traffic** (e.g., Calico/Nginx ingress misrules).
- **Self-hosted registries (EUREKA, Consul) not updating.**

#### ** Fixes:**
##### **A. Verify Service Name Registration**
- **Check Kubernetes Services:**
  ```sh
  kubectl get svc | grep order-service
  ```
  - Ensure the service name matches the DNS entry (`order-service.default.svc.cluster.local`).
- **Check Eureka/Nacos:**
  ```sh
  curl -X GET http://eureka-server:8761/eureka/apps
  ```
  - If the service is missing, check the **client-side configuration** (`application.yml`):
    ```yaml
    eureka:
      client:
        serviceUrl:
          defaultZone: http://eureka-server:8761/eureka/
        fetchRegistry: true  # Ensure this is enabled
    ```

##### **B. Test DNS Resolution**
```sh
kubectl exec -it <pod-name> -- nslookup order-service.default.svc.cluster.local
```
- **Fix:** If DNS fails, check **Kube-DNS** logs:
  ```sh
  kubectl logs -l k8s-app=kube-dns
  ```

##### **C. Verify Network Policies**
```sh
kubectl get networkpolicy -A
```
- **Fix:** If traffic is blocked, update the policy:
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: allow-order-internal
  spec:
    podSelector:
      matchLabels:
        app: order-service
    policyTypes:
    - Ingress
    ingress:
    - from:
      - podSelector:
          matchLabels:
            app: api-gateway
      ports:
      - protocol: TCP
        port: 8080
  ```

---

### **2. High Latency in API Calls**
**Symptom:** `2xx` responses but **slow execution** (e.g., 2s → 20s).

#### **Root Causes:**
- **Unoptimized HTTP clients** (e.g., no connection pooling).
- **Missing circuit breakers** (e.g., Hystrix/Resilience4j).
- **Database bottlenecks** (e.g., single DB connection, no sharding).
- **Chatty services** (e.g., too many nested calls).

#### **Fixes:**
##### **A. Optimize REST Clients (Spring Boot Example)**
- **Use `RestTemplate` with connection pooling:**
  ```java
  @Bean
  public RestTemplate restTemplate() {
      HttpClient httpClient = HttpClients.custom()
          .setMaxConnTotal(100)
          .setMaxConnPerRoute(20)
          .build();
      HttpComponentsClientHttpRequestFactory factory =
          new HttpComponentsClientHttpRequestFactory(httpClient);
      return new RestTemplate(factory);
  }
  ```
- **Use WebClient (Reactors) for async calls:**
  ```java
  @Bean
  public WebClient webClient() {
      return WebClient.builder()
          .baseUrl("http://order-service")
          .filter(new CircuitBreakerWebFilter()) // Resilience4j
          .build();
  }
  ```

##### **B. Implement Circuit Breakers**
- **Add Resilience4j to `pom.xml`:**
  ```xml
  <dependency>
      <groupId>io.github.resilience4j</groupId>
      <artifactId>resilience4j-spring-boot2</artifactId>
      <version>1.7.1</version>
  </dependency>
  ```
- **Configure in `application.yml`:**
  ```yaml
  resilience4j:
    circuitbreaker:
      instances:
        orderService:
          registeredSuccesForHalfOpenDuration: 5s
          failureRateThreshold: 50
          waitDurationInOpenState: 30s
  ```
- **Apply to method:**
  ```java
  @CircuitBreaker(name = "orderService", fallbackMethod = "fallback")
  public Mono<Order> getOrder(Long id) {
      return webClient.get().uri("/orders/{id}", id).retrieve().bodyToMono(Order.class);
  }
  ```

##### **C. Batch Database Queries**
- **Use JPA `@NamedQuery` + `CriteriaBuilder` instead of N+1:**
  ```java
  @Repository
  public interface OrderRepository extends JpaRepository<Order, Long> {
      @Query("SELECT o FROM Order o WHERE o.id IN :ids")
      List<Order> findAllByIds(@Param("ids") List<Long> ids);
  }
  ```
- **Enable Spring Data JPA batch fetching:**
  ```java
  @Configuration
  public class JpaConfig {
      @Bean
      public LocalContainerEntityManagerFactoryBean entityManagerFactory(
          EntityManagerFactoryBuilder builder,
          DataSource dataSource) {
          return builder
              .dataSource(dataSource)
              .packages("com.example.model")
              .properties(
                  Map.of(
                      "spring.jpa.properties.hibernate.fetch.size.batching_size", "20",
                      "spring.jpa.properties.hibernate.fetch.size.enable", "true"
                  )
              )
              .build();
      }
  }
  ```

---

### **3. Inconsistent Data (Eventual Consistency Issues)**
**Symptom:** `Order` created but `Inventory` not updated.

#### **Root Causes:**
- **No compensating transactions** on failure.
- **Eventual consistency not enforced** (e.g., missing Kafka consumers).
- **Idempotency keys missing** in event processing.

#### **Fixes:**
##### **A. Use Saga Pattern (Choreography)**
- **Publish events on order creation:**
  ```java
  @Transactional
  public void createOrder(Order order) {
      // Save order
      orderRepository.save(order);

      // Publish "OrderCreated" event
      orderCreatedEventPublisher.publish(
          new OrderCreatedEvent(order.getId(), order.getProductId(), 1));
  }
  ```
- **Handle events in separate service (Inventory):**
  ```java
  @KafkaListener(topics = "order-created")
  public void handleOrderCreated(OrderCreatedEvent event) {
      inventoryService.deductStock(event.getProductId(), event.getQuantity());
  }
  ```
- **Add retry logic (Spring Retry):**
  ```xml
  <dependency>
      <groupId>org.springframework.retry</groupId>
      <artifactId>spring-retry</artifactId>
  </dependency>
  ```
  ```java
  @Retryable(value = {StockNotAvailableException.class}, maxAttempts = 3)
  public void deductStock(Long productId, int quantity) {
      // Logic to deduct stock
  }
  ```

##### **B. Implement Idempotency**
- **Store processed events in DB:**
  ```java
  @Entity
  public class ProcessedEvent {
      @Id
      private UUID eventId;
      private LocalDateTime processedAt;
      // ... getters/setters
  }
  ```
- **Check before processing:**
  ```java
  @KafkaListener
  public void listen(OrderCreatedEvent event) {
      if (processedEventRepository.existsByEventId(event.getEventId())) {
          return; // Skip if already processed
      }
      // Process logic...
      processedEventRepository.save(
          new ProcessedEvent(event.getEventId(), LocalDateTime.now()));
  }
  ```

---

### **4. Log Corruption & Overload**
**Symptom:** `grep "ERROR" *log* | tail` returns nothing, or logs take too long to parse.

#### **Root Causes:**
- **Log rotation not configured** (logs grow unbounded).
- **Async loggers (e.g., Logback) misconfigured.**
- **ELK/Grafana pipeline failing.**

#### **Fixes:**
##### **A. Configure Log Rotation (Logback Example)**
```xml
<configuration>
    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/app.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/app.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory> <!-- Keep 30 days -->
        </rollingPolicy>
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    <root level="INFO">
        <appender-ref ref="FILE" />
    </root>
</configuration>
```

##### **B. Use Structured Logging (JSON)**
```java
@Slf4j
public class OrderController {
    @PostMapping("/orders")
    public ResponseEntity<Order> createOrder(@RequestBody OrderRequest request) {
        Order order = service.createOrder(request);
        log.info("Order created: {}",
            JsonObject.of(
                "orderId", order.getId(),
                "status", "CREATED",
                "timestamp", Instant.now()
            )
        );
        return ResponseEntity.ok(order);
    }
}
```
**Benefit:** Easier querying in ELK:
```json
// ELK Query DSL
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "INFO" } },
        { "match": { "msg": "Order created" } }
      ]
    }
  }
}
```

##### **C. Monitor Log Shipper (Fluentd/Logstash)**
- **Check Fluentd logs for failures:**
  ```sh
  docker logs fluentd
  ```
- **Verify ELK indices:**
  ```sh
  curl -X GET "http://localhost:9200/_cat/indices?v"
  ```

---

### **5. "Service Unavailable" Errors (503)**
**Symptom:** `503` despite healthy pods.

#### **Root Causes:**
- **Liveness probes failing** (e.g., health check endpoint returns `500`).
- **HPA (Horizontal Pod Autoscaler) stuck.**
- **Ingress misconfiguration** (e.g., wrong `host` rule).

#### **Fixes:**
##### **A. Debug Liveness Probes**
- **Check pod logs:**
  ```sh
  kubectl logs <pod-name> --previous  # Check previous container
  ```
- **Test the health endpoint manually:**
  ```sh
  curl http://<pod-ip>:8080/actuator/health
  ```
- **Fix probe in deployment:**
  ```yaml
  livenessProbe:
    httpGet:
      path: /actuator/health
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  ```

##### **B. Verify HPA Scaling**
```sh
kubectl get hpa
kubectl describe hpa <hpa-name>
```
- **Fix scaling issues:**
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: order-service-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: order-service
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

##### **C. Check Ingress Rules**
```sh
kubectl get ingress
kubectl describe ingress <ingress-name>
```
- **Fix misconfigured host:**
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: Ingress
  metadata:
    name: api-ingress
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: /$2
  spec:
    rules:
    - host: api.example.com
      http:
        paths:
        - path: /order(/|$)(.*)
          pathType: Prefix
          backend:
            service:
              name: order-service
              port:
                number: 80
  ```

---

## **Debugging Tools & Techniques**

| **Tool** | **Purpose** | **Example Command/Usage** |
|----------|------------|---------------------------|
| **Kubernetes `kubectl debug`** | Run a temporary shell in a failing pod | `kubectl debug -it <pod> --image=busybox` |
| **Postman/Newman** | Test API contracts | `newman run postman_collection.json --reporters cli,junit` |
| **Prometheus + Grafana** | Monitor service health | `kubectl port-forward svc/prometheus 9090:9090` |
| **Jaeger/Tracing** | Track distributed transactions | `curl http://jaeger:16686/search` |
| **Fluent Bit** | Debug log shipping | `docker logs fluent-bit` |
| **cURL + `jq`** | Inspect API responses | `curl -s http://order-service/health | jq '.'` |
| **NetData** | Real-time network metrics | `netdata-cli --help` |
| **Git blame** | Find when a config changed | `git blame config/application.yml` |

---

## **Prevention Strategies**

### **1. Enforce Conventions via CI/CD**
- **Static Analysis:**
  - Use **OpenAPI/Swagger** to validate API contracts.
  - Example: **SpringDoc OpenAPI** with `springdoc-openapi-starter-webmvc-ui`.
  ```java
  @Bean
  public OpenAPI customOpenAPI() {
      return new OpenAPI()
          .components(new Components()
              .addSecuritySchemes("bearerAuth",
                  new SecurityScheme()
                      .type(SecurityScheme.Type.HTTP)
                      .scheme("bearer")
                      .bearerFormat("JWT"))
          )
          .addSecurityItem(new SecurityRequirement()
              .addList("bearerAuth"));
  }
  ```
- **Git Hooks:**
  - Block merges if `application.yml` has typos:
    ```sh
    # .git/hooks/pre-commit
    if grep -q "eureka.client.serviceUrl.defaultZone" .; then
      if ! grep -q "http://eureka-server:8761/eureka/" .; then
        echo "Eureka config missing!"; exit 1
      fi
    fi
    ```

### **2. Automated Testing**
| **Test Type** | **Tool** | **Example** |
|--------------|---------|-------------|
| **Contract Tests** | Pact | `mvn test -Dpact.method=contract-test` |
| **Chaos Engineering** | Gremlin | Simulate network partitions |
| **Load Testing** | Locust | Scale to 1000 RPS |

### **3. Observability as Code**
- **Centralized Tracing:**
  ```yaml
  # application.yml
  spring:
    sleuth:
      sampler:
        probability: 1.0
    zipkin:
      base-url: http://zipkin:9411
  ```
- **Auto-Generated Metrics:**
  ```properties
  # prometheus.yml
  scrape_configs:
    - job_name: 'spring_boot'
      metrics_path: '/actuator/prometheus'
      static_configs:
        - targets: ['order-service:8080']
  ```

### **4. Chaos Engineering (Preventive Checks)**
- **Kill pods randomly (Gremlin):**
  ```sh
  gremlin run kill-random-pods -n default -l app=order-service --frequency=5s
  ```
- **Simulate latency:**
  ```sh
  tc qdisc add dev lo root netem delay 500ms
  ```

### **5. Documentation & Runbooks**
- **Maintain a `CONTRIBUTING.md`** with:
  ```markdown
  ## Microservices Conventions
  1. All services must expose `/actuator/health`.
  2. Use UUIDs for IDs (not auto-increment IDs).
  3. Deploy with `kubectl apply -f k8s/`.
  ```
- **Create a `RUNBOOK.md`** for common failures:
  ```markdown
  ## Service Unavailable (503)
  1. Check HPA: `kubectl get hpa`
  2. Verify liveness