# **[Pattern] Accessibility Testing Reference Guide**

---

## **Overview**
This reference guide outlines the **Accessibility Testing Pattern**, a structured approach to ensuring digital products, applications, and services are usable by people with disabilities. Accessibility testing evaluates compliance with standards like **WCAG (Web Content Accessibility Guidelines)**, **ADA (Americans with Disabilities Act)**, and other region-specific regulations. This pattern covers **manual testing, automated tools, heuristic evaluation, and integration testing** to identify and remediate barriers (e.g., color contrast, keyboard navigation, ARIA labels, screen reader compatibility).

Key objectives:
- **Detect** accessibility violations early in development.
- **Validate** fixes to prevent regression.
- **Document** findings for legal compliance and user inclusion.
- **Automate** repetitive checks for efficiency.

This guide assumes familiarity with **accessibility principles** (e.g., POUR: Perceivable, Operable, Understandable, Robust) and basic **HTML/CSS/JavaScript** concepts.

---

## **Schema Reference**
Below is a structured breakdown of the **Accessibility Testing Pattern**, divided into **phases**, **methods**, and **key validation criteria**.

| **Phase**          | **Method**               | **Description**                                                                                     | **Key Validation Criteria**                                                                                     | **Tools/Libraries**                                                                                     |
|--------------------|--------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **1. Planning**    | **Scope Definition**     | Define test scope (web apps, mobile, APIs, documents). Identify user personas (e.g., low vision, motor impairment). | - Target platforms/browsers. <br> - Priority feature areas (e.g., forms, media). <br> - Compliance level (A/AA/AAA). | [User Story Mapping](https://www.mural.co/templates/user-story-mapping) <br> [Priority Matrix](https://www.prioritizr.com/) |
| **2. Manual Testing** | **Heuristic Evaluation** | Expert review of UI/UX against WCAG principles.                                                     | - Perceivable: Text contrast ratio (≥4.5:1 for normal, ≥3:1 for large). <br> - Operable: Keyboard navigability. <br> - Understandable: ARIA labels, language attributes. <br> - Robust: Compatibility across assistive tech. | [WCAG Contrast Checker](https://webaim.org/resources/contrastchecker/) <br> [axe DevTools](https://www.deque.com/axe/) |
|                   | **User Testing**         | Observe real users with disabilities (e.g., via cognitive labs or accessibility communities).       | - Task completion success rate. <br> - Frustration points (e.g., form labels missing). <br> - Time-on-task metrics. | [UserTesting.com](https://www.usertesting.com/) <br> [AccessibilityJS](https://accessibilityjs.com/) |
|                   | **Keyboard Testing**     | Validate all interactions are keyboard-accessible (no mouse-dependent elements).                     | - Tab order follows logical sequence. <br> - Focus indicators visible. <br> - Skip links functional.           | Native browser dev tools (F6 for tabbing) <br> [Keyboard Navigator](https://chrome.google.com/webstore/detail/keyboard-navigator/ohhodjkdndegacgcpdpdgcpkkjbhjbck) |
| **3. Automated Testing** | **Static Analysis**      | Scan code for accessibility violations (e.g., missing alt text, semantic HTML).                     | - `alt` attributes on images. <br> - Proper heading hierarchy (`<h1>`–`<h6>`). <br> - ARIA roles/states.       | [ESLint (w/ plugins)](https://www.npmjs.com/package/eslint-plugin-jsx-a11y) <br> [axe CLI](https://www.deque.com/axe/browser-doc/) |
|                   | **Dynamic Testing**      | Run tests during runtime to check dynamic content (e.g., modals, dropdowns).                      | - ARIA live regions update screen readers. <br> - Dynamic content keyboard-navigable. <br> - Focus traps avoidable. | [Lighthouse CI](https://developer.chrome.com/docs/lighthouse/ci/) <br> [Pa11y](https://pa11y.org/)       |
| **4. Compliance Checks** | **WCAG/AODA/Section 508** | Validate against specific regulations (e.g., WCAG 2.2 Level AA).                                   | - Color contrast (WCAG 1.4.3). <br> - Keyboard operation (WCAG 2.1.1). <br> - Captions/transcripts (WCAG 1.2).   | [WAVE Evaluation Tool](https://wave.webaim.org/) <br> [AChecker](https://achecker.ca/checker/index.php) |
|                   | **Color Blindness Testing** | Simulate color vision deficiencies (protanopia, deuteranopia).                                      | - Sufficient color contrast even for simulated conditions. <br> - Non-color-critical info (e.g., icons).            | [Color Oracle](https://colororacle.org/) <br> [Sim Daltonism](https://apps.apple.com/us/app/sim-daltonism/id1038077113) |
| **5. Reporting**   | **Issue Logging**        | Document findings in a structured format (e.g., Jira, GitHub Issues).                              | - Clear reproduction steps. <br> - Severity (Critical/Major/Minor). <br> - Acceptance criteria for fixes.     | [Jira](https://www.atlassian.com/software/jira) <br> [GitHub Issues](https://github.com/features/issues)  |
|                   | **Accessibility Audit Report** | Summarize compliance status, risks, and remediation steps.                                           | - Pass/fail status per WCAG criterion. <br> - Risk ranking. <br> - Roadmap for fixes.                          | Custom templates or tools like [AXE Report](https://www.deque.com/axe/core-concepts/report/)              |
| **6. Remediation & Validation** | **Fix Verification**     | Re-test after fixes to ensure issues are resolved.                                                   | - Re-run automated tools. <br> - Manual re-validation (e.g., keyboard testing). <br> - User feedback loop.      | Same tools as Phases 2–4                                                                               |
|                   | **Continuous Integration** | Integrate accessibility testing into CI/CD pipelines.                                                 | - Automated checks on every commit/PR. <br> - Blockers for non-compliant code.                             | [Snyk](https://snyk.io/) <br> [SonarQube](https://www.sonarsource.com/products/sonarqube/)               |

---

## **Query Examples**
Below are practical examples of how to apply this pattern in different stages of development.

### **1. Planning: Define Accessibility Scope**
**Scenario**: A team is building a new dashboard for a data analytics platform.
**Query**:
*How do we prioritize accessibility testing for the dashboard given limited resources?*
**Steps**:
1. **Identify critical user flows**:
   - Focus on **data visualization** (e.g., charts, tables) and **filtering** (keyboard nav).
   - Prioritize **high-contrast modes** for low-vision users.
2. **User personas**:
   - Screen reader users (NVDA, VoiceOver).
   - Motor-impaired users (voice control, slow typing).
3. **Tools**:
   - Use a [priority matrix](https://www.prioritizr.com/) to rank features:
     | Feature          | Low-Vision Impact | Motor-Impairment Impact | Severity |
     |------------------|--------------------|-------------------------|----------|
     | Table sorting    | Medium             | High                    | High     |
     | Chart labels     | High               | Low                     | Medium   |

---

### **2. Manual Testing: Heuristic Evaluation**
**Scenario**: Evaluating a login form for WCAG compliance.
**Query**:
*How do we check if the form is keyboard-accessible?*
**Steps**:
1. **Tab order**:
   - Open dev tools (`F12`), press `Tab` repeatedly.
   - Verify order: Username → Password → Submit → Skip link.
   - **Issue found**: Submit button is out of order.
   - **Fix**: Reorder HTML: `<input type="text"> <input type="password"> <button type="submit"> <a href="#main">Skip to content</a>`
2. **Focus styles**:
   - Press `Tab` and confirm focus outlines are visible (no `outline: none`!).
   - **Issue found**: Focus outline hidden on buttons.
   - **Fix**: Add CSS: `button:focus { outline: 2px solid #0056b3; }`.
3. **ARIA labels**:
   - Check if `<label>` is associated with `<input>` via `for` attribute.
   - **Issue found**: Missing labels for radio buttons.
   - **Fix**: Add `<label for="gender-male">Male</label>`.

---
### **3. Automated Testing: Static Analysis**
**Scenario**: Running a WCAG scan on a React component.
**Query**:
*How do we automate checks for missing alt text in images?*
**Steps**:
1. **Integrate ESLint plugin**:
   - Install: `npm install eslint-plugin-jsx-a11y --save-dev`.
   - Add to `.eslintrc.js`:
     ```js
     plugins: ["jsx-a11y"],
     rules: {
       "jsx-a11y/alt-text": ["error", {
         elements: ["img", "area"],
         objects: true,
         imgAltEmptyStringAccessible: true
       }]
     }
     ```
2. **Run in CI**:
   - Add to `package.json` scripts:
     ```json
     "scripts": {
       "lint:accessibility": "eslint . --ext .js,.jsx,.ts,.tsx"
     }
     ```
3. **Check output**:
   - Example error:
     ```
     Line 45: Enabled by default. alt text is required. src="logo.png"
     ```

---

### **4. Compliance Checks: WCAG 2.2**
**Scenario**: Validating a mobile app for WCAG AA compliance.
**Query**:
*How do we ensure touch targets meet WCAG 1.4.2 criteria?*
**Steps**:
1. **Touch target size**:
   - Minimum **48x48 CSS pixels** (or **24x24 pixels scaled to 48x48 at 200% zoom**).
   - **Tool**: Use [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) to inspect touch elements.
   - **Issue found**: Button is 40x40px.
   - **Fix**: Increase size: `button { min-width: 48px; min-height: 48px; }`.
2. **Touch spacing**:
   - Ensure interactive elements have **≥4.8 CSS pixels** between them.
   - **Tool**: [WAVE](https://wave.webaim.org/) highlights violations.
   - **Issue found**: Two buttons overlap when zoomed.
   - **Fix**: Add `gap: 4.8px` in CSS.

---
### **5. Reporting: Accessibility Audit**
**Scenario**: Generating a report for stakeholders.
**Query**:
*What metrics should we include in our accessibility report?*
**Steps**:
1. **Compliance Status**:
   - Summarize WCAG criteria passed/failed (e.g., 85% AA compliance).
2. **Issue Breakdown**:
   | Issue Type          | Count | Severity | Example Fix                          |
   |--------------------|-------|----------|---------------------------------------|
   | Missing alt text    | 12    | Critical | Add `alt` attribute.                  |
   | Low contrast        | 5     | Major    | Increase contrast ratio.              |
   | Keyboard trap       | 3     | Minor    | Add `role="dialog"` + escape handler. |
3. **Risk Assessment**:
   - **High Risk**: Forms with no labels (blocking user submission).
   - **Medium Risk**: Poor color contrast in charts (risk of misinterpretation).
4. **Roadmap**:
   - **Phase 1 (1 week)**: Fix all critical issues.
   - **Phase 2 (2 weeks)**: User testing for fixes.

---
## **Query Examples: Automated Tools**
### **Tool 1: axe (Deque)**
**Query**: *How do I run axe in a Node.js project?*
**Steps**:
1. Install: `npm install axe-core`.
2. Run in CLI:
   ```bash
   npx axe-core https://myapp.com/login
   ```
3. Output:
   ```
   1 violations found
   ❌ Color contrast for button "Submit" (4.1:1, needs to be 4.5:1) (wcag21aa.new-color-contrast)
   ```

### **Tool 2: Lighthouse (Chrome DevTools)**
**Query**: *How do I audit accessibility in Lighthouse?*
**Steps**:
1. Open DevTools (`F12`), go to **Lighthouse** tab.
2. Select **Accessibility** category.
3. Run audit:
   ```
   Accessibility score: 92/100
   Issues:
   - Missing "alt" attribute on image (ID: low-contrast-logo).
   - Form lacks "aria-label" for submit button.
   ```

---

## **Related Patterns**
1. **[Inclusive Design](https://www.inclusive-design.org/)**
   - *How to*: Embed accessibility into the design process from the start (e.g., inclusive user research, flexible interfaces).
   - *When to use*: Early in product planning or redesigns.
   - *Tools*: [Inclusive Components](https://inclusive-components.design/).

2. **[Progressive Enhancement](https://www.smashingmagazine.com/2021/03/progressive-enhancement-2021/)**
   - *How to*: Build core functionality with accessibility first, then enhance for advanced users.
   - *When to use*: Legacy systems or highly customizable apps (e.g., CMS platforms).
   - *Example*: Ensure forms work without JavaScript, then enhance with animations.

3. **[Content Accessibility](https://www.w3.org/WAI/tutorials/forms/)**
   - *How to*: Structure text, media, and tables for accessibility (e.g., proper headings, captions, ARIA landmarks).
   - *When to use*: Document-heavy or multimedia-rich applications.
   - *Tools*: [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/).

4. **[Automated Testing Patterns](https://www.martinfowler.com/articles/automated-testing.html)**
   - *How to*: Integrate accessibility checks into CI/CD pipelines (e.g., pre-commit hooks, post-deploy scans).
   - *When to use*: Agile/DevOps workflows.
   - *Tools*: [Pa11y CI](https://pa11y.org/#ci), [Storybook Addons](https://storybook.js.org/addons/@storybook/addon-a11y).

5. **[User Testing with Disabilities](https://www.ncd.gov.au/guidelines/user-testing-accessibility)**
   - *How to*: Conduct remote or in-person testing with real users (e.g., via [AbilityNet](https://www.abilitynet.org.uk/) or [Accessible360](https://www.accessible360.com/)).
   - *When to use*: Validation of complex UIs or post-launch improvements.
   - *Ethics*: Compensate participants and follow [W3C ethical guidelines](https://www.w3.org/WAI/ER/testing/ethics/).

---
## **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Why It’s Bad**                                                                 | **Fix**                                                                 |
|--------------------------------|----------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| **"Fix it later"**             | Accessibility fixes are often costly to retrofit.                                | Budget time for accessibility in sprints.                            |
| **Over-reliance on automation** | Tools miss contextual issues (e.g., dynamic content, custom interactions).      | Combine manual + automated testing.                                  |
| **Color-only communication**   | Assumes users can perceive colors.                                               | Use icons, text, or patterns for critical info.                      |
| **Skipping keyboard testing**   | Many users rely solely on keyboards (e.g., motor impairments).                   | Test all interactions via keyboard (`Tab`, `Enter`, `Escape`).         |
| **"AAA compliance"**           | Over-optimizing for rare edge cases can delay releases.                         | Prioritize AA compliance; use AAA only for high-impact content.       |

---
## **Key Metrics to Track**
| **Metric**                     | **Tool**               | **Goal**                                                                 |
|--------------------------------|------------------------|--------------------------------------------------------------------------|
| Automation coverage            | CI logs (e.g., axe)     | ≥80% of codebase scanned in pipeline.                                    |
| Manual test pass rate          | Test tracking (Jira)   | ≥90% of heuristic evaluations passed.                                    |
| User testing success rate      | Session recording      | ≥85% of users complete critical tasks without frustration.               |
| Contrast ratio compliance      | WAVE/axe               | 100% of interactive elements meet WCAG 2.2 AA (≥4.5:1 for normal text). |
| Keyboard navigability          | DevTools (Tab testing) | 0 critical focus order or trap issues.                                  |
| Accessibility bugs per release | Bug tracker            | ≤5 critical accessibility bugs per sprint.                              |

---
## **Further Reading**
1. **Standards**:
   - [WCAG 2.2 Guidelines](https://www.w3.org/TR/WCAG22/)
   - [ADA Title III](https://www.ada.gov/regs guidelines/titleiii/tiiiindex.htm)
   - [Section 508 (U.S.)](https://www.section508.gov/)

2. **Frameworks**:
   - [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
   - [CSS Accessibility](https://css-tricks.com/a-comprehensive-guide-to-accessibility-in-modern-css/)

3. **Communities**:
   - [a11y Project](https://www.a11yproject.com/)
   - [Accessibility Stack Exchange](https://stackoverflow.com/questions/tagged/accessibility)