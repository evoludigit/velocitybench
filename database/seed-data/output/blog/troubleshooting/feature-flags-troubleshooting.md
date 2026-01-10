# **Debugging Feature Flags & Progressive Rollout: A Troubleshooting Guide**

## **Introduction**
The **Feature Flags & Progressive Rollout (FRP)** pattern enables decoupling code deployment from feature release, allowing safe experimentation, A/B testing, and controlled rollouts. However, misconfigurations, debugging challenges, or scalability issues can arise.

This guide focuses on **quick resolution** of common problems in FRP implementations.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| Symptom | Description |
|---------|-------------|
| **Feature not toggling** | Flags ignored, code path skipped or fully active. |
| **Rollout percentages misconfigured** | Wrong % of users see a feature. |
| **Flag evaluation too slow** | High latency in feature flag checks. |
| **Flag cache inconsistencies** | Flags not updating across services. |
| **Feature not A/B tested** | No clear segmentation (e.g., users vs. groups). |
| **Rollback fails** | Feature cannot be disabled post-deploy. |
| **Flag service unavailable** | 3rd-party flagging service (e.g., LaunchDarkly) crashes. |
| **Feature drift** | Code assumes flag exists but fails when toggled off. |

---

## **2. Common Issues & Fixes (with Code)**

### **2.1. Feature Flag Not Working (Silently Ignored)**
**Symptom:** No error, but the feature behaves as if unset.

**Root Causes & Fixes:**
| Cause | Solution | Example Fix |
|-------|----------|-------------|
| **Flag name misspelled** | Check flag name in config and code. | ```javascript
// Correct:
const isFeatureEnabled = flags.isNewDashboardEnabled;

// Bad:
const isFeatureToggled = flags.isNewDashboardToggled; // Won't match
``` |
| **Flag SDK not initialized** | Ensure flag client is loaded before use. | ```javascript
// Initialize early (e.g., in app startup):
import { init } from 'featureflags';
init({ serviceUrl: 'https://flags.example.com' });

// Then check:
const isFeatureActive = flags.isNewFeature;
``` |
| **Flag environment mismatch** | Flags may vary by environment (dev/staging/prod). | ```json
// Config (e.g., LaunchDarkly):
{
  "feature_flags": {
    "NEW_DASHBOARD": {
      "targeting_key": "ENVIRONMENT",
      "rules": [
        { "key": "production", "variation": 1 }
      ]
    }
  }
}
``` |

---

### **2.2. Rollout Percentages Not Applying**
**Symptom:** Too many users see a feature, or none do.

**Root Causes & Fixes:**

| Cause | Solution | Example Fix |
|-------|----------|-------------|
| **Incorrect flag variation** | Some flag services use `variations` (e.g., 0=false, 1=true). | ```javascript
// LaunchDarkly rule (JSON):
{
  "on": {
    "variation": 1, // Active for 100%?
    "segments": { "users": { "rollout": 20 } }
  }
}
``` |
| **Segmentation error** | Wrong user/group assigned to rollout. | ```javascript
// Check user attributes in flag service:
{
  "key": "userId123",
  "attributes": { "user_type": "gold" },
  "segments": {
    "gold_users": { "rollout": 50 }
  }
}
``` |
| **Cache stale** | Flags not refreshing due to caching. | ```javascript
// Force refresh (if using LaunchDarkly):
flags.flush().then(() => {
  console.log("Flags updated:", flags.isNewFeature);
});
``` |

---

### **2.3. High Latency in Flag Checks**
**Symptom:** App hangs when evaluating flags.

**Root Causes & Fixes:**

| Cause | Solution | Example Fix |
|-------|----------|-------------|
| **No client-side caching** | Flag service called on every request. | ```javascript
// Enable caching in SDK:
init({
  evaluate: (flagKey, user) => {
    const cached = flagsCache.get(flagKey);
    if (cached) return cached;
    // Fallback to remote call if needed
  }
});
``` |
| **Over-fetching flags** | Loading all flags instead of just needed ones. | ```javascript
// Only fetch necessary flags:
flags.on('ready', (flags) => {
  const isFeatureActive = flags.isNewFeature; // No extra work
});
``` |
| **Network issues** | Flag service API too slow. | ```javascript
// Fallback to local config if online:
const fallbackFlags = {
  NEW_FEATURE: process.env.NODE_ENV === 'development'
};
``` |

---

### **2.4. Flag Cache Inconsistencies**
**Symptom:** Flags updated in one service but not another.

**Root Causes & Fixes:**

| Cause | Solution | Example Fix |
|-------|----------|-------------|
| **No sync mechanism** | Local caches not updated. | ```javascript
// Use a shared cache (Redis, Memcached):
const redis = require('redis');
const client = redis.createClient();

async function getFlag(flagName) {
  const cached = await client.get(`flag:${flagName}`);
  if (cached) return JSON.parse(cached);
  // Fetch from remote if not cached
}
``` |
| **Time skew** | Servers have misaligned clocks. | ```javascript
// Use NTP for synchronization:
const ntpSync = require('ntp-sync');
await ntpSync.syncTime();
``` |

---

### **2.5. Cannot A/B Test Properly**
**Symptom:** No clear control over test groups.

**Root Causes & Fixes:**

| Cause | Solution | Example Fix |
|-------|----------|-------------|
| **No user segmentation** | All users in one bucket. | ```javascript
// Define user groups in flag service:
{
  "segments": {
    "test_group": {
      "variation": 1,
      "rollout": 15
    }
  }
}
``` |
| **Manual overrides not working** | Admins cannot force enable/disable. | ```javascript
// Enable admin override in SDK:
init({
  override: {
    userId: "admin123",
    overrides: { NEW_FEATURE: true }
  }
});
``` |

---

### **2.6. Rollback Fails**
**Symptom:** Feature cannot be disabled after deployment.

**Root Causes & Fixes:**

| Cause | Solution | Example Fix |
|-------|----------|-------------|
| **Flag not set to "off"** | Default should disable feature. | ```javascript
// Default to false in config:
const isFeatureEnabled = flags.isNewFeature || false; // Safe fallback
``` |
| **Hardcoded logic** | Code ignores flag. | ```javascript // ❌ Bad:
if (isNewFeature()) { ... } // ❌ Assumes flag is true

// ✅ Safe:
if (flags.isNewFeature) { ... }
``` |
| **No rollback flag** | Missing "emergency disable" flag. | ```json
// Add an override flag:
{
  "FEATURE_DISABLED_FOR_ALL": {
    "default": false,
    "rules": [{
      "key": "admin", "variation": 1
    }]
  }
}
``` |

---

## **3. Debugging Tools & Techniques**
### **3.1. Logging & Monitoring**
- **Log flag evaluations** to verify behavior:
  ```javascript
  flags.on('evaluate', (flagKey, result) => {
    console.log(`Flag ${flagKey} resolved to`, result);
  });
  ```
- **Use APM tools** (New Relic, Datadog) to track flag latency.

### **3.2. Flag Service Dashboard**
- **LaunchDarkly / Flagsmith / Unleash** provide UIs to inspect:
  - Who sees which flags?
  - Rollout percentages.

### **3.3. Unit Testing Flags**
- Mock flag evaluations:
  ```javascript
  // Jest example:
  test('flag forces true', () => {
    const flags = { isNewFeature: true };
    expect(isFeatureEnabled(flags)).toBe(true);
  });
  ```

### **3.4. Distributed Tracing**
- Add tracing to flag checks (OpenTelemetry):
  ```javascript
  const tracer = new Tracer();
  tracer.startSpan('flag-check', async (span) => {
    span.setAttribute('flag', 'NEW_FEATURE');
    const result = flags.isNewFeature;
    span.end();
  });
  ```

---

## **4. Prevention Strategies**
### **4.1. Design Guidelines**
- **Fail-safe defaults:**
  ```javascript
  const isFeatureActive = flags.isNewFeature ?? false;
  ```
- **Avoid "flag soup":** Group related features under one flag.
- **Document flags** in a central repo (e.g., `docs/flags.md`).

### **4.2. Testing & Validation**
- **Pre-deploy checks:**
  ```bash
  # Script to verify all flags resolve correctly
  ./validate-feature-flags.sh
  ```
- **Canary testing:** Roll out flags to 1% of users first.

### **4.3. Observability**
- **Metrics for flag health:**
  ```promql
  # Alert if flag checks take >500ms
  rate(flags_latency_seconds{quantile="0.95"}[5m]) > 0.5
  ```
- **SLOs for feature toggles** (e.g., 99.9% uptime).

### **4.4. Rollout Best Practices**
- **Use nested flags** for granular control:
  ```json
  {
    "FEATURE_X": {
      "default": false,
      "rules": [
        { "key": "group_alpha", "variation": 1, "rollout": 50 }
      ]
    }
  }
  ```
- **Never assume flags are true**—always handle `undefined`.

---

## **Conclusion**
Feature flags are powerful but require **careful configuration and monitoring**. Use this guide to:
✅ Quickly diagnose flag issues.
✅ Optimize performance.
✅ Ensure reliability in rollouts.

**Next Steps:**
- Audit existing flag usage.
- Implement monitoring for flag health.
- Document flag lifecycle (creation → deprecation).

By following these patterns, you’ll minimize downtime and improve release safety.