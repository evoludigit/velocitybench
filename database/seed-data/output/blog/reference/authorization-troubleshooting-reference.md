# **[Pattern] Authorization Troubleshooting: Reference Guide**

---
## **Overview**
Authorization failures can disrupt application workflows, exposing security gaps or misconfigurations. This guide provides a structured approach to debugging authorization issues in distributed systems, APIs, and identity providers. It covers common error scenarios, logging analysis, role-based access control (RBAC) troubleshooting, attribute-based access control (ABAC), and integration checks with identity management systems (e.g., OAuth2, OpenID Connect). Whether dealing with **403 Forbidden** errors, inconsistent access policies, or identity provider misconfigurations, this pattern helps isolate root causes and apply targeted fixes while maintaining security best practices.

---

## **Key Concepts & Implementation Details**
### **1. Common Authorization Failure Scenarios**
| Scenario               | Description                                                                 | Common Root Causes                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **403 Forbidden**      | User lacks permissions for requested resource.                            | Missing roles, incorrect policy bindings.  |
| **401 Unauthorized**   | Invalid or expired credentials.                                             | Token expiration, cache issues.             |
| **500 Internal Error** | Server-side authorization logic failure (e.g., policy engine crash).       | Misconfigured RBAC/ABAC rules, dependency failures. |
| **Request Rejected**   | Identity provider (IdP) rejects authentication/authorization.               | IdP misconfiguration, revoked tokens.       |

### **2. Authorization Flow Components**
Authorization relies on these components working in tandem:
- **Client** (e.g., browser, mobile app, service account)
- **Identity Provider (IdP)** (e.g., OAuth2 auth server, LDAP, SAML)
- **Resource Server** (API/gateway enforcing policies)
- **Policy Engine** (e.g., Open Policy Agent, AWS IAM)
- **Data Stores** (role mappings, attribute stores)

---

## **Schema Reference**
### **1. Authorization Error Response Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "error": {
      "type": "string",
      "enum": ["unauthorized", "forbidden", "invalid_token", "policy_violation"]
    },
    "error_code": {
      "type": "string",
      "format": "uuid"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "request_id": {
      "type": "string"
    },
    "context": {
      "type": "object",
      "properties": {
        "user": {
          "type": "string"
        },
        "resource": {
          "type": "string"
        },
        "action": {
          "type": "string"
        },
        "missing_roles": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "policy_id": {
          "type": "string"
        }
      }
    },
    "trace_id": {
      "type": "string"
    }
  }
}
```

### **2. Policy Evaluation Decision Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "evaluation": {
      "type": "string",
      "enum": ["ALLOW", "DENY", "NOT_APPLICABLE"]
    },
    "policy_name": {
      "type": "string"
    },
    "request": {
      "type": "object",
      "properties": {
        "subject": {
          "type": "string"
        },
        "resource": {
          "type": "string"
        },
        "action": {
          "type": "string"
        },
        "attributes": {
          "type": "object"
        }
      }
    },
    "rulesApplied": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "rule_id": {
            "type": "string"
          },
          "description": {
            "type": "string"
          },
          "result": {
            "type": "string"
          }
        }
      }
    }
  }
}
```

---

## **Query Examples**
### **1. Debugging 403 Forbidden Errors**
**Scenario**: A user with role `admin` is denied access to `/api/v1/data`.
**Steps**:
1. **Log Analysis**:
   ```bash
   grep "403 Forbidden" /var/log/api-gateway.log | \
     awk '{print $12}' | \
     sort | uniq -c | sort -nr
   ```
2. **Policy Check**:
   ```bash
   # Query Open Policy Agent (OPA) for rule violations
   curl -X POST http://localhost:8181/v1/data/decision \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "request": {
           "subject": "user:123",
           "resource": "/api/v1/data",
           "action": "read"
         }
       }
     }'
   ```

### **2. Token Validation Issues**
**Scenario**: `401 Unauthorized` persisted after token refresh.
**Steps**:
1. **Token Introspection**:
   ```bash
   curl -X POST https://auth-server.com/introspect \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "token={JWT_TOKEN}&client_id=client-123&client_secret=secret"
   ```
2. **IdP Health Check**:
   ```bash
   curl -v https://auth-server.com/.well-known/openid-configuration
   ```

### **3. RBAC Role Mismatch**
**Scenario**: Role not assigned in IdP but works locally.
**Steps**:
1. **Verify Role Assignment**:
   ```bash
   # Example for LDAP
   ldapsearch -x -H ldap://ldap-server:389 \
     -D "cn=admin,dc=example,dc=com" \
     -w password \
     -b "dc=example,dc=com" \
     "(uid=user123)" roles
   ```
2. **Sync Roles**:
   ```bash
   # Trigger role sync (e.g., AWS Cognito)
   aws cognito-idp admin-update-user-attributes \
     --user-pool-id us-east-1_abc123 \
     --username user123 \
     --user-attributes Name=custom:roles,Value=["admin"]
   ```

---

## **Requirements for Implementation**
### **1. Logging & Monitoring**
- **Structured Logging**: Use JSON logs for `error_code`, `context`, and `trace_id`.
- **Metrics**: Track authorization latency (`p99`, `p50`) and rejection rates.
- **Alerting**: Trigger alerts for repeated `403`/`401` errors (e.g., Prometheus + Alertmanager).

### **2. Policy Testing**
- **Unit Tests**: Mock policy engine decisions (e.g., using OPA’s `--server` mode).
- **Integration Tests**: Validate IdP token refresh and revocation flows.

### **3. IdP-Specific Checks**
| IdP          | Troubleshooting Command                          |
|--------------|--------------------------------------------------|
| **OAuth2**   | `curl -X POST {REDIRECT_URI}?code={CODE}&grant_type=authorization_code` |
| **SAML**     | `curl -X POST https://idp.example.com/SSOService -d "<saml:AuthnRequest..."` |
| **AWS IAM**  | `aws iam list-attached-user-policies --user-name user123` |

### **4. Policy Engine Configuration**
- **OPA (Open Policy Agent)**:
  ```bash
  # Example policy to deny access without explicit role
  allow {
    input.request.subject.roles._contains("admin")
  } else {
    deny
  }
  ```
- **AWS IAM**:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::bucket/*",
        "Condition": {
          "StringEquals": {
            "aws:PrincipalTag/Role": "admin"
          }
        }
      }
    ]
  }
  ```

---

## **Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **[Authentication Troubleshooting]** | Debug token issuance, expiration, and refresh flows.                      |
| **[API Gateway Authentication]**      | Configure and validate auth headers (JWT, API keys).                       |
| **[Distributed Tracing]**            | Trace requests across services for latency/authorization delays.            |
| **[Policy as Code]**               | Define policies in declarative formats (e.g., OPA, Terraform IAM modules). |
| **[IdP Federation]**               | Troubleshoot cross-IdP authentication (e.g., SAML bridges).                |

---
## **Further Reading**
- [OPA Documentation](https://www.openpolicyagent.org/docs/latest/)
- [AWS IAM Policy Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

---
**Last Updated**: `{DATE}`
**Version**: `1.2`