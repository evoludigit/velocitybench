---
# **[Pattern] Jenkins Pipelines Integration Patterns – Reference Guide**

---

## **Overview**
Jenkins Pipelines enable scalable, reproducible, and declarative automation workflows using Domain-Specific Language (DSL) scripts. This reference guide outlines **integration patterns** for Jenkins Pipelines, focusing on modularity, extensibility, and common interaction flows with external systems, repositories, and tools.

The guide covers:
✔ **Core pipeline types** (Scripted vs. Declarative)
✔ **Integration with SCMs, artifact repositories, and CI/CD tools**
✔ **Best practices for dynamic inputs, reusable libraries, and parallel execution**
✔ **Handling errors, retries, and failure scenarios**
✔ **Security considerations (credentials, secrets, and isolation)**

---

## **Schema Reference**
Below is a structured breakdown of key integration patterns and their components:

| **Integration Pattern**          | **Purpose**                                                                 | **Core Components**                                                                                                                                                                                                 | **Example Use Case**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Shared Pipeline Libraries**     | Reusable modular code for shared functionality.                            | `Jenkinsfile`, `vars/` (Groovy scripts), `scripts/` (reusable functions), `snippets/` (snippet generator).                                                                                                    | `build.gradle`, `docker-compose.yml` validation across multiple projects.                  |
| **SCM Triggers (Git/GitHub)**    | Automate pipeline execution on code changes.                                | `pollSCM`, `git` plugin, `webhook` (GitHub/GitLab triggers), `Bitbucket Polling`.                                                                                                                             | Deploy `.NET` app on `main` branch push.                                                |
| **Parallel Stages**               | Execute stages concurrently to reduce build time.                          | `stage(name: 'Test') { parallel { stage('Unit') { ... }, stage('Integration') { ... } } }`, resource allocation tools like `kubernetes` plugin.                                                         | Run `unit tests` + `security scans` simultaneously.                                      |
| **Post-Build Artifact Handling**  | Publish/build artifacts post-execution.                                    | `archiveArtifacts`, `publish` (Docker image), `artifactUploader`, `nexus`/`maven-repository`.                                                                                                                    | Push compiled `.jar` to Nexus after build.                                               |
| **Dynamic Workflows (Groovy)**    | Conditional logic based on inputs/environments.                           | `script { steps { if (env.BRANCH == 'prod') { deploy() } } }`, `withEnv`, `when` keyword (Declarative).                                                                                                  | Run `canary deploy` only for `dev` branches.                                            |
| **Credentials Binding**           | Securely inject secrets into pipelines.                                    | `withCredentials`, `bind`, `secretText()`, `secretFile()`, Jenkins Credentials Plugin.                                                                                                                             | Load `DATABASE_PASSWORD` from Vault without hardcoding.                                  |
| **Pipeline as Code (PaC)**        | Version-controlled pipeline definitions.                                   | `Jenkinsfile` (Declarative/Scripted), `Jenkinsfile.d` (custom dir), Git/SCM integration, `Jenkins Shared Libraries`.                                                                                             | Store CI/CD config in Git alongside source code.                                        |
| **Multi-Branch Pipeline**         | Auto-sync pipelines with SCM branches.                                     | `multibranch-scm` plugin, `Jenkinsfile` in each branch, `Branch Indexing`.                                                                                                                                     | Sync `feature/*` branches with respective pipeline configs.                              |
| **External API Calls**           | Trigger/notify external systems (e.g., Slack, Kubernetes).                 | `sh`, `bat`, `curl`, `withCredentials`, `jenkins.model.Jenkins.instance.getItemByFullName`.                                                                                                                          | Notify Slack on build failure via webhook.                                              |
| **Matrix Builds**                 | Run tests across multiple configurations (OS, JDK, etc.).                  | `matrix { axis { label 'linux', label 'windows' }, steps { ... } }`, `parallel` combination.                                                                                                                   | Test app on `Java 8/11` + `Linux/Ubuntu`.                                               |
| **Retry Mechanisms**              | Handle transient failures gracefully.                                      | `retry` (Declarative), `untilSuccess` (Scripted), `waitUntil` (for external APIs).                                                                                                                                | Retry failed `database migrations` up to 3 times.                                       |
| **Pipeline Chaining**             | Trigger downstream pipelines.                                               | `build job: 'downstream', wait: true`, `build upstream: { upstreamJob: 'job-name', parameters: [...] }`.                                                                                                     | Trigger `staging` pipeline after `testing` succeeds.                                   |
| **Infrastructure as Code (IaC)**  | Manage cloud resources dynamically.                                          | `aws` plugin, `terraform`, `kubernetes` plugin, `infrastructure-scm` integration.                                                                                                                               | Deploy Kubernetes manifests via `Helm` in pipeline.                                    |

---

## **Query Examples**
### **1. Shared Pipeline Libraries**
```groovy
@Library('shared-libs') _  // Loads functions from Git repo
def call() {
    deploy(app: 'my-app', env: 'prod')
}
```
**Key Files:**
- `vars/deploy.groovy`
  ```groovy
  def deploy(String app, String env) { ... }
  ```
- `scripts/notify.groovy`
  ```groovy
  def notifyFailure() {
      slackSend(channel: '#dev', message: "Build failed!")
  }
  ```

---

### **2. SCM Trigger (GitHub Webhook)**
```groovy
pipeline {
    agent any
    triggers {
        githubPush()
    }
    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/org/repo.git'
            }
        }
    }
}
```
**GitHub Webhook Setup:**
- **Payload URL:** `http://<Jenkins-IP>/github-webhook/`
- **Secret:** Configured in Jenkins `Credentials`.

---

### **3. Parallel Stages**
```groovy
pipeline {
    agent any
    stages {
        stage('Tests') {
            parallel {
                stage('Unit') { steps { sh 'mvn test' } }
                stage('Integration') {
                    steps { sh 'gradle integrationTest' }
                    when { branch 'main' }  // Only run on main
                }
            }
        }
    }
}
```

---

### **4. Dynamic Workflow (Groovy)**
```groovy
stage('Deploy') {
    steps {
        script {
            def env = env.BRANCH == 'prod' ? 'production' : 'staging'
            deploy(to: env)
        }
    }
}
```

---

### **5. Retry Mechanism**
```groovy
stage('Database Migrations') {
    steps {
        retry(3) {
            sh 'python migrate.py'
        }
    }
}
```

---

### **6. Credentials Binding**
```groovy
stage('Deploy') {
    steps {
        withCredentials([string(credentialsId: 'DB_PASSWORD', variable: 'DB_PASS')]) {
            sh "export DB_PASS=$DB_PASS && ./deploy.sh"
        }
    }
}
```

---

### **7. Multi-Branch Pipeline**
**Directory Structure:**
```
/repo/
├── Jenkinsfile  // Default config
├── /feature-branch/
│   └── Jenkinsfile  // Override
└── /main/
    └── Jenkinsfile
```

---

### **8. External API Call (Slack Notification)**
```groovy
post {
    always {
        script {
            def response = sh(
                script: "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Build ${currentBuild.fullDisplayName} completed\"}' ${env.SLACK_WEBHOOK_URL}",
                returnStdout: true
            ).trim()
        }
    }
}
```

---

### **9. Infrastructure as Code (Terraform)**
```groovy
stage('Deploy Cloud') {
    steps {
        sh '''
            cd infrastructure/terraform
            terraform init
            terraform apply -auto-approve -var="app_name=${env.APP_NAME}"
        '''
    }
}
```

---

## **Best Practices & Pitfalls**
### **✅ Best Practices**
1. **Modularize Code:**
   - Use **Jenkins Shared Libraries** to avoid duplication.
   - Example: Move `notifyFailure()` logic to a shared library.

2. **Secure Secrets:**
   - Always use `withCredentials` or **Jenkins Credentials Plugin**.
   - Avoid hardcoding tokens in `Jenkinsfile`.

3. **Parallelize Stages:**
   - Offload independent steps (e.g., tests, security scans) to `parallel` blocks.

4. **Idempotency:**
   - Design deployments to handle retries (e.g., Terraform `apply` with `-auto-approve`).

5. **Dynamic Environments:**
   - Use `env.BRANCH` or `params` to conditionally trigger stages.

6. **Monitor Failures:**
   - Use `post { always { ... } }` to notify teams on failures/retries.

7. **Version Control:**
   - Store `Jenkinsfile` in SCM (Git) for traceability.

---

### **❌ Common Pitfalls**
| **Pitfall**                          | **Risk**                                                                 | **Mitigation**                                                                                     |
|--------------------------------------|--------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Hardcoding secrets in `Jenkinsfile`  | Credential leaks, compliance violations.                               | Use `withCredentials` or **Vault integration**.                                                  |
| Monolithic pipelines                 | Slow builds, hard to maintain.                                          | Split into modular libraries/stages.                                                               |
| No retries for flaky steps           | Builds fail on transient errors (e.g., network timeouts).               | Wrap steps in `retry` or `untilSuccess`.                                                         |
| Overusing `script` blocks            | Reduces readability in Declarative pipelines.                           | Prefer Declarative keywords (`steps`, `when`) over `script { ... }`.                              |
| Ignoring resource allocation         | Stages block each other due to shared agents.                           | Use `kubernetes` plugin or `label` constraints for parallel execution.                             |
| No error handling                    | Silent failures or undefined behavior.                                  | Use `try-catch` or `catchError` in Scripted pipelines.                                            |
| Dynamic paths not validated           | `sh "ls /dynamic/path"` may fail.                                      | Prefer `dir` or `mkdir` steps to ensure paths exist.                                             |
| Long-running pipelines               | Jenkins agent resource exhaustion.                                       | Split into smaller jobs or use **resource pools**.                                                |

---

## **Related Patterns**
For deeper integration, explore these complementary patterns:

| **Pattern**                          | **Purpose**                                                                 | **Link/Reference**                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Jenkins Blue Ocean**               | Modern UI for pipeline visualization.                                       | [Jenkins Blue Ocean Docs](https://bintray.com/blueocean/blueocean-plugin)          |
| **Jenkins Agent Provisioning**       | Dynamic agent scaling (Kubernetes, Docker).                                | [Agent Provisioners Plugin](https://plugins.jenkins.io/agent-provisioner/)        |
| **Jenkins Pipeline UX Plugin**       | UI for debugging pipelines.                                                 | [Pipeline UX Plugin](https://plugins.jenkins.io/pipeline-ux/)                       |
| **GitHub Actions Integration**       | Hybrid GitHub Actions + Jenkins workflows.                                  | [GitHub Actions Plugin](https://plugins.jenkins.io/github/)                         |
| **Terraform + Jenkins**              | IaC provisioning in pipelines.                                             | [Terraform Plugin](https://plugins.jenkins.io/terraform/)                           |
| **Slack Notifications**              | Real-time build status alerts.                                             | [Slack Plugin](https://plugins.jenkins.io/slack/)                                     |
| **Jenkinsfile Validation**           | Catch syntax errors early (pre-commit hooks).                              | [Jenkinsfile Validator](https://github.com/jenkins-python/jenkinsfile-validator)    |

---

## **Further Reading**
- [Official Jenkins Pipeline Docs](https://www.jenkins.io/doc/book/pipeline/)
- [Declarative Pipeline Tutorial](https://www.jenkins.io/doc/book/pipeline/syntax/#declarative-pipeline)
- [Shared Library Guide](https://github.com/jenkinsci/library-plugin)
- [Kubernetes Plugin](https://plugins.jenkins.io/kubernetes/) for dynamic agents.

---
**Last Updated:** `[Insert Date]`
**Version:** `1.0`