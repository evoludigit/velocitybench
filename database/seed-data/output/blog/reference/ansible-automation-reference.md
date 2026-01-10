# **[Pattern] Ansible Automation Integration Patterns – Reference Guide**

---

## **Overview**
The **Ansible Automation Integration Patterns** provide a structured approach to designing, implementing, and maintaining reusable automation workflows that integrate seamlessly with external systems, APIs, cloud platforms, CI/CD pipelines, and other automation tools. This guide outlines core principles, implementation best practices, and common anti-patterns to ensure scalable, maintainable, and efficient automation.

Ansible’s agentless architecture and YAML-based workflows make it highly adaptable for integration scenarios, but successful implementations require careful consideration of modularity, error handling, and data exchange mechanisms. This guide covers key strategies like:
- **External API Integration** (REST/gRPC, OAuth, API keys)
- **Cloud & IaC Integration** (AWS, Azure, GCP, Terraform, Pulumi)
- **CI/CD Pipeline Integration** (GitHub Actions, GitLab CI, Jenkins)
- **Event-Driven Automation** (Webhooks, MQTT, Kafka)
- **Legacy System Integration** (SSH/SCP, SNMP, databases)
- **Dynamic Inventory & Discovery**

---

## **Schema Reference**
Below are standardized **YAML schemas** for common integration patterns. Adjust as needed for your environment.

| **Integration Type**       | **YAML Schema**                                                                 | **Key Parameters**                                                                 |
|----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **REST API Call**          | `resource: "{{ lookup('url', api_url + payload, wantlist=False) }}"`          | `api_url`, `method` (GET/POST), `headers`, `auth` (Bearer/OAuth), `timeout` (s)    |
| **Cloud Provider Module**  | `- name: Create AWS EC2 instance` <br>  `aws_ec2: ...`                           | `instance_type`, `image_id`, `key_name`, `security_groups`, `region`             |
| **Webhook Event Handler**  | `async_task: "{{ playbook_url }}?webhook_token={{ token }}"`                   | `webhook_url`, `body` (event payload), `verify_certs`, `timeout` (60s–3600s)       |
| **CI/CD Trigger**          | `local_action: command "curl -X POST {{ github_webhook_url }}"`                | `webhook_url`, `payload` (JSON), `branch`, `commit_hash`                         |
| **Database Query**         | `postgres_query: db=db_name user=user password=pass query="SELECT * FROM users"` | `db`, `user`, `password`, `query`, `return_format` (list/dict)                   |
| **Dynamic Inventory**      | `aws_ec2_inventory: ...`                                                        | `regions`, `filters`, `cache_file`, `cache_timeout` (s)                          |

---

## **Query & Example Implementations**
### **1. REST API Integration (HTTP Request)**
**Use Case:** Fetching user data from a third-party API (e.g., Stripe, Slack).
**Example Playbook:**
```yaml
---
- name: Fetch Stripe customers
  hosts: localhost
  vars:
    stripe_api_key: "{{ lookup('env', 'STRIPE_API_KEY') }}"
    endpoint: "https://api.stripe.com/v1/customers"
  tasks:
    - name: Call Stripe API
      uri:
        url: "{{ endpoint }}"
        method: GET
        headers:
          Authorization: "Bearer {{ stripe_api_key }}"
        return_content: yes
      register: stripe_response
      failed_when: stripe_response.status != 200

    - name: Display results
      debug:
        var: stripe_response.json
```

**Key Considerations:**
- Use `uri` module for HTTP requests.
- Handle **pagination** via `limit`/`offset`.
- Cache responses for idempotency.
- Validate JSON responses with `jq`.

---

### **2. Cloud Provider Integration (AWS Example)**
**Use Case:** Provisioning an EC2 instance with security groups.
**Example Playbook:**
```yaml
---
- name: Launch AWS EC2 instance
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Create security group
      amazon.aws.ec2_group:
        name: "ansible-sg"
        description: "SG for Ansible-controlled instances"
        region: us-east-1
        rules:
          - proto: tcp
            ports: ["22", "80"]
            cidr_ip: 0.0.0.0/0

    - name: Launch instance
      amazon.aws.ec2_instance:
        key_name: "ansible-key"
        instance_type: t2.micro
        image_id: ami-0c55b159cbfafe1f0
        security_groups: "ansible-sg"
        vpc_subnet_id: subnet-12345678
        tags:
          Name: "Ansible-Managed"
        wait: yes
        state: present
```

**Key Considerations:**
- Use **AWS CLI credentials** (`~/.aws/credentials`) or environment variables.
- Tag instances for inventory management.
- Enable **SSH key rotation** via `user_data`.

---

### **3. CI/CD Integration (GitHub Actions Webhook)**
**Use Case:** Trigger an Ansible playbook on code push.
**Example Webhook Playbook:**
```yaml
---
- name: Handle GitHub Actions webhook
  hosts: localhost
  gather_facts: no
  vars:
    webhook_token: "{{ lookup('env', 'WEBHOOK_TOKEN') }}"
  tasks:
    - name: Verify webhook signature
      assert:
        that:
          - request.headers['X-Hub-Signature'] == "sha1={{ sha1(github_payload | hash('sha1') + webhook_token) }}"
        fail_msg: "Invalid webhook signature"

    - name: Run playbook based on event
      include_tasks: "{{ github_payload['action'] }}.yml"
      when: "'push' in github_payload['action']"
```

**Key Considerations:**
- Use `async_task` for long-running jobs.
- Validate payloads with `json_query`.
- Store secrets in **GitHub Actions secrets**.

---

### **4. Event-Driven Automation (MQTT Pub/Sub)**
**Use Case:** Subscribing to IoT sensor data.
**Example Playbook:**
```yaml
---
- name: MQTT Sensor Data Processor
  hosts: localhost
  tasks:
    - name: Subscribe to MQTT topic
      mqtt_subscribe:
        topic: "sensors/#"
        qos: 1
        username: "{{ mqtt_user }}"
        password: "{{ mqtt_pass }}"
        will_topic: "sensors/offline"
        will_message: "offline"
        will_retain: yes
      register: mqtt_sub

    - name: Process sensor data
      mqtt_publish:
        topic: "sensors/{{ item.data.topic.split('/')[1] }}/action"
        payload: "{{ item.data.payload }}"
        retain: no
      loop: "{{ mqtt_sub.messages }}"
```

**Key Considerations:**
- Use `emqx` or `Mosquitto` for MQTT brokers.
- Handle **reconnects** with retries.
- Persist state to avoid duplicate processing.

---

### **5. Dynamic Inventory (AWS EC2 Discovery)**
**Use Case:** Auto-updating inventory from AWS.
**Example Script (`aws_ec2_dynamic_inventory.py`):**
```python
#!/usr/bin/env python3
import boto3
import json
import argparse

def get_aws_inventory():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'tag:Ansible-Managed', 'Values': ['true']}])
    inventory = []
    for instance in instances.all():
        inventory.append({
            'hostname': instance.public_dns_name,
            'groups': ['webservers', instance.tags.get('Environment', 'dev')],
            'ansible_host': instance.public_ip_address,
            'ansible_user': 'ec2-user'
        })
    return inventory

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    if args.list:
        print(json.dumps({'all_hosts': {'hosts': get_aws_inventory()}}))
```

**Key Considerations:**
- Cache inventory to avoid API throttling.
- Use **AWS IAM roles** for credentials.
- Validate tags for grouping.

---

## **Common Pitfalls & Best Practices**
### **⚠️ Pitfalls**
1. **Tight Coupling:** Avoid hardcoding API endpoints or credentials. Use **variables** (`vars_files`) or **vault**.
2. **No Error Handling:** Always validate API responses (e.g., `failed_when: response.status != 200`).
3. **Idempotency:** Ensure playbooks can rerun without unintended changes.
4. **Secret Management:** Never hardcode passwords. Use **Ansible Vault** or **HashiCorp Vault**.
5. **Performance:** Minimize API calls in loops. Use `delegate_to: localhost` for API-heavy tasks.

### **✅ Best Practices**
1. **Modular Design:** Split playbooks into **roles** for reusability.
   ```yaml
   - name: Include common tasks
     include_role:
       name: common_tasks
       tasks_from: api_auth.yml
   ```
2. **Idempotency:** Use `state: present/absent` for resource modules.
3. **Logging:** Enable `verbose: yes` during debugging.
4. **Testing:** Use `molecule` for automated playbook validation.
5. **Documentation:** Annotate playbooks with `# @group Integration` for clarity.

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                 | **Use Case Example**                          |
|---------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **[Role-Based Access Control (RBAC)]** | Designate permissions for users/teams in Ansible Tower/AWX.                   | Restrict access to `prod` infrastructure.    |
| **[Workflow Orchestration]**          | Chain multiple playbooks using `workflows` or `ansible-navigator`.          | Multi-stage deployments (build → test → prod). |
| **[Configuration as Code (IaC)]**    | Manage infrastructure via Ansible + Terraform/Pulumi.                       | Spin up Kubernetes clusters.                 |
| **[Observability Integration]**       | Log and monitor Ansible runs with Prometheus/Grafana.                      | Track playbook execution duration.           |
| **[GitOps for Ansible]**              | Sync Ansible playbooks via Git (e.g., ArgoCD, Flux).                        | Automate compliance checks.                  |

---

## **Further Reading**
- [Ansible API Documentation](https://docs.ansible.com/ansible/latest/collections/index.html)
- [AWS Ansible Modules](https://docs.aws.amazon.com/powershell/latest/userguide/pt_aws_ansible.html)
- [MQTT with Ansible](https://docs.ansible.com/ansible/latest/collections/community/mqtt/index.html)
- [GitHub Actions Webhooks](https://docs.github.com/en/developers/webhooks-and-events)