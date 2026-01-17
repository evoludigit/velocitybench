---
# **[Pattern] Hybrid Techniques Reference Guide**

---

## **1. Overview**
The **Hybrid Techniques** pattern combines **traditional code-centric approaches** with **declarative or runtime-driven automation** to achieve optimal performance, flexibility, and maintainability. This approach bridges the gap between manual scripting and pure declarative workflows by leveraging:

- **Hybrid scripts** (mix of imperative and declarative logic)
- **Runtime dynamic adjustments** (adapting logic based on system state or external triggers)
- **Partial automation** (automating repetitive tasks while allowing manual overrides)

Ideal for scenarios where **pure automation isn’t sufficient**, but **full manual intervention is inefficient**. Common use cases include:
- **CI/CD pipelines** (hybrid deployments with manual approvals)
- **Infrastructure provisioning** (Terraform + custom scripts for edge cases)
- **Data processing pipelines** (batch + stream processing with dynamic branching)

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                 | **Example Value**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Trigger Type**            | Defines when the hybrid technique executes (manual, schedule, event, API).    | `["on_build_complete", "manual_override", "error_breaker"]`                       |
| **Execution Mode**          | Determines code execution strategy: imperative, declarative, or mixed.          | `["script", "config-driven", "hybrid"]`                                           |
| **Runtime Adaptors**        | Components dynamically adjusting logic (e.g., conditionals, loops, substitutions). | `["if-else-chainer", "loop-breaker", "api-trigger"]`                              |
| **Fallback Mechanism**      | Defines how to handle failures (retry, manual, skip).                          | `{"retries": 2, "max_time": 60, "fallback_to": "manual_review"}`                 |
| **Audit Trail**             | Logs executed steps and overrides for compliance/debugging.                     | `{ "action": "deploy_app", "status": "partially_automated", "override_by": "user"`}|
| **Version Control**         | Tracks changes to hybrid logic (e.g., Git, artifact registry).                 | `{ "version": "1.2.0", "last_modified": "2024-02-15" }`                          |
| **Integration Hooks**       | External systems called during execution (APIs, databases, messaging queues).   | `["slack_notification", "database_sync", "kafka_publish"]`                       |

---

## **3. Implementation Details**

### **3.1 Core Principles**
1. **Modular Design**
   - Break hybrid logic into reusable components (e.g., reusable functions, config files).
   - Example:
     ```yaml
     # hybrid_config.yaml
     deploy_step:
       mode: hybrid
       imperative_part: "run ./deploy.sh"  # Script execution
       declarative_part:
         - action: "run_terraform"
           conditions: "-if 'terraform_state == stable'"
     ```

2. **Stateful Execution**
   - Track runtime variables (e.g., environment variables, API responses) to enable dynamic branching.
   - Example (Python):
     ```python
     import os
     if os.getenv("RUN_MODE") == "prod":
         # Critical path
         os.system("terraform apply -auto-approve")
     else:
         # Fallback
         input("Press Enter to approve manually...")
     ```

3. **Graceful Fallbacks**
   - Define escalation paths for failures (e.g., notify ops team, skip step, or abort).
   - Example (CLI):
     ```bash
     #!/bin/bash
     if ! ./validate_credentials.sh; then
       echo "Error detected. Falling back to manual review..."
       slack_notify "Manual approval required for $STAGE"
       exit 1
     fi
     ```

### **3.2 Runtime Adaptors**
| **Adaptor**               | **Purpose**                                                                 | **Example Use Case**                                  |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------|
| **Conditional Logic**     | Executes branches based on runtime conditions.                               | `if (disk_free > 5GB) { proceed } else { alert }`     |
| **Loop Breaker**          | Stops/skips iterative processes early.                                      | `while (queue_length > 0) { process_item(); if error break; }` |
| **API Trigger**           | Dynamically calls external APIs for real-time data.                          | Fetch database status before deploying.                 |
| **Time-based Switch**     | Adjusts logic based on cron-like schedules.                                | "Run cleanup only during off-peak hours (2AM)."       |
| **User Input Prompt**     | Forces manual approvals mid-execution.                                      | `confirm_deployment: "Press Y to proceed"`              |

---

## **4. Query Examples**

### **4.1 Querying Hybrid Logic with CLI**
```bash
# List hybrid steps in a pipeline
hybrid-cli list --pipeline deploy_app

# Debug a hybrid step
hybrid-cli trace --step "validate_db" --version 1.2.0

# Override a hybrid condition
hybrid-cli override --step "deploy" --mode manual --user alice
```

### **4.2 Querying via API**
```http
GET /api/v1/pipelines/hybrid/deploy_app/status
Headers:
  Authorization: Bearer <token>
Response:
{
  "status": "partially_automated",
  "steps": [
    {
      "name": "build",
      "mode": "automated",
      "completed": true
    },
    {
      "name": "deploy",
      "mode": "hybrid",
      "status": "pending_user_approval",
      "last_override": "2024-02-15T10:00:00Z",
      "overridden_by": "jdoe"
    }
  ]
}
```

### **4.3 Example: Hybrid Deployment Workflow**
1. **Automated Steps** (Imperative):
   ```bash
   #!/bin/bash
   git pull origin main
   mvn package
   ```
2. **Hybrid Step** (Declarative + Runtime Adjustment):
   ```yaml
   - name: deploy_to_env
     mode: hybrid
     imperative:
       - "kubectl apply -f k8s/deploy.yaml"
     declarative:
       - action: "rollout_status"
         conditions:
           - "if 'kubectl get pods | grep -v Running'":
               - action: "slack_alert"
                 message: "Pods not running. Manual intervention required."
   ```
3. **Fallback**:
   If the declarative check fails, the system triggers a Slack alert and halts further automation.

---

## **5. Query Patterns by Use Case**

| **Use Case**               | **Query Pattern**                                                                 | **Example**                                                                 |
|----------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **CI/CD with Manual Gates** | Use `hybrid-cli override --step <step> --mode manual` to pause automation.       | `hybrid-cli override --step "deploy_prod" --mode manual`                   |
| **Dynamic Infrastructure** | Query runtime adaptors for API-triggered adjustments.                             | `hybrid-cli query --step "scale_db" --adaptor "time_based_switch"`          |
| **Audit Compliance**       | Filter steps with `fallback_to: manual` in audit logs.                           | `hybrid-cli audit --filter "manual_fallback=true"`                         |

---

## **6. Related Patterns**

| **Pattern**                | **Connection to Hybrid Techniques**                                                                 | **When to Use Together**                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Step Chaining**          | Hybrid techniques often rely on step chaining to sequence imperative/declarative blocks.         | When steps depend on each other’s success/failure (e.g., `build → test → deploy`).        |
| **Config-Driven Workflows**| Hybrid logic can reference configs (e.g., Terraform, Ansible) for declarative parts.              | For infrastructure-as-code with customizable logic.                                    |
| **Circuit Breakers**       | Fallback mechanisms in hybrid techniques can integrate with circuit breakers for resilience.      | When handling flaky external APIs or services.                                          |
| **Event-Driven Automation**| Hybrid techniques can trigger on events (e.g., Kafka messages, webhooks).                          | For reactive systems where runtime decisions depend on external triggers.               |
| **Canary Deployments**     | Hybrid logic can dynamically route traffic to canary instances based on runtime metrics.         | Gradual rollouts with manual override fallback.                                        |

---

## **7. Best Practices**
1. **Document Overrides**
   - Log all manual interventions in the audit trail for traceability.
2. **Leverage Idempotency**
   - Design hybrid logic to be retriable (e.g., use `kubectl apply --server-side`).
3. **Optimize Runtime Checks**
   - Minimize API calls or disk I/O in conditional logic for performance.
4. **Test Fallbacks**
   - Simulate failures to ensure fallbacks (e.g., mock API errors) work as expected.
5. **Version Hybrid Logic**
   - Tag hybrid configurations (e.g., `v1.2.0`) to roll back if issues arise.

---
**See Also:**
- [Step Chaining Pattern Reference](link)
- [Config-Driven Workflows](link)
- [Circuit Breaker Pattern](link)