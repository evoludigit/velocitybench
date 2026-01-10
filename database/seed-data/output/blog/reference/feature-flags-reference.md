# **[Pattern] Feature Flags & Progressive Rollout – Reference Guide**

---

## **1. Overview**
**Feature Flags & Progressive Rollout** enables controlled deployment of experimental or incomplete code to production without immediate user exposure. This pattern allows incremental testing, rollout validation, and gradual adoption while minimizing risk. Unlike traditional deployment methods (e.g., blue-green), feature flags decouple code availability from user access, enabling:
- **A/B testing** of new features
- **Canary releases** (gradual rollouts)
- **Dark launching** (testing in production without user visibility)
- **Rollback capabilities** in case of failures

By embedding feature flags (boolean switches) in code, teams can:
✔ Deploy changes without version bumps or downtime.
✔ Measure impact (e.g., metrics, user feedback) before full release.
✔ Target specific user segments (e.g., feature toggles by region, role, or device).

---

## **2. Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                  |
|------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Feature Flag**       | A runtime switch to enable/disable code paths.                                | `enable_new_ui` flag toggles a redesign.      |
| **Progressive Rollout**| Gradual exposure to users (e.g., 1% → 10% → 100%).                           | Roll out a checkout flow to 5% of traffic.   |
| **Flag Provider**      | Backend service (e.g., LaunchDarkly, Unleash) storing flag configurations.    | `FlagService.getFlag("feature_x")`.          |
| **Client-Side Flag**   | Flags evaluated in the browser/app (reduces latency).                         | JavaScript SDK checks `window.enable_flag`.   |
| **Server-Side Flag**   | Flags evaluated on the backend (secure for sensitive logic).                  | Node.js app calls `/api/flags?feature=payments`. |
| **Fallback Value**     | Default behavior if the flag’s value isn’t available (e.g., `false`).          | Disable a feature if the flag API fails.     |
| **Targeting Rules**    | Conditions to control who sees the feature (e.g., user ID, attributes).       | Only users with `is_premium=true` see X.    |
| ** Experiments**       | Structured A/B tests with flag-based traffic splitting.                       | Route 30% of users to the new dashboard.    |

---

## **3. Schema Reference**
Below are common data structures for implementing feature flags.

### **3.1 Flag Schema (Backend Storage)**
| Field               | Type          | Description                                                                 | Example Value                     |
|---------------------|---------------|-----------------------------------------------------------------------------|------------------------------------|
| `flagKey`           | `string`      | Unique identifier for the flag (e.g., `new_payments_ui`).                   | `"payments_v2"`                    |
| `defaultValue`      | `boolean`     | Fallback if flag isn’t found (default: `false`).                           | `false`                            |
| `variation`         | `any`         | Custom payload (e.g., `{"color": "red"}`).                                 | `{"theme": "dark"}`                |
| `targetingRules`    | `array`       | Conditions to evaluate (see [Targeting Rules](#targeting-rules)).           | `[{ "key": "user.role", "op": "==", "value": "admin" }]` |
| `trafficAllocation` | `object`      | Percentages for progressive rollouts.                                       | `{ "canary": 5, "beta": 20, "all": 75 }` |
| `createdAt`         | `timestamp`   | When the flag was created.                                                  | `2023-10-01T00:00:00Z`            |
| `expiryDate`        | `timestamp`   | When the flag auto-disables (optional).                                     | `2024-01-01T00:00:00Z`            |
| `environments`      | `array`       | Environments where the flag applies (e.g., `["prod", "staging"]`).          | `["production"]`                   |

---

### **3.2 Targeting Rules Schema**
| Field  | Type     | Description                                                                 | Example                          |
|--------|----------|-----------------------------------------------------------------------------|----------------------------------|
| `key`   | `string` | User attribute to check (e.g., `country`, `device.type`).                  | `"user.country"`                  |
| `op`    | `string` | Comparison operator (`==`, `!=`, `>`, `in`).                               | `"=="`                           |
| `value` | `any`    | Value to compare against (e.g., `"US"`, `20`).                             | `"en"`                           |
| `match` | `boolean`| If `true`, user matches the rule; if `false`, they’re excluded.            | `true` (default)                 |

**Example Rule:**
```json
{
  "key": "user.device.type",
  "op": "==",
  "value": "mobile",
  "match": true
}
```
*(Applies the flag only to mobile users.)*

---

### **3.3 Progressive Rollout Schema**
| Field              | Type     | Description                                                                 | Example                     |
|--------------------|----------|-----------------------------------------------------------------------------|-----------------------------|
| `rolloutId`        | `string` | Unique identifier for the rollout.                                           | `"payments_v2_rollout_1"`    |
| `phase`            | `string` | Current phase (e.g., `canary`, `beta`, `full`).                             | `"canary"`                   |
| `percentage`       | `number` | % of traffic to expose (0–100).                                            | `10`                         |
| `startTime`        | `timestamp` | When the phase began.                                                  | `2023-10-02T09:00:00Z`       |
| `endTime`          | `timestamp` | When the phase ends (auto-advances to next).                          | `2023-10-03T09:00:00Z`       |
| `metrics`          | `object` | KPIs to monitor (e.g., `errorRate`, `conversion`).                         | `{ "errorRate": { "target": 0.05 } }` |

---
## **4. Implementation Patterns**
### **4.1 Client-Side Evaluation (Browser/JS)**
**Purpose:** Reduce backend calls by evaluating flags locally.
**Example (JavaScript):**
```javascript
// Initialize with a flag provider (e.g., LaunchDarkly SDK)
const ld = new LDClient("YOUR_CLIENT_ID", {
  flags: ["new_checkout", "dark_mode"]
});

// Evaluate a flag with user context
const isFeatureEnabled = ld.variation("new_checkout", {
  user: {
    id: "user123",
    country: "US",
    isPremium: true
  }
}, false); // Fallback: false

if (isFeatureEnabled) {
  // Enable new checkout UI
  renderNewCheckout();
}
```

**Key Methods:**
| Method               | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `variation(key, ctx, fallback)` | Returns the flag’s value (`true`/`false`) or custom variation.           |
| `variationDetail(key, ctx)`      | Returns flag metadata (e.g., `variation`, `lastChangedAt`).               |
| `identify(userId, attributes)`  | Associates user attributes for targeting.                                   |

---

### **4.2 Server-Side Evaluation (Backend)**
**Purpose:** Securely evaluate flags for sensitive logic (e.g., payments).
**Example (Node.js/Express):**
```javascript
const express = require('express');
const app = express();

// Mock flag service (replace with LaunchDarkly/Unleash client)
const flagService = {
  getFlag: async (flagKey, userContext) => {
    // Fetch from a database or external API
    return { enabled: true, variation: { theme: "dark" } };
  }
};

app.get('/api/checkout', async (req, res) => {
  const user = { id: req.user.id, role: "admin" };
  const flag = await flagService.getFlag("new_checkout", user);

  if (flag.enabled) {
    return res.json({ ui: "v2", ...flag.variation });
  }
  res.json({ ui: "v1" });
});
```

**Best Practices:**
- Cache flag responses (e.g., Redis) to avoid repeated calls.
- Use middleware to inject flag evaluations into requests.

---

### **4.3 Progressive Rollout Logic**
**Purpose:** Gradually expose features to user segments.
**Example (Pseudocode):**
```python
def should_expose_to_user(user, flag_key):
    rollout = get_rollout_config(flag_key, user.segment)  # e.g., "canary"
    random_value = random.uniform(0, 100)  # 0–100

    if random_value <= rollout.percentage:
        return True
    return False
```

**Common Rollout Strategies:**
1. **Canary:** Expose to 1–5% of traffic (e.g., using a hash of `user.id`).
2. **Beta:** Gradual increase (e.g., 10% → 30% → 100%).
3. **Geographic:** Target by region (e.g., US first, then EU).
4. **Time-Based:** Roll out at specific hours (e.g., 9 AM PST).

---

## **5. Query Examples**
### **5.1 Evaluating a Flag (Client-Side)**
**Request:**
```javascript
// Check if "dark_mode" is enabled for user "alice"
const isDarkModeOn = ld.variation("dark_mode", {
  user: { id: "alice", prefersDarkMode: true }
}, false);
```

**Response:**
```json
true // Flag is enabled for "alice"
```

---

### **5.2 Fetching Flag Metadata (Server-Side)**
**Request (gRPC/API):**
```http
GET /api/flags?key=payments_v2&user.id=user123&user.role=admin
```

**Response:**
```json
{
  "flagKey": "payments_v2",
  "enabled": true,
  "variation": { "paymentMethod": "crypto" },
  "trafficAllocation": { "canary": 5, "all": 95 },
  "lastChangedAt": "2023-10-01T12:00:00Z"
}
```

---

### **5.3 Updating a Progressive Rollout**
**Request (Backend API):**
```http
POST /api/flags/payments_v2/rollout/canary/percentage
Headers: { "Authorization": "Bearer API_KEY" }
Body:
{
  "newPercentage": 10,
  "endTime": "2023-10-03T00:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "rollout": {
    "phase": "canary",
    "percentage": 10,
    "usersExposed": 500 // Approximate
  }
}
```

---

## **6. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|-------------------------------------------------|
| **[Canary Deployments](#)**      | Gradually deploy to a subset of servers/users to monitor performance.          | High-traffic systems (e.g., databases).         |
| **[Feature Toggles](#)**         | General-purpose runtime feature control (simpler than progressive rollouts).   | Quick experiments or organization-wide flags.  |
| **[A/B Testing](#)**             | Compare two variants (e.g., UI vs. UX) using flag-based traffic splitting.    | Hypothesis-driven product improvements.         |
| **[Shadow Release](#)**          | Deploy code but hide it from users (e.g., for testing).                      | Dark launches or performance testing.            |
| **[Blue-Green Deployment](#)**   | Switch traffic between identical environments (no feature flags).             | Zero-downtime releases for major version bumps.  |
| **[Config as Code](#)**          | Manage feature flags via version-controlled configs (e.g., YAML/JSON).        | Infrastructure-as-code (IaC) workflows.          |

---
## **7. Anti-Patterns & Pitfalls**
| **Anti-Pattern**               | **Risk**                                                                       | **Mitigation**                                  |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------|
| **Overusing Flags**             | Code becomes unmaintainable ("flag soup").                                    | Limit to experimental/incremental features.      |
| **No Fallback Logic**           | Features break silently if flags fail to load.                                | Always provide defaults (e.g., `false`).         |
| **Ignoring Rollback Strategies**| Long recovery times during failures.                                         | Document rollback commands (e.g., disable flags).|
| **Hardcoding Flag Keys**        | Refactoring becomes error-prone.                                             | Use constants or DI (Dependency Injection).     |
| **Bypassing Flags in Prod**     | "It works for me!" syndrome undermines testing.                              | Enforce flag checks in CI/CD.                   |

---
## **8. Tools & Libraries**
| **Tool/Library**       | **Type**               | **Use Case**                                      | **Link**                                  |
|------------------------|------------------------|---------------------------------------------------|-------------------------------------------|
| **LaunchDarkly**       | SaaS/Client-SDK        | Enterprise-grade feature flags with A/B testing.  | [launchdarkly.com](https://launchdarkly.com) |
| **Unleash**            | Self-Hosted/Open Source| Lightweight flag management with targeting rules.  | [getunleash.io](https://getunleash.io)     |
| **Flagsmith**          | SaaS/Open Source       | Developer-friendly with visual flag management.    | [flagsmith.com](https://flagsmith.com)    |
| **Flagged**            | Self-Hosted            | Simple Redis-backed flag service.                 | [flagged.tech](https://flagged.tech)      |
| **Flagger (Kubernetes)** | CNCF Project          | Canary deployments for Kubernetes workloads.      | [github.com/flagger](https://github.com/flagger) |

---
## **9. Example Workflow: Progressive Rollout**
1. **Deploy Code:**
   ```bash
   # Git commit: "feat: add dark mode toggle"
   git commit -m "feat: add dark mode feature flag"
   git push origin main
   ```
   *(Deploy to production without exposing the flag.)*

2. **Configure Flag (LaunchDarkly):**
   - Create flag `dark_mode` with `defaultValue: false`.
   - Set targeting rules: `user.preferences.darkMode == true`.
   - Configure rollout: 1% → 5% → 100% over 7 days.

3. **Monitor Impact:**
   - Track metrics (e.g., "dark_mode_usage" in Analytics).
   - Use LaunchDarkly’s dashboard to adjust percentages.

4. **Release Fully:**
   ```bash
   # Toggle flag permanently
   curl -X PUT "https://app.launchdarkly.com/api/v2/flags/dark_mode" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -d '{"variation":true}'
   ```

---
## **10. Key Takeaways**
- **Decouple Deployment from Release:** Ship features early, expose them later.
- **Target Precise Segments:** Use user attributes (e.g., `role`, `device`) for control.
- **Monitor & Iterate:** Track metrics to justify full releases.
- **Avoid Flag Fatigue:** Clean up unused flags regularly.
- **Combine with Other Patterns:** Pair with canary deployments or A/B testing for safety.

---
**See also:**
- [Feature Toggle Anti-Patterns](https://martinfowler.com/bliki/FeatureToggle.html)
- [Progressive Delivery at Scale (Gartner)](https://www.gartner.com/en/documents/3995522)