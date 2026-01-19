```markdown
---
title: "Fraisier Webhook: Building an Event-Driven Deployment Pipeline"
date: 2023-11-15
tags: ["Backend Engineering", "DevOps", "Continuous Deployment", "API Design", "Webhooks"]
description: "Learn how to implement the Fraisier webhook pattern for automatic, event-driven deployments triggered by Git push events."
---

# **Fraisier Webhook: The Event-Driven Deployment Pipeline**

Automating deployments is a cornerstone of modern DevOps. Yet, many systems still rely on manual triggers, error-prone scripts, or inflexible CI/CD pipelines. This is where **Fraisier Webhook**—a pattern for event-driven deployments—comes into play.

Fraisier is a webhook-based system that listens for Git push events from providers like GitHub, GitLab, Gitea, and Bitbucket. When a push occurs on a mapped branch, the webhook automatically routes the deployment to the correct **fraise** (a microservice/environment) without manual intervention. This approach eliminates bottlenecks, reduces human error, and ensures seamless deployments across distributed systems.

In this post, we’ll explore:
- The pain points of manual deployments
- How Fraisier resolves them with webhooks
- A **practical implementation** in Go (though adaptable to other languages)
- Common pitfalls and best practices

---

## **The Problem: Why Manual Deployments Fail**

Manual deployments are slow, inconsistent, and prone to errors. Consider this typical workflow:

1. A developer pushes code to a branch (e.g., `feature/login`).
2. A teammate manually runs SSH commands to trigger deployments on multiple services.
3. The deployment may fail silently or require multiple retries.
4. No audit trail exists to trace what triggered the deployment.

This approach scales poorly:
- **No automatic routing**: You must hardcode which services depend on which branches.
- **No security checks**: Unauthorized webhooks can trigger deployments.
- **No failover handling**: Missed webhooks or rate limits break the pipeline.
- **No observability**: Unclear what changes triggered a deployment.

Enter **Fraisier Webhook**—a solution that turns Git push events into automated, secure, and observable deployments.

---

## **The Solution: Event-Driven Deployments with Webhooks**

Fraisier replaces manual triggers with a **webhook server** that:
1. Listens for Git provider events (pushes, PRs, merges).
2. Validates the webhook’s origin (using HMAC signatures).
3. Maps branches to target environments (fraises).
4. Executes deployments via CLI scripts or API calls.

### **Key Components**
| Component          | Responsibility                                                                 |
|--------------------|-------------------------------------------------------------------------------|
| **Webhook Server** | Receives HTTP POSTs from Git providers like GitHub/GitLab.                     |
| **Signature Verification** | Ensures the webhook is genuine (prevents spoofing).                       |
| **Branch Mapping** | Routes deployments to the right fraise (e.g., `main → production`, `dev → staging`). |
| **Event Parser**  | Normalizes different Git provider webhook formats (GitHub vs. GitLab).       |
| **Deployment Executor** | Runs deployment scripts (Docker, Ansible, Kubernetes, etc.).               |

---

## **Implementation Guide: Building Fraisier in Go**

Let’s build a **minimal Fraisier webhook server** in Go. We’ll use:
- `github.com/gin-gonic/gin` (HTTP router)
- `github.com/gojwt/jwt` (signature verification)
- Environment variables for config

### **1. Set Up the Server**

```go
package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()

	// Webhook endpoint
	r.POST("/webhook", webhookHandler)

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("Server running on port %s", port)
	log.Fatal(r.Run(":" + port))
}
```

### **2. Parse GitHub Webhooks (Example)**

GitHub sends JSON payloads like this:
```json
{
  "ref": "refs/heads/main",
  "head_commit": { "id": "abc123", "message": "Fix login bug" },
  "repository": { "full_name": "org/repo" }
}
```

Our handler parses and validates it:

```go
type GitHubEvent struct {
	Ref     string `json:"ref"`
	HeadCommit struct {
		ID      string `json:"id"`
		Message string `json:"message"`
	} `json:"head_commit"`
	Repository struct {
		FullName string `json:"full_name"`
	} `json:"repository"`
}

func webhookHandler(c *gin.Context) {
	var event GitHubEvent
	if err := c.ShouldBindJSON(&event); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid payload"})
		return
	}

	// Verify signature (GitHub sends 'X-Hub-Signature-256')
	sig := c.GetHeader("X-Hub-Signature-256")
	if !verifySignature(c.Request.Body, sig) {
		c.AbortWithStatus(http.StatusUnauthorized)
		return
	}

	// Map branch to fraise
	commitRef := extractBranch(event.Ref)
	fraise := branchToFraise(commitRef)

	// Execute deployment
	if err := deploy(fraise); err != nil {
		log.Printf("Deployment failed for %s: %v", fraise, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "deployment failed"})
	} else {
		c.JSON(http.StatusOK, gin.H{"message": "deployed", "fraise": fraise})
	}
}
```

### **3. Verify Webhook Signatures**

GitHub/GitLab provide HMAC signatures to prevent spoofing:

```go
import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
)

func verifySignature(body io.Reader, signature string) bool {
	secret := os.Getenv("GITHUB_WEBHOOK_SECRET") // e.g., "abc123"
	expected := "sha256=" + hmac.New(sha256.New, []byte(secret)).Sum(body).Hash()

	return hmac.Equal([]byte(expected), []byte(signature))
}
```

### **4. Branch-to-Fraise Mapping**

Define rules like:
- `main` → `production`
- `dev` → `staging`
- `feature/*` → `test`

```go
func branchToFraise(branch string) string {
	switch branch {
	case "refs/heads/main":
		return "production"
	case "refs/heads/dev":
		return "staging"
	default:
		return "test" // Default
	}
}
```

### **5. Deploy to a Fraise**

Trigger a deployment via a CLI script (e.g., `deploy.sh`):

```bash
#!/bin/bash
FRAISE=$1
git pull origin main
docker-compose -p $FRAISE up -d --build
```

Call it from Go:

```go
func deploy(fraise string) error {
	cmd := exec.Command("sh", "./deploy.sh", fraise)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("deployment failed: %s", string(output))
	}
	return nil
}
```

---

## **Common Mistakes to Avoid**

1. **Ignoring Signature Verification**
   - Always validate webhooks. Without it, attackers can trigger deployments.
   - Use GitHub/GitLab’s `X-Hub-Signature-*` headers.

2. **Assuming All Providers Use the Same Format**
   - GitHub, GitLab, and Bitbucket have different payload schemas.
   - Normalize events into a unified format (e.g., `event.Branch`, `event.Commit`).

3. **Hardcoding Fraise Mappings**
   - Use a config file (YAML/JSON) for branch-to-fraise rules:
     ```yaml
     branches:
       main: production
       dev: staging
     ```

4. **No Error Handling for Rate Limits**
   - Git providers throttle webhooks. Add retries or dead-letter queues.

5. **No Logging/Audit Trail**
   - Log deployments with commit IDs for debugging:
     ```go
     log.Printf("Deployed %s from commit %s", fraise, event.HeadCommit.ID)
     ```

6. **Silent Failures**
   - Always return HTTP errors (e.g., `500` if deployment fails).

---

## **Key Takeaways**
✅ **Eliminate Manual Triggers** – Automate with webhooks.
✅ **Secure with Signatures** – Prevent spoofed events.
✅ **Normalize Event Parsing** – Handle GitHub/GitLab differences.
✅ **Map Branches to Fraises** – Use config for flexibility.
✅ **Log Everything** – Debug deployments via commit IDs.
✅ **Fail Fast** – Return errors instead of silently failing.

---

## **Conclusion**

Fraisier Webhook provides a **scalable, secure, and observable** way to automate deployments. By leveraging Git push events and branching rules, you can:
- Reduce human errors
- Speed up releases
- Improve traceability

Start small (a single GitHub webhook) and expand to multiple providers. For production use, consider:
- Adding a **queue system** (RabbitMQ, Kafka) for reliability.
- Using **Kubernetes operators** for containerized fraises.
- Integrating with **logging systems** (ELK, Datadog).

Would you like a follow-up post on scaling Fraisier with Kubernetes? Let me know!

---
**Further Reading:**
- [GitHub Webhooks API](https://docs.github.com/en/webhooks)
- [GitLab Webhook Documentation](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [Event-Driven Architecture Patterns](https://www.oreilly.com/library/view/event-driven-architecture/9781491950397/)
```