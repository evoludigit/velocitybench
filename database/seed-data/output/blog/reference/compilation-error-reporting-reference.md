# **[Pattern] Compilation Error Reporting – Reference Guide**

---

## **Overview**
The **Compilation Error Reporting** pattern is a debugging and developer experience (DX) best practice that ensures the build pipeline collects and presents **all compilation errors** (rather than halting at the first) with **detailed context** (line numbers, code snippets, error messages, and actionable suggestions).

This pattern is critical in CI/CD pipelines, IDE integrations, and internal developer tools where **fast iteration** and **minimal friction** are prioritized. By providing **consolidated error reporting**, teams reduce debugging time, improve collaboration, and maintain high code quality.

---

## **Schema Reference**

The following table defines the **core components** of a **Compilation Error Report** in a structured format (adaptable to JSON, XML, or YAML).

| **Field**               | **Type**   | **Description**                                                                                   | **Example Value**                          | **Required?** |
|-------------------------|------------|---------------------------------------------------------------------------------------------------|--------------------------------------------|---------------|
| `compilation_id`        | `string`   | Unique identifier for the failed compilation run (e.g., CI job ID).                             | `"build_abc123"`                           | Yes           |
| `timestamp`             | `ISO8601`  | When the compilation finished (or was reported).                                               | `"2024-05-20T14:30:22Z"`                   | Yes           |
| `source_language`       | `string`   | The programming language being compiled (e.g., TypeScript, Python, Go).                         | `"typescript"`                              | Yes           |
| `errors`                | `array`    | List of all encountered compilation errors (even if >1).                                         | *[see nested table below]*                 | Yes           |
| `total_errors`          | `integer`  | Total number of errors (for quick scanning).                                                  | `3`                                        | Yes           |
| `file_path`             | `string`   | Root directory of the project being compiled (if applicable).                                    | `"/projects/app/src"`                      | No            |
| `suppress_warnings`     | `boolean`  | Flag to indicate whether warnings are included in reporting.                                     | `false`                                    | No            |

---

### **Nested Error Schema**
Each error in the `errors` array follows this structure:

| **Field**               | **Type**   | **Description**                                                                                   | **Example Value**                          | **Required?** |
|-------------------------|------------|---------------------------------------------------------------------------------------------------|--------------------------------------------|---------------|
| `error_id`              | `string`   | Unique identifier for this specific error (auto-generated).                                       | `"error_ts_123"`                           | Yes           |
| `file`                  | `string`   | Path to the file where the error occurred (relative to `file_path`).                              | `"src/components/Button.tsx"`              | Yes           |
| `line_number`           | `integer`  | Line number of the error (1-based).                                                               | `42`                                        | Yes           |
| `column_number`         | `integer`  | Column number of the error (optional for some languages).                                        | `10`                                        | No            |
| `severity`              | `enum`     | Severity level (`"error"`, `"warning"`, `"suggestion"`).                                         | `"error"`                                   | Yes           |
| `message`               | `string`   | Human-readable error message (e.g., from the compiler).                                           | `"Type 'undefined' is not assignable to type 'string'."` | Yes           |
| `suggestions`           | `array`    | Array of actionable fixes (if available).                                                       | `[{"action": "add missing type annotation", "code": "FixLine3"}]` | No            |
| `code_context`          | `object`   | Snippet of code surrounding the error (e.g., 3 lines before/after).                              | `{ "start_line": 39, "end_line": 45, "code": "..." }` | No            |
| `compiler_message`      | `string`   | Raw error message from the compiler (for advanced debugging).                                    | `"TS2339: Property 'foo' does not exist on type 'Bar'."` | No            |
| `related_files`         | `array`    | List of files that might need attention (e.g., imports).                                          | `[{"file": "src/types.d.ts", "reason": "missing interface"}]` | No            |

---

## **Implementation Details**

### **1. Compiler Integration**
- **Language-Specific Hooks**: Modify the compiler’s output stream to capture all errors (e.g., using TypeScript’s `tsc --noEmitOnError` + custom parsing).
- **Tooling Support**:
  - **Build Systems**: Webpack, Vite, or Babel can be configured to emit error collections (e.g., via plugins).
  - **IDE Plugins**: Integrate with VS Code, IntelliJ, or WebStorm to show errors **without requiring a full rebuild**.

### **2. Error Aggregation**
- **Buffering**: Store errors in memory until the entire compilation completes (avoids premature termination).
- **Deduplication**: Group similar errors (e.g., multiple missing exports) into a single report entry.

### **3. Formatting & Display**
| **Format Option**       | **Use Case**                          | **Example Tools**              |
|-------------------------|---------------------------------------|---------------------------------|
| **Terminal Output**     | CI/CD pipelines, local builds.       | `tsc --pretty`, custom scripts. |
| **Rich HTML/Markdown**  | IDE integrations, docs.              | `error-report-generator`.       |
| **JSON/YAML**           | APIs, programmatic processing.       | Postman, curl requests.         |
| **Interactive UI**      | Web dashboards (e.g., GitHub Actions).| Custom React/Next.js app.       |

### **4. Example Output (Terminal)**
```plaintext
▲ Compilation Errors (3 total) ▼
───────────────────────────────
[error_ts_123] src/components/Button.tsx:42:10
  Type 'undefined' is not assignable to type 'string'.
  Suggestions:
    1. Add `defaultProps` to Button.tsx
    2. Check `getName()` return type in utils.ts

[warning_ts_456] src/hooks/useFetch.ts:15:5
  Unused parameter 'timeout'. Remove or rename.
───────────────────────────────
```

### **5. API Endpoint Example (REST)**
```http
POST /api/compilation-reports
Content-Type: application/json

{
  "compilation_id": "build_abc123",
  "source_language": "typescript",
  "errors": [
    {
      "error_id": "error_ts_123",
      "file": "src/components/Button.tsx",
      "line_number": 42,
      "severity": "error",
      "message": "Type 'undefined' is not assignable to type 'string'.",
      "suggestions": [{
        "action": "Add `onClick` handler",
        "code": "FixLine42"
      }]
    }
  ]
}
```

---

## **Query Examples**

### **1. Filter Errors by Severity (SQL-like)**
```sql
SELECT * FROM compilation_errors
WHERE severity = "error"
AND file_path LIKE "%components%";
```

### **2. Get Most Common Error Type (Python Example)**
```python
from collections import defaultdict
errors = [{"severity": s} for s in error_list]
error_counts = defaultdict(int)
for error in errors:
    error_counts[error["severity"]] += 1
print(error_counts)  # {'error': 3, 'warning': 2}
```

### **3. Generate a Report Summary (CLI Tool)**
```bash
#!/bin/bash
# Parse error report JSON and generate a summary
errors=$(jq '.errors[] | {file, line_number, message}' report.json)
echo "Total Errors: $(jq '.total_errors' report.json)"
echo "$errors" | column -t -s $'\t'
```

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                 | **When to Use**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[First Error Fast]**           | Stops at the first error to fail fast (opposite of this pattern).                               | Small projects, strict CI gates.                                               |
| **[Error Grouping]**             | Combines similar errors (e.g., multiple missing exports) into a single entry.                 | Reducing noise in large codebases.                                             |
| **[Compiler-as-a-Service]**      | Offloads compilation to a remote service (e.g., GitHub Codespaces).                          | Distributed teams, cloud-native dev environments.                              |
| **[Lint-as-Code]**               | Treats linting/warnings as part of the code review process (e.g., pre-commit hooks).         | Enforcing consistency via Git hooks.                                           |
| **[Diff-Aware Compilation]**     | Only checks changed files between commits (e.g., `git diff`).                                 | Speeding up CI builds in large repos.                                           |

---

## **Best Practices**
1. **Prioritize Actionability**: Always include **suggestions** or **fix templates** (e.g., `FixLineX`).
2. **Support Multiple Languages**: Extend the pattern to JavaScript, Rust, Go, etc., via language-specific adapters.
3. **Performance**: Avoid slowing down builds by optimizing error parsing (e.g., streaming).
4. **Localization**: Provide translated error messages for international teams.
5. **IDE Integration**: Expose errors via **LSP (Language Server Protocol)** for real-time feedback.

---
**References**:
- [TypeScript Compiler API](https://www.typescriptlang.org/tsconfig)
- [ESLint Error Reporting](https://eslint.org/docs/developer-guide/nodejs-api)
- [GitHub Actions Error Summary](https://docs.github.com/en/actions/learn-github-actions/workflow-commands-for-github-actions#setting-an-error-message)