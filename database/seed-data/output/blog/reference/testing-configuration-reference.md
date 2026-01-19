# **[Testing Configuration] Reference Guide**

---

## **Overview**
The **Testing Configuration** pattern is a structured approach to define, manage, and execute test cases programmatically. It centralizes test logic, environment variables, and assertions into configurable components, enabling reusability, maintainability, and dynamic test execution. This pattern is particularly useful in CI/CD pipelines, multi-environment testing (dev/stage/prod), and large-scale test suites where flexibility and modularity are critical.

Key benefits include:
- **Decoupled test logic** from implementation details (e.g., APIs, databases).
- **Environment-aware tests** via configurable parameters (e.g., URLs, credentials).
- **Scalability** through reusable test modules and dynamic selectors.
- **Automation-friendly** designs for CI/CD integration.

This guide covers schema design, implementation best practices, and examples for common use cases.

---

## **Implementation Details**

### **Core Components**
The Testing Configuration pattern typically includes:

| **Component**               | **Description**                                                                                     | **Example**                                  |
|-----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Config Files**            | YAML/JSON files defining test environments, parameters, and assertions.                            | `test_config.yaml`                          |
| **Test Modules**            | Reusable Python/JS/other code snippets for common assertions, API calls, or UI interactions.      | `auth_utils.py`, `api_verifier.js`           |
| **Dynamic Selectors**       | Placeholders (e.g., `${env}`) for values loaded at runtime (e.g., URLs, credentials).              | `${base_url}/api/users`                     |
| **Environment Profiles**    | Predefined sets of configs for dev/stage/prod (e.g., `prod_config.json`).                        | `{ "url": "https://api.prod.example.com" }` |
| **Hooks**                   | Functions triggered before/after tests (e.g., setup DB, cleanup).                               | `on_start()` / `on_finish()`                 |
| **Assertion Libraries**     | Shared libraries for assertions (e.g., `expect().to.equal()`).                                    | `chai.js`, `pytest.assert`                   |

---

### **Schema Reference**
Below is a standardized schema for config files (YAML/JSON). Adjust fields based on your testing framework.

#### **1. Root Config Structure**
```yaml
# test_config.yml
environments:
  - name: dev
    url: ${DEV_URL}
    auth:
      token: ${DEV_TOKEN}
  - name: prod
    url: ${PROD_URL}
    auth:
      token: ${PROD_TOKEN}
modules:
  - name: auth
    path: ./modules/auth_utils.py
  - name: api
    path: ./modules/api_verifier.js
assertions:
  - type: response_status
    expected: 200
  - type: schema_validation
    schema_path: ./schemas/user_schema.json
```

#### **2. Environment-Specific Config**
```yaml
# dev_config.yml
env_name: dev
base_url: "https://api.dev.example.com"
credentials:
  api_key: "sk_demo_123"
  database:
    host: "db.dev.example.com"
    port: 5432
```

#### **3. Dynamic Placeholder Syntax**
Use `${VAR_NAME}` for runtime substitution. Replace with CI/CD secrets or CLI flags:
```yaml
# test_config.yml
api_endpoint: "${API_BASE}/${env}/users"
```

#### **4. Test Case Template**
```yaml
# test_cases/user_auth.yml
description: "Test user authentication flow."
steps:
  - module: auth
    action: login
    params:
      username: "testuser"
      password: "secure123"
  - module: api
    action: verify_token
    params:
      endpoint: "${api_endpoint}/validate"
  - assertions:
      - type: response_status
        expected: 200
```

---

## **Query Examples**
This section demonstrates how to integrate the pattern with common testing frameworks.

---

### **1. Python (Pytest + Config Loader)**
```python
# config_loader.py
import yaml
from typing import Dict, Any

class TestConfig:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.data = yaml.safe_load(f)

    def get(self, key: str) -> Any:
        return self.data.get(key)
```

**Usage in Test:**
```python
# test_auth.py
from pytest import mark
from config_loader import TestConfig

config = TestConfig("test_config.yml")

@mark.parametrize("env", ["dev", "prod"])
def test_auth_flow(env):
    env_config = config.get("environments")[env]
    base_url = env_config["url"]
    token = env_config["auth"]["token"]

    # Use dynamic URL
    endpoint = f"{base_url}/auth/validate?token={token}"
    response = requests.get(endpoint)
    assert response.status_code == 200
```

---

### **2. JavaScript (Mocha + NPM Scripts)**
```javascript
// test_config.js
const yaml = require("yamljs");
const config = yaml.load("./test_config.yml");

module.exports = {
  getEnv: (envName) => config.environments.find(e => e.name === envName),
  getModule: (moduleName) => require(`./modules/${moduleName}.js`),
};
```

**Test Example:**
```javascript
// test_auth.js
const config = require("./test_config");
const assert = require("chai").assert;

describe("Auth Flow", () => {
  it("should validate token in ${env}", async () => {
    const env = config.getEnv("prod");
    const { auth } = env;

    const response = await config.getModule("api")
      .callApi(`/validate`, { token: auth.token });
    assert.equal(response.status, 200);
  });
});
```

---

### **3. CLI Integration (Substituting Placeholders)**
Use tools like `dotenv` (Node.js) or `python-dotenv` to replace placeholders:
```bash
# Run tests with CI secrets
export DEV_URL="https://api.dev.example.com"
python -m pytest test_auth.py --env="dev" -s
```

**Python Example:**
```python
# Replace placeholders before loading config
import os
from pathlib import Path

def resolve_placeholders(config: str) -> str:
    for placehold in config.split():
        if placehold.startswith("${") and placehold.endswith("}"):
            var = placehold[2:-1]
            config = config.replace(placehold, os.getenv(var, ""))
    return config
```

---

### **4. Assertion Libraries**
- **Python:** Use `pytest` built-in assertions or `pytest-assertations`.
- **JavaScript:** `chai.js` for fluent assertions.
- **Schema Validation:** Use `jsonschema` (JS) or `marshmallow` (Python).

**Example (Python):**
```python
# schemas/user_schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string" }
  },
  "required": ["id", "name"]
}
```

**Assertion in Test:**
```python
from jsonschema import validate

def test_response_schema(response):
    validate(instance=response.json(), schema=open("schemas/user_schema.json"))
```

---

## **Requirements & Best Practices**
### **1. Schema Validation**
- Validate config files on load (e.g., using `jsonschema` or `pydantic`).
- Example validation rule:
  ```json
  // config_schema.json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "environments": { "type": "array", "items": { "type": "object" } },
      "modules": { "type": "array" }
    },
    "required": ["environments"]
  }
  ```

### **2. Environment Isolation**
- Use separate config files per environment (e.g., `dev_config.json`, `prod_config.json`).
- Avoid hardcoding sensitive data; use secrets managers (AWS Secrets Manager, HashiCorp Vault).

### **3. Dynamic Test Generation**
- Generate test cases dynamically from config (e.g., loop over `test_cases` in YAML).
  ```yaml
  # test_cases.yml
  test_cases:
    - name: "Login with valid credentials"
      params:
        username: "admin"
        password: "admin123"
    - name: "Login with invalid credentials"
      params:
        username: "guest"
        password: "wrong"
  ```

**Python Code:**
```python
import pytest
from config_loader import TestConfig

config = TestConfig("test_cases.yml")

@pytest.mark.parametrize("test_case", config.get("test_cases"))
def test_login(test_case):
    username = test_case["params"]["username"]
    # Execute test logic...
```

### **4. Logging & Debugging**
- Log config values at test startup for debugging:
  ```python
  import logging
  logging.debug(f"Loaded config: {config.data}")
  ```

### **5. CI/CD Integration**
- **GitHub Actions Example:**
  ```yaml
  # .github/workflows/test.yml
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - run: pip install pytest python-dotenv
        - run: |
            echo "DEV_URL=${{ secrets.DEV_URL }}" > .env
            pytest --env="dev" -v
  ```

---

## **Query Examples Summary Table**
| **Framework** | **Task**                          | **Example Command/Code**                          |
|---------------|-----------------------------------|--------------------------------------------------|
| **Python**    | Load config                        | `config = yaml.safe_load("test_config.yml")`     |
| **Python**    | Run tests with env                 | `pytest --env="dev" -s`                          |
| **JavaScript**| Load config                        | `const config = yaml.load("test_config.yml");`   |
| **JavaScript**| Run Mocha tests                    | `mocha --env=prod test_auth.js`                  |
| **CLI**       | Substitute placeholders           | `export DEV_URL="..." && python script.py`       |
| **CI/CD**     | Secrets management                 | `echo "URL=${{ secrets.PROD_URL }}" > .env`     |

---

## **Related Patterns**
1. **Page Object Model (POM)**
   - **Relation:** Use `Testing Configuration` to define dynamic locators (e.g., `${env}/login-page`) in POM classes.
   - **Use Case:** Web UI tests where selectors vary by environment.

2. **Factory Pattern**
   - **Relation:** Generate test data dynamically from config (e.g., user records in `test_data/config.yml`).
   - **Use Case:** Data-driven testing with reusable factories.

3. **Feature Flags**
   - **Relation:** Toggle test execution via config (e.g., `"enabled": false` for flaky tests).
   - **Use Case:** Skip tests in CI if a feature isn’t ready.

4. **Modular Testing (Gherkin)**
   - **Relation:** Define steps in `test_config.yml` and map to Gherkin feature files.
   - **Use Case:** Behavior-driven development (BDD) with dynamic scenarios.

5. **Environment Variables as Config**
   - **Relation:** Fallback to `.env` files if config keys are missing.
   - **Example:**
     ```yaml
     # test_config.yml
     api_url: "${API_URL:-https://default.example.com}"
     ```

---

## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| Placeholder not resolved            | Ensure variables are set in CI or `.env` files.                             |
| Schema validation fails             | Check config file syntax against `config_schema.json`.                     |
| Module not found                    | Verify `path` in `modules` points to the correct file.                      |
| Assertion errors                    | Log response data for debugging (`print(response.json())`).                 |
| Environment-specific failures       | Test locally with `export` or CLI flags before CI.                         |

---

## **Further Reading**
- [Python Pytest Configuration Docs](https://docs.pytest.org/)
- [Mocha.js Testing Framework](https://mochajs.org/)
- [JSON Schema Validation](https://json-schema.org/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)