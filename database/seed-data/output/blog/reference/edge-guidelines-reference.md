# **[Pattern] Edge Guidelines Reference Guide**

---

## **Overview**
The **Edge Guidelines** pattern ensures that content remains readable and functional at the edges of a viewport, regardless of screen size, device type, or browser zoom level. This pattern mitigates issues caused by **Viewport Responsiveness Constraints**, where elements (e.g., text, icons, padding) may become cut off, misaligned, or unreadable at screen boundaries. It achieves this by dynamically adjusting padding, margins, and scaling factors to maintain a fixed visual boundary (e.g., 10px from the viewport edge). This pattern is critical for:
- **Accessibility** (ensuring content remains legible at all zoom levels).
- **Consistency** (preventing abrupt layout shifts).
- **Performance** (avoiding layout thrashing from recalculations).

Edge Guidelines work in tandem with **CSS Clamp()** for dynamic sizing and **Viewport Units (vh/vw/vmin)** for fluid responsive layouts. This pattern is most effective when combined with **CSS Container Queries** or **CSS Grid** for complex layouts.

---

## **Implementation Details**

### **Core Principles**
1. **Fixed Edge Buffer**: Maintain a constant padding/margin (e.g., `10px`, `20px`) from the viewport edge.
2. **Viewport-Aware Scaling**: Use relative units (`vw`, `vh`, `dvw`, `dvh`) or `clamp()` to scale content dynamically.
3. **Prevent Overflow**: Ensure no content extends beyond the safe area (e.g., using `overflow: hidden` on parent containers).
4. **Fallbacks**: Provide graceful degradation for browsers unsupported `dvw`/`dvh` (e.g., Safari <15).

---

### **Key Components**
| Component               | Purpose                                                                 | Example Code                                  |
|-------------------------|-------------------------------------------------------------------------|-----------------------------------------------|
| **Viewport Units**      | Scale elements relative to viewport dimensions.                         | `width: 100dvw;`                              |
| **CSS Clamp()**         | Dynamically adjust padding/margins between min/max bounds.             | `padding: clamp(10px, 2vw, 30px);`            |
| **Safe Area Insets**    | Account for device notches (iPhone X, Android P).                      | `@media (safe-area-inset-top: var(--safe)) {}` |
| **Container Queries**   | Adjust layout based on container size (not viewport).                   | `@container (max-width: 600px) { ... }`       |
| **Media Queries**       | Fallbacks for unsupported features (e.g., `dvw` in older browsers).    | `@media (max-width: 1200px) { ... }`          |

---

## **Schema Reference**
Below is a structured schema for implementing Edge Guidelines in a component or layout system.

| Property               | Type          | Description                                                                 | Example Values                     | Required |
|------------------------|---------------|-----------------------------------------------------------------------------|------------------------------------|----------|
| **`edgeBuffer`**       | `number`      | Fixed padding/margin from viewport edges (in pixels or `%`).                 | `10px`, `2%`                       | Yes       |
| **`viewportUnits`**    | `boolean`     | Enable/disable `vw`, `vh`, `dvw`, `dvh` usage.                             | `true`, `false`                    | No        |
| **`clampEnabled`**     | `boolean`     | Use `clamp()` for dynamic scaling between min/max bounds.                   | `true`, `false`                    | No        |
| **`clampMin`**         | `string`      | Minimum value for `clamp()` (e.g., `10px`, `1%`).                           | `10px`, `0.5vw`                    | Conditional |
| **`clampMax`**         | `string`      | Maximum value for `clamp()` (e.g., `30px`, `5%`).                           | `30px`, `5vw`                      | Conditional |
| **`safeAreaSupport`**  | `boolean`     | Account for device notches/safe areas.                                       | `true`, `false`                    | No        |
| **`containerQuery`**   | `boolean`     | Enable CSS Container Queries for nested components.                        | `true`, `false`                    | No        |
| **`overflowControl`**  | `string`      | Handle overflow (e.g., `hidden`, `auto`, `scroll`).                       | `hidden`, `auto`                   | No        |

### **Example Schema Implementation (JSON)**
```json
{
  "edgeBuffer": "20px",
  "viewportUnits": true,
  "clampEnabled": true,
  "clampMin": "15px",
  "clampMax": "40px",
  "safeAreaSupport": true,
  "containerQuery": false,
  "overflowControl": "hidden"
}
```

---

## **Query Examples**
This section demonstrates how to apply Edge Guidelines in different scenarios using **CSS**, **JavaScript**, and **React/JSX**.

---

### **1. Basic CSS Implementation (Static Buffer)**
Apply a fixed padding buffer to maintain distance from viewport edges.
```css
.container {
  padding: 20px;
  max-width: 100%;
  box-sizing: border-box;
}
```

**Edge Case Handling**:
```css
/* Prevent text from being cut off at bottom */
.container {
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
}
```

---

### **2. Dynamic Scaling with `clamp()` and `vw`**
Adjust padding based on viewport width while respecting an edge buffer.
```css
.container {
  padding: clamp(10px, 2vw, 30px);
  margin: 0 auto;
  max-width: 90dvw;
}
```

**Combined with Safe Area Insets**:
```css
.container {
  padding: clamp(10px, 2vw, 30px);
  padding-bottom: clamp(10px, 2vh, 30px) +
                    env(safe-area-inset-bottom);
}
```

---

### **3. JavaScript Implementation (Dynamic Adjustment)**
Dynamically adjust margins/padding based on browser zoom or device size.
```javascript
function applyEdgeGuidelines(container) {
  const minBuffer = 10;
  const maxBuffer = 30;
  const viewportWidth = window.innerWidth;
  const buffer = Math.min(
    Math.max(minBuffer, (viewportWidth * 0.01)), // 1% of viewport width
    maxBuffer
  );
  container.style.padding = `${buffer}px`;
}

// Apply on load and resize
applyEdgeGuidelines(document.querySelector('.container'));
window.addEventListener('resize', () => applyEdgeGuidelines(document.querySelector('.container')));
```

---

### **4. React/JSX Example (Conditional Rendering)**
Use state or props to toggle Edge Guidelines based on conditions.
```jsx
import { useState, useEffect } from 'react';

function ResponsiveContainer({ children }) {
  const [buffer, setBuffer] = useState(20);

  useEffect(() => {
    const updateBuffer = () => {
      setBuffer(Math.min(30, window.innerWidth * 0.02));
    };
    updateBuffer();
    window.addEventListener('resize', updateBuffer);
    return () => window.removeEventListener('resize', updateBuffer);
  }, []);

  return (
    <div
      style={{
        padding: `${buffer}px`,
        maxWidth: '100%',
        boxSizing: 'border-box',
      }}
    >
      {children}
    </div>
  );
}
```

---

### **5. CSS Grid with Edge Guidelines**
Ensure grid items maintain spacing from viewport edges.
```css
.grid-container {
  display: grid;
  gap: 1rem;
  padding: clamp(10px, 2vw, 30px);
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.grid-item {
  padding: 1rem;
  box-sizing: border-box;
}
```

---

## **Query Examples: Edge Case Scenarios**

| Scenario                          | Solution                                                                 |
|-----------------------------------|-------------------------------------------------------------------------|
| **Text cut off at viewport bottom** | Use `env(safe-area-inset-bottom)` or `vh`-based padding.              |
| **Overflow on small screens**      | Combine with `overflow: auto` or `@container` queries.                  |
| **Browser zoom > 200%**           | Use `vw`/`vh` units with `clamp()` to prevent excessive scaling.        |
| **Dark mode contrast issues**      | Adjust `background-color`/`color` dynamically (e.g., `prefers-color-scheme`). |
| **Nested components**             | Use CSS Container Queries to scope edge guidelines per component.      |

---
## **Related Patterns**
To maximize effectiveness, combine Edge Guidelines with these patterns:

| Pattern                          | Description                                                                 | Use Case Example                          |
|----------------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **[Responsive Typography](responsive-typography.md)** | Scale font sizes dynamically using `clamp()` and `rem`/`em`.               | Ensuring readability at all viewport sizes. |
| **[Viewport Units](viewport-units.md)** | Use `vw`, `vh`, `dvw`, `dvh` for fluid layouts.                          | Scaling components with viewport dimensions. |
| **[CSS Container Queries](container-queries.md)** | Apply styles based on container size, not viewport.                     | Nested components with independent edge rules. |
| **[Safe Area Insets](safe-area-inks.md)** | Account for device notches (iPhone X, Android P).                          | Preventing UI elements from being obscured. |
| **[Responsive Images](responsive-images.md)** | Optimize images for viewport size and resolution.                          | High-DPI displays (Retina, 4K).           |
| **[Mobile-First Design](mobile-first.md)** | Start with small screens, scale up.                                       | Prioritizing content for low-bandwidth users. |
| **[Accessible Color Contrast](contrast.md)** | Ensure readability with `prefers-contrast` media queries.                | Dark mode and low-vision users.          |

---

## **Best Practices**
1. **Test Across Devices**:
   - Use **Browsershots** or **LambdaTest** to verify behavior on iOS/Android.
   - Simulate zoom levels up to **200%** (e.g., Chrome DevTools).

2. **Performance Considerations**:
   - Avoid excessive `clamp()` calculations in JS-heavy apps.
   - Prefer CSS-only solutions where possible (e.g., `env(safe-area-inset)`).

3. **Fallbacks**:
   - Support older browsers with `@supports` (e.g., for `dvw`):
     ```css
     @supports not (width: -webkit-fill-available) {
       .container {
         padding: 20px; /* Fallback */
       }
     }
     ```

4. **Documentation**:
   - Clearly communicate edge buffer values in design systems (e.g., Figma/Storybook).
   - Use **design tokens** (e.g., `$edge-buffer: 20px`) for maintainability.

5. **Animation Considerations**:
   - Animate edge adjustments smoothly (e.g., `transition: padding 0.3s ease`).
   - Avoid layout thrashing during rapid viewport changes.

---
## **Anti-Patterns to Avoid**
| Anti-Pattern                          | Why It Fails                                                                 | Solution                          |
|---------------------------------------|-------------------------------------------------------------------------------|-----------------------------------|
| **Fixed Pixel Padding (e.g., `20px`)** | Doesn’t scale with viewport or zoom.                                       | Use `clamp()` or `%`-based units. |
| **Ignoring Safe Areas**               | UI elements get cut off on notched devices (e.g., iPhone X).               | Use `env(safe-area-inset)`.       |
| **Over-Reliance on Media Queries**    | Media queries break at arbitrary breakpoints, not viewport edges.          | Prefer `dvw`/`dvh` units.        |
| **Hardcoded `vw`/`vh` Values**        | Can lead to unintended scaling (e.g., `100vw` on mobile).                  | Use `clamp()` for bounds.         |
| **No Fallbacks**                      | Older browsers may render incorrectly or not at all.                        | Test with `@supports` polyfills. |

---
## **Tools & Libraries**
| Tool/Library               | Purpose                                                                   | Link                                  |
|----------------------------|---------------------------------------------------------------------------|---------------------------------------|
| **CSS Container Queries**  | Scope edge guidelines to nested components.                              | [MDN Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/Container_Queries) |
| **PostCSS `clamp` Plugin** | Autoprefix `clamp()` for broader browser support.                         | [GitHub](https://github.com/andy-johnson/postcss-clamp) |
| **Safari `dvw` Polyfill**  | Support `dvw`/`dvh` in Safari <15.                                        | [GitHub](https://github.com/mathiasbynens/dvw) |
| **Browsershots**           | Test across real devices/browsers.                                        | [Website](https://www.browsershots.org/) |
| **LambdaTest**             | Cloud-based cross-device testing.                                         | [Website](https://www.lambdatest.com/) |

---
## **Example Code Repository**
For a practical implementation, refer to:
- **[Edge Guidelines Starter Kit](https://github.com/your-org/edge-guidelines-example)**
  (Includes React, Vue, and vanilla CSS templates.)

---
## **Summary Checklist**
Before finalizing implementation, verify:
- [ ] Edge buffers maintain consistency across devices.
- [ ] Text/icons never touch viewport edges (test at zoom extremes).
- [ ] Safe areas are respected on notched devices.
- [ ] Fallbacks work in unsupported browsers.
- [ ] Performance impact is minimal (no layout thrashing).

---
**Next Steps**:
1. Integrate Edge Guidelines into your design system.
2. Test with real users (especially high-zoom scenarios).
3. Document the pattern for your team (e.g., Confluence/Notion).