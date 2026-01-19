# **[Pattern] UI Visual Regression Testing – Reference Guide**

---

## **Overview**
UI Visual Regression Testing (VRT) is an automated process that detects unintended visual changes between snapshots of a UI—such as layouts, colors, or typography—ensuring consistency across environments, browsers, devices, or over time. This pattern helps teams maintain design integrity by catching unintentional regressions early in the development cycle, reducing manual visual QA effort.

Key use cases include:
- **Cross-browser/device testing** (e.g., Chrome vs. Safari, desktop vs. mobile).
- **Design system consistency** (e.g., UI libraries or component updates).
- **CI/CD pipeline integration** (e.g., automatic failures on snapshots drift).
- **A/B testing validation** (e.g., comparing variant designs).

VRT is complementary to unit and functional testing but focuses explicitly on visual fidelity rather than behavior. Tools like [Percy](https://percy.io/), [Applitools](https://applitools.com/), or [Storybook](https://storybook.js.org/) support this pattern, but implementations can leverage custom solutions with frameworks like Playwright or Cypress.

---

## **Schema Reference**
Below is the core schema for implementing UI Visual Regression Testing. Adjust based on tool/framework choice.

| **Component**               | **Description**                                                                                                                                                                                                 | **Example Values/Attributes**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Test Environment**        | Target runtime (browser, device, OS) where snapshots are captured.                                                                                                                                             | `browser: "chrome", version: "112", device: "iPhone 13"`                                                      |
| **Snapshot Baseline**       | Reference image(s) against which new captures are compared. Can be manually or automatically generated.                                                                                                     | `baseline_version: "v1.0", baseline_date: "2023-10-01", baseline_tool: "Percy"`                              |
| **Capture Rules**           | Configurable settings for snapshot generation (e.g., viewport size, scroll depth, interaction steps).                                                                                                          | `viewport: [1920, 1080], scroll_steps: [0, 500, 1000], delay: 2000ms`                                       |
| **Comparison Algorithm**    | Method for detecting differences between snapshots (e.g., pixel-perfect, fuzzy matching, or region-based).                                                                                                      | `"algorithm": "fuzzy", "threshold": 0.05` (5% tolerance)                                                       |
| **Test Case**               | A logical unit of UI VRT (e.g., a page, component, or flow).                                                                                                                                                 | `name: "LoginPage", path: "/login", test_id: "login_vrt_001"`                                                   |
| **Dependencies**            | External resources or services required (e.g., user authentication, dynamic data).                                                                                                                                | `requires_auth: true, data_source: "mock_api"`                                                                   |
| **Exceptions**              | Known visual differences intentionally ignored (e.g., dynamic timestamps).                                                                                                                                      | `skip_elements: ["#clock", "#user-avatar"]`, `skip_regions: [rectangle(50,50,200,100)]`                       |
| **Integration Hooks**       | CI/CD or build system triggers for snapshot capture/comparison.                                                                                                                                              | `trigger: "on_push", pipeline: "github_actions", artifact_path: "screenshots/vrt"`                             |
| **Notifications**           | Alerts for failures (e.g., Slack, email) or approval workflows for new baselines.                                                                                                                                | `notify_on_fail: true, channel: "#design-team", approval_required: true`                                     |
| **Performance Metrics**     | Benchmarking data (e.g., capture time, comparison speed, memory usage).                                                                                                                                     | `capture_time_ms: 1245, comparison_time_ms: 872, memory_usage_mb: 412`                                       |

---

## **Implementation Steps**
### **1. Define Scope & Baseline**
- **Scope**: Identify critical UI surfaces (e.g., dashboards, forms, modals) or components (e.g., buttons, cards).
- **Baseline Generation**:
  - Manually: Capture initial "golden" screenshots using a tool (e.g., `percy-capture` CLI).
  - Automatically: Run tests on a stable branch (e.g., `main`) to auto-generate baselines.
  - *Example CLI*:
    ```bash
    percy exec "npm run build && npm run test:ui" --baseline "initial-release"
    ```

### **2. Configure Capture Settings**
Use **viewport and scroll rules** to avoid partial captures:
```json
// Example config (Percy)
{
  "viewport": {
    "width": 1280,
    "height": 720,
    "device": "iPhone 12"
  },
  "scroll": {
    "strategy": "continuous",
    "pixelPadding": 20
  },
  "waitForSelector": "#app-root"
}
```
- **Dynamic Content**: Use `data-testid` or `aria-label` selectors to stabilize elements.
- **Animations**: Add delays (`waitFor: 3000`) or disable animations during capture.

### **3. Integrate with Test Framework**
#### **Playwright Example**
```javascript
// playwright.test.js
const { test, expect } = require('@playwright/test');
const { captureScreenshot } = require('percy-playwright');

test('Login Page VRT', async ({ page }) => {
  await page.goto('https://example.com/login');
  await captureScreenshot(page, { name: 'login-page' });
  await expect(page).toHaveScreenshot('login-expected.png', {
    threshold: 0.05,
    mask: ['#unpredictable-id']
  });
});
```
#### **Cypress Example**
```javascript
// cypress/e2e/vrt.cy.js
describe('Visual Regression', () => {
  it('should match dashboard snapshot', () => {
    cy.visit('/dashboard');
    cy.compareSnapshot('dashboard', {
      scroll: true,
      skip: ['#dynamic-timestamp']
    });
  });
});
```

### **4. Compare Snapshots**
- **Tools**:
  - **Percy**: Cloud-based with interactive diffs and baseline approvals.
  - **Applitools**: AI-powered matching with "masks" for dynamic elements.
  - **Storybook**: Built-in VRT addon for component libraries.
- **Custom Tools**:
  Use libraries like [`pixelmatch`](https://github.com/mapbox/pixelmatch) to compare PNGs:
  ```javascript
  const { diffPixels } = require('pixelmatch');
  const diff = diffPixels(
    refImage, currentImage, {threshold: 0.1},
    {onlyDifferentPixels: true}
  );
  if (diff > 0) throw new Error(`Visual regression detected (${diff} pixels differ)`);
  ```

### **5. Handle Failures**
- **Auto-Approval Workflow**:
  - Flag failures but allow manual approval for intentional changes.
  - *Example (Percy)*:
    ```yaml
    # .percy.yml
    approval:
      required: true
      reviewers: ["design-team"]
    ```
- **Differential Updates**:
  Overwrite baselines only if changes are approved:
  ```bash
  percy approve --add-baseline "login-page" --message "Updated button colors"
  ```

### **6. Integrate with CI/CD**
Example GitHub Actions workflow:
```yaml
# .github/workflows/vrt.yml
name: Visual Regression
on: [push, pull_request]
jobs:
  vrt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npx playwright test --ui --headed  # Visual debug mode
      - run: npx percy exec "npm run test:ui"
        env:
          PERCY_TOKEN: ${{ secrets.PERCY_TOKEN }}
```

---

## **Query Examples**
### **1. Capture & Publish Screenshots**
```bash
# Capture all pages in a test suite
npx playwright test --ui --screenshot-on-failure
# Publish to Percy
percy upload "playwright-results/screenshots"
```

### **2. Dry Run (No Upload)**
```bash
percy exec "npm test" --dry-run
```

### **3. Retry Failed Tests**
```bash
percy retry --count 2 "login-page"  # Retry failed comparison
```

### **4. Force Update Baseline**
```bash
percy update --baseline "dashboard" --message "Resolved layout shift"
```

### **5. Generate Report**
```bash
percy report --output "vrt-report.json"
```

---

## **Best Practices**
1. **Scope Wisely**:
   - Start with high-visibility pages/components (e.g., onboarding, checkout).
   - Exclude non-critical or dynamic elements (e.g., ads, live feeds).

2. **Optimize Performance**:
   - Limit viewport sizes to avoid heavy captures.
   - Use `waitForSelector` to avoid timing issues.

3. **Handle Dynamic Content**:
   - Skip known variables (e.g., dates, user avatars) using selectors or masks.
   - Example (Applitools):
     ```json
     {
       "regions": [
         {
           "selector": "#timestamp",
           "strategy": "ignore"
         }
       ]
     }
     ```

4. **Baseline Strategy**:
   - **Semantic Versioning**: Link baselines to release tags (e.g., `v1.0.0`).
   - **Environment Isolation**: Maintain separate baselines for staging/prod.

5. **Collaboration**:
   - Notify designers/developers of failures early (e.g., Slack alerts).
   - Use tools like Percy’s "Visual Diff" to debug changes interactively.

6. **False Positives**:
   - Adjust thresholds for fuzzy matching (e.g., `threshold: 0.02` for minor color shifts).
   - Whitelist known regressions temporarily with `skip` rules.

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Component Testing](#)**           | Isolates UI components (e.g., buttons) for unit-like visual tests.                                                                                                                                             | Testing reusable components (e.g., Storybook stories).                                              |
| **[Cross-Browser Testing](#)**       | Ensures UI works identically across browsers/OS.                                                                                                                                                               | Launching multi-browser applications.                                                              |
| **[Accessibility Testing](#)**       | Validates UI meets WCAG/AAA standards.                                                                                                                                                                      | Compliance-driven projects (e.g., government, banking).                                           |
| **[A/B Testing](#)**                 | Compares two UI variants for performance/metrics.                                                                                                                                                                | Marketing experiments (e.g., "Button A vs. Button B").                                             |
| **[Performance Budgeting](#)**       | Sets limits for load times/rendering speed.                                                                                                                                                                  | Optimizing heavy UIs (e.g., dashboards).                                                          |
| **[Dark Mode Testing](#)**           | Tests UI in dark/light mode consistency.                                                                                                                                                                      | Themes/preferences-based apps.                                                                    |

---
## **Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                                                                     |
|-------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------------------------|
| False negatives                     | Fuzzy threshold too strict.               | Increase threshold (e.g., `0.05` → `0.1`).                                                      |
| Partial captures                    | Scroll/viewport misconfig.                | Adjust `scrollStrategy` or add `pixelPadding`.                                                  |
| Slow comparisons                    | Large images/resolutions.                 | Reduce viewport size or use WebP format.                                                        |
| Dynamic content mismatches          | Unstable selectors.                       | Use `data-testid` or region-based masking.                                                       |
| CI pipeline flakiness               | Network/delay inconsistencies.           | Add retries or `waitForSelector` with longer delays.                                             |
| Approval bottlenecks                | Manual baseline updates.                  | Automate for non-critical paths (e.g., "staging" branches).                                     |

---
## **Tools & Libraries**
| **Tool**               | **Type**               | **Key Features**                                                                                     | **Link**                                      |
|------------------------|------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| Percy                  | SaaS                   | AI-powered diffs, interactive debugging, CI integration.                                           | [percy.io](https://percy.io/)                 |
| Applitools             | SaaS                   | Visual AI, eye-tracking overlay, cross-browser support.                                             | [applitools.com](https://applitools.com/)      |
| Storybook              | Open-source            | Built-in VRT addon, component-driven testing.                                                      | [storybook.js.org](https://storybook.js.org/)   |
| Playwright/VRT         | Open-source            | Integrates with Playwright for screenshot comparisons.                                             | [playwright.dev/docs/test-vrt](https://playwright.dev/docs/test-vrt) |
| Cypress VRT            | Plugin                 | Customizable snapshots, region masking.                                                          | [cypress.io/plugins/vrt](https://on.cypress.io/plugins) |
| Pixelmatch             | Library                | Pure JavaScript pixel-diffing (e.g., for custom tools).                                           | [github.com/mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) |

---
## **Further Reading**
- [Percy Docs: Visual Regression Testing](https://docs.percy.io/docs/visual-regression-testing)
- [Applitools Visual Testing Guide](https://applitools.com/docs/guides/visual-testing)
- [Playwright VRT Deep Dive](https://playwright.dev/docs/test-vrt)
- [Storybook Addon: Chakra VRT](https://storybook.js.org/addons/@storybook/addon-chakra)

---
**Note**: Adjust tooling and thresholds based on your project’s sensitivity to visual changes (e.g., e-commerce vs. internal tools). Start with a small scope and expand coverage iteratively.