# **[Azure Architecture Patterns] Reference Guide**

---

## **Overview**
Azure Architecture Patterns provide **proven, reusable solutions** to common cloud design challenges, ensuring scalability, security, resilience, and cost-efficiency. These patterns are categorized into **five core areas**:
- **Resiliency**: Ensures systems can recover from failures.
- **Scalability & Elasticity**: Adapts to workload demands.
- **Security**: Protects data and infrastructure.
- **Performance**: Optimizes speed and efficiency.
- **Reliability**: Maintains consistent, predictable behavior.

This reference outlines **15 core patterns** (e.g., *CQRS, Event Sourcing, Microservices*, etc.) with **implementation guidance, trade-offs, and best practices**. Use this guide to **select, customize, and deploy** patterns in Azure cloud environments.

---

## **Schema Reference**
Below is a structured breakdown of **Azure Architecture Patterns**, organized by category and key attributes.

| **Pattern Name**       | **Category**          | **Primary Use Case**                          | **Key Components**                                                                 | **Azure Services**                                                                 | **Trade-offs**                                                                                     |
|------------------------|-----------------------|-----------------------------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Nested Virtual Application** | Resiliency           | Fault-tolerant web apps                       | Load Balancer, Auto Scaling, Health Probes                                       | Application Gateway, Azure Load Balancer, VM Scale Sets                          | Higher complexity, increased monitoring overhead.                                               |
| **CQRS (Command Query Responsibility Segregation)** | Scalability | High-performance read/write separation      | API Gateway, Event Store, Read/Write Models                                      | Cosmos DB, Azure Functions, API Management                                      | Complex event sourcing; requires careful versioning.                                            |
| **Event-Driven Microservices** | Scalability/Resiliency | Decoupled, scalable services                  | Pub/Sub Model, Event Hubs, Service Bus, Event Sourcing                           | Azure Event Grid, Service Bus, Cosmos DB                                             | Event ordering challenges; state management complexity.                                       |
| **Hybrid Cloud Integration** | Security/Performance | Unify on-prem and cloud workloads            | VPN Gateway, ExpressRoute, Active Directory Federation                             | Azure VPN Gateway, ExpressRoute, Azure AD                                          | Latency for cross-premises calls; security risk if misconfigured.                              |
| **Multi-Tier Web Application** | Reliability          | Scalable, secure web apps                     | Frontend, Backend, Database, CDN, Caching                                         | Azure App Service, Azure SQL DB, CDN                                             | Monolithic scaling limitations; security risk if tiers aren’t isolated.                      |
| **Microservices**      | Scalability/Reliability | Independent, modular services                | Containers, Kubernetes, API Gateways, Service Mesh                             | Azure Kubernetes Service (AKS), Azure Container Instances, API Management         | Orchestration complexity; inter-service communication overhead.                                |
| **Serverless**         | Scalability/Performance | Event-driven, auto-scaled functions          | Event Sources, Functions, Storage (Blob/Queue)                                   | Azure Functions, Logic Apps, Cosmos DB                                             | Cold-start latency; vendor lock-in risks.                                                   |
| **Bright/Shiny Interface** | Performance           | High-performance UI with lightweight backend | Static Hosting, Edge Caching, Progressive Web Apps                              | Azure Static Web Apps, CDN, Azure Front Door                                        | Backend logic must be stateless.                                                          |
| **Event Sourcing**     | Resiliency            | Audit-able, immutable data history            | Event Store, Stream Processing, State Reconstruction                             | Cosmos DB, Event Hubs, Azure Stream Analytics                                      | Query complexity; requires replay capability.                                               |
| **Command Bus**        | Scalability           | Distributed command processing                | Message Brokers, Retry Policies, Compensation Transactions                      | Service Bus, Event Grid                                                               | Complex transaction management.                                                          |
| **Rate Limiting & Throttling** | Security             | Prevent abuse of APIs                          | Token Bucket, Fixed Window, Sliding Window Policies                               | Azure API Management, Application Gateway                                          | False positives if misconfigured.                                                       |
| **Data Partitioning**  | Performance           | Horizontal scaling of storage                  | Sharding, Range Partitioning, Hash Partitioning                                   | Cosmos DB, SQL DB, Blob Storage                                                     | Hotspots if partitioning keys aren’t optimized.                                            |
| **Optimistic Concurrency** | Resiliency           | Conflict-free data updates                     | Version Stamping, Last-Write-Wins, Conflict-Free Replicated Data Types (CRDTs) | Cosmos DB, SQL DB                                                                           | Risk of lost updates if conflicts aren’t resolved.                                         |
| **Caching**            | Performance           | Reduce latency for frequent queries           | Distributed Cache, CDN, Query Cache                                            | Redis Cache, Azure CDN, Cache API                                                     | Cache invalidation challenges.                                                          |
| **Identity Federation** | Security              | Secure cross-domain authentication            | OAuth 2.0, OpenID Connect, Kerberos                                           | Azure AD, Azure AD B2C, AD FS                                                         | Complex setup; relies on trusted identity providers.                                       |
| **Disaster Recovery (Hybrid/Cloud)** | Resiliency           | Business continuity across regions           | Backup & Restore, Geo-Replication, Failover Testing                            | Azure Backup, Azure Site Recovery, Traps                                                 | Increased operational overhead.                                                           |

---
## **Query Examples**
Below are **common implementation scenarios** for Azure Architecture Patterns.

---

### **1. Implementing CQRS with Cosmos DB**
**Scenario**: A high-traffic e-commerce app needs **separate read/write models** for performance.

#### **Steps**:
1. **Define Commands & Queries**:
   ```json
   // Command (Write Operation)
   {
     "command": "CreateOrder",
     "order": { "orderId": "123", "items": [{ "productId": "A", "qty": 2 }] }
   }

   // Query (Read Operation)
   {
     "query": "GetOrder",
     "orderId": "123"
   }
   ```
2. **Deploy Read Optimizer (Cosmos DB Container)**:
   ```bash
   az cosmosdb sql create-container \
     --account-name MyCosmosDB \
     --resource-group MyRG \
     --database OrdersDB \
     --name OrdersRead \
     --partition-key-path /orderId \
     --options "{\"indexingPolicy\":{\"indexingMode\":\"consistent\"}}"
   ```
3. **Use Azure Functions for Processing**:
   ```csharp
   [FunctionName("ProcessOrder")]
   public static void Run([ServiceBusTrigger("orders-queue")] string orderJson, ILogger log)
   {
       // Parse & store in Write Model (separate Container)
       var order = JsonConvert.DeserializeObject<Order>(orderJson);
       await _cosmosWrite.CreateItemAsync(order);
   }
   ```

---

### **2. Setting Up Event-Driven Microservices with Event Grid**
**Scenario**: A **loyalty program** needs real-time notifications when users spend over a threshold.

#### **Steps**:
1. **Publish Event from Service**:
   ```bash
   az eventgrid event create \
     --topic-name SpendThresholdTopic \
     --event-data '{
       "eventType": "SpendThresholdCrossed",
       "userId": "user123",
       "amount": 100
     }'
   ```
2. **Subscribe Notification Service**:
   ```csharp
   // Azure Function Trigger (Event Grid)
   [FunctionName("ProcessSpendEvent")]
   public static async Task Run(
       [EventGridTrigger] EventGridEvent eventGridEvent,
       ILogger log)
   {
       if (eventGridEvent.EventType == "SpendThresholdCrossed")
       {
           await _loyaltyService.AwardPoints(eventGridEvent.Data);
       }
   }
   ```

---

### **3. Implementing Rate Limiting with Azure API Management**
**Scenario**: Protect an API from **DDoS attacks** with **token bucket throttling**.

#### **Steps**:
1. **Configure Policy in APIM**:
   ```xml
   <rate-limit-by-key calls="1000" renewable-calls="1000" renewable-period="60" counter-key="@(context.Request.IpAddress)" />
   ```
2. **Apply to API**:
   ```bash
   az apim policy add \
     --product-name "MyProduct" \
     --policy-file "rate-limit-policy.xml"
   ```
3. **Test with Postman**:
   ```bash
   curl -X POST "https://myapi.azure-api.net/api/orders" \
     -H "Authorization: Bearer $TOKEN"
   ```
   *(Should return `429 Too Many Requests` after limit is hit.)*

---

### **4. Hybrid Cloud Integration with ExpressRoute**
**Scenario**: Sync **on-premises SQL Server** with **Azure SQL DB** for disaster recovery.

#### **Steps**:
1. **Create ExpressRoute Circuit**:
   ```bash
   az network express-route circuit create \
     --resource-group MyRG \
     --name MyExpressRoute \
     --peer-asn 65010 \
     --spoke-bandwidth 1Gbps
   ```
2. **Configure SQL Database Sync (Azure Arc)**:
   ```bash
   az arc server provision \
     --resource-group MyRG \
     --server-name "OnPremSQL" \
     --location "eastus" \
     --connectivity-method "expressroute"
   ```
3. **Set Up Log Shipping**:
   ```sql
   -- On Azure SQL DB
   EXEC sp_set_db_for_tql_notifications @db_name = 'MyDB', @notification_level = '2';
   ```

---

## **Related Patterns**
Azure Architecture Patterns often **complement** other Microsoft and industry-standard designs:

| **Related Pattern**               | **Purpose**                                                                 | **When to Use**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Azure Well-Architected Framework** | Guides **five pillars** (Operational Excellence, Security, Reliability, etc.) | Use for **enterprise-scale validation** of designs.                        |
| **12-Factor App**                 | Best practices for **modern app development** (stateless, config as code, etc.) | Pair with **serverless** or **microservices** for cloud-native apps.       |
| **SRE (Site Reliability Engineering)** | Balances **reliability** with **efficiency** in production systems.          | Critical for **high-availability** systems (e.g., financial services).          |
| **Event-Driven Architecture (EDA)** | Loosely coupled systems via **events**.                                      | Use for **real-time processing** (e.g., IoT, notifications).                 |
| **Domain-Driven Design (DDD)**    | Models software around **business domains**.                                 | Helps **microservices** boundaries align with business logic.                |
| **GitOps**                        | Manages infrastructure via **Git repositories**.                            | Use for **declarative CI/CD** in Kubernetes (AKS).                           |

---

## **Best Practices**
1. **Start Small, Iterate**:
   - Begin with **one pattern** (e.g., serverless for a new feature) before scaling.
2. **Monitor & Optimize**:
   - Use **Azure Monitor** and **Application Insights** to track performance.
3. **Security by Default**:
   - Enforce **least-privilege access** (RBAC) and **encryption at rest/transit**.
4. **Disaster Recovery Planning**:
   - Test **failover** with **Azure Site Recovery** at least quarterly.
5. **Cost Optimization**:
   - Use **Azure Advisor** to identify underutilized resources (e.g., VMs, storage).

---
## **Troubleshooting Common Issues**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|------------------------------------|----------------------------------------|------------------------------------------------------------------------------|
| **Cold Start Latency (Serverless)** | Function scales to zero after inactivity. | Use **Premium Plan** or **keep-alive patterns**.                           |
| **Cosmos DB Throttling**           | Requests exceed **RU/s** limits.        | Increase **RU/s** or optimize queries.                                       |
| **Event Ordering Problems**        | Events processed out of sequence.      | Use **event sourcing** with **sequence numbers** or **sagas**.              |
| **Hybrid VPN Instability**         | Network jitter or misconfigured routes. | Check **MTU settings** and **BGP peering**.                                  |
| **API Throttling (APIM)**          | Rate limits hit.                       | Adjust **policies** or use **cache layer**.                                 |

---
## **Further Reading**
- [Microsoft Azure Architecture Patterns Documentation](https://docs.microsoft.com/en-us/azure/architecture/patterns/)
- [Azure Well-Architected Framework](https://docs.microsoft.com/en-us/azure/architecture/framework/)
- [12-Factor App](https://12factor.net/)
- [SRE Best Practices](https://cloud.google.com/sre)

---
**Last Updated**: `[Insert Date]`
**Feedback**: [Azure Architecture Patterns Feedback](https://feedback.azure.com/forums/217313-azure-microsoft-store-feedback)