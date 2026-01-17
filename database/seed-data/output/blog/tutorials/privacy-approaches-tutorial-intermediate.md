```markdown
---
title: "Privacy Approaches Pattern: Designing Systems That Respect and Protect Data"
date: "2023-11-15"
tags: ["backend design", "database design", "api design", "privacy", "data protection"]
author: "Alex Stone"
---

# Privacy Approaches Pattern: Designing Systems That Respect and Protect Data

![Privacy approaches pattern illustration](https://example.com/privacy-pattern-illustration.png)

*Imagine you're building a healthcare dashboard for a major hospital chain. Patients entrust you with sensitive information—diagnosis records, genetic data, treatment histories. Or perhaps you're creating a financial platform handling account details and transaction logs. In these scenarios, privacy isn't just a checkbox; it's the foundation of trust. The wrong design choice could mean compliance violations, reputational damage, or worse—security breaches exposing thousands of records.*

As backend engineers, we're responsible for designing systems that not only meet functional requirements but also uphold strict privacy standards. The **Privacy Approaches Pattern** provides a framework for systematically addressing data privacy challenges in your application architecture. This pattern focuses on how we structure our data, control access, and process information in ways that minimize privacy risks while maintaining usability.

In this tutorial, we'll explore how to implement privacy protection through design patterns that go beyond simple encryption or access controls. We'll discuss three core approaches—data minimization, selective disclosure, and differential privacy—with practical examples in each case. By the end, you'll have actionable strategies to apply to your next system design, whether you're working with PII, healthcare data, or any other sensitive information.

---

## The Problem: When Privacy Design Fails

Before diving into solutions, let's examine what goes wrong when we neglect privacy in our systems. Here are common scenarios where poor privacy approaches create significant challenges:

### 1. The Blob Approach
Many systems treat data with one-size-fits-all security:
```sql
-- Classic over-permissive schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    ssn VARCHAR(11),  -- Social security number
    credit_card_number VARCHAR(16),
    medical_history TEXT,
    -- ... 50+ other fields
    created_at TIMESTAMP
);
```
*Problems:*
- Every consumer of the database has access to everything
- No audit trail of who accesses sensitive data
- Compliance violations when data is exported or logged

### 2. The "Just Mask It Later" Syndrome
```python
# Frontend code that "fixes" privacy problems
def get_user_data(user_id):
    raw_data = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    # Scrub sensitive fields
    if role == "admin":
        return raw_data  # Oops, forgot to mask
    else:
        return {k: v for k, v in raw_data.items()
                if k not in ["ssn", "credit_card_number"]}
```
*Problems:*
- Security decisions are made late in the pipeline
- Masking happens inconsistently
- Security logic leaks through logging/system monitoring

### 3. The Compliance Black Hole
Many developers treat privacy compliance as an afterthought:
- "We'll add encryption when we hit GDPR"
- "We'll anonymize later if needed for reporting"
- "Our database team handles all the security"

This leads to:
- Last-minute feature changes that violate privacy
- Technical debt accumulating in security
- Inconsistent protection across different data types

### The Reputation Risk
Beyond immediate technical problems, poor privacy design can:
- Damage user trust permanently
- Lead to regulatory fines (GDPR: up to 4% of global revenue)
- Create legal liabilities for data breaches
- Force costly re-architecting when privacy becomes a concern

---

## The Solution: Privacy Approaches Pattern

The Privacy Approaches Pattern is an architectural framework that addresses privacy concerns at the system design level. It consists of three complementary strategies:

1. **Data Minimization**: Only collect and store what's absolutely necessary
2. **Selective Disclosure**: Control exactly what data is visible to different users
3. **Differential Privacy**: Add controlled noise to data to prevent identification

These approaches work together to create a privacy-preserving architecture where data protection is baked into the system rather than bolted on later.

---

## Components/Solutions: Practical Implementations

Let's explore each approach with code examples and architectural patterns.

### 1. Data Minimization: The Precision Principle

*Principle*: "Only collect personal data that is necessary for the specified purpose."

**Implementation Strategies:**

#### a) Schema Design for Minimization

```sql
-- Before (over-collecting)
CREATE TABLE patient_visits (
    visit_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id),
    diagnosis TEXT,  -- Often contains sensitive info
    treatment_plans TEXT,
    billing_info JSONB,  -- Contains credit card details
    notes TEXT,  -- May include protected health info
    visited_at TIMESTAMP
);

-- After (minimized)
CREATE TABLE patient_visits (
    visit_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id),
    diagnosis_code VARCHAR(10),  -- Standardized codes
    treatment_plan_id INT REFERENCES treatment_plans(id),
    billing_id INT REFERENCES billing_records(id),
    visit_type VARCHAR(20),  -- Emergency, routine, etc.
    visited_at TIMESTAMP,
    visit_duration INTERVAL,
    -- Remove all unneeded fields
);
```

#### b) Temporal Data Minimization

```python
# Only store data for the required retention period
class DataRetentionManager:
    def __init__(self, table_name, retention_days):
        self.table_name = table_name
        self.retention_days = retention_days

    def prune_old_data(self):
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        affected_rows = self._delete_old_data(cutoff_date)
        logger.info(f"Pruned {affected_rows} old records from {self.table_name}")

    def _delete_old_data(self, cutoff_date):
        # Implement database-specific deletion
        # For PostgreSQL:
        with connection.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self.table_name} WHERE created_at < %s RETURNING id",
                (cutoff_date,)
            )
            return cur.fetchall()
```

#### c) Field-Level Minimization

```python
# Example of a normalized schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email_hash BYTEA,  -- Just the hash, not the raw email
    email_verification_token VARCHAR(64),
    password_hash BYTEA,
    created_at TIMESTAMP
);

CREATE TABLE user_profiles (
    user_id INT REFERENCES users(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    -- Only store what's needed for the profile
    PRIMARY KEY (user_id)
);
```

**Tradeoff Considerations:**
- *Pros*: Reduced attack surface, easier compliance, better performance
- *Cons*: May require application changes to work with less data, might need to join tables more frequently

---

### 2. Selective Disclosure: Row-Level Security

*Principle*: "Different users should see different subsets of data based on their roles."

**Implementation Strategies:**

#### a) Database-Level Row-Level Security (RLS)

```sql
-- Enable RLS on a table
ALTER TABLE patient_records ENABLE ROW LEVEL SECURITY;

-- Create a policy for doctors
CREATE POLICY doctor_view_policy ON patient_records
    USING (doctor_id = current_setting('app.current_doctor_id')::int
           OR patient_id = current_setting('app.current_patient_id')::int);

-- Create a policy for admins
CREATE POLICY admin_view_policy ON patient_records
    FOR ALL
    USING (true);
```

#### b) Application-Level Selective Disclosure

```python
# Python example using dependency injection
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class UserContext:
    user_id: int
    roles: List[str]

class DataAccessService:
    def __init__(self, user_context: UserContext):
        self.user_context = user_context

    def get_related_records(self, base_record_id: int):
        # Apply selective disclosure logic
        if self.user_context.roles == ['admin']:
            return self._get_all_related_records(base_record_id)
        elif 'doctor' in self.user_context.roles:
            # Only return records for their patients
            return self._get_patient_related_records(base_record_id,
                self._get_patient_ids_for_doctor())
        else:
            return self._get_public_related_records(base_record_id)

    # ... implementation methods
```

#### c) Column-Level Security with Views

```sql
-- Basic view for doctors
CREATE VIEW doctor_patient_view AS
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    -- Exclude sensitive PII
    pv.diagnosis,
    pv.treatment_plan
FROM patients p
JOIN patient_visits pv ON p.patient_id = pv.patient_id
WHERE p.doctor_id = current_setting('app.current_doctor_id')::int;

-- View with computed columns
CREATE VIEW billing_summary AS
SELECT
    patient_id,
    SUM(amount) as total_spent,
    COUNT(*) as visit_count
FROM billing_records
GROUP BY patient_id;
```

**Tradeoff Considerations:**
- *Pros*: Precise access control, better performance (fewer rows scanned), auditability
- *Cons*: Complex schema, potential performance overhead for policies, developer learning curve

---

### 3. Differential Privacy: Adding Noise to Data

*Principle*: "Distort data slightly to prevent identification while maintaining utility."

**Implementation Strategies:**

#### a) Simple Noise Injection

```python
import numpy as np

def add_differential_noise(data: List[float], epsilon: float = 1.0) -> List[float]:
    """
    Add Laplace noise to numerical data

    Args:
        data: List of numerical values
        epsilon: Privacy budget (higher = more noise = more privacy)
    """
    sensitivity = 1.0  # Maximum change one record can make
    scale = sensitivity / epsilon

    return [val + np.random.laplace(0, scale) for val in data]

# Usage example
original_data = [123000, 150000, 98000]  # Salary data
private_data = add_differential_noise(original_data, epsilon=0.5)
```

#### b) Count Sketch with Differential Privacy

```python
from collections import defaultdict
import math

class PrivateCounter:
    def __init__(self, epsilon: float):
        self.epsilon = epsilon
        self.sensitivity = 1.0  # Each item contributes at most 1 to count
        self.scale = (self.sensitivity / self.epsilon)

    def private_count(self, items: list) -> int:
        """Compute a differentially private count of items"""
        true_count = len(items)
        noise = int(round(np.random.laplace(0, self.scale)))
        return max(0, true_count + noise)

    def private_top_k(self, items: list, k: int) -> dict:
        """Find top-k items with private counts"""
        counts = defaultdict(int)
        for item in items:
            counts[item] += 1

        # Apply noise to each count
        private_counts = {item: counts[item] + int(round(np.random.laplace(0, self.scale)))
                         for item in counts}

        # Sort and return top-k
        return dict(sorted(private_counts.items(),
                          key=lambda x: x[1], reverse=True)[:k])
```

#### c) Differential Privacy in Aggregations

```python
# PostgreSQL extension for differentially private queries
-- Install: CREATE EXTENSION pgdifferentialprivacy;

SELECT dp_approx_count(*)
FROM user_visits
WHERE visit_date = '2023-01-01'
WITH epsilon = 1.0;

-- More complex example with parameterized privacy
SELECT dp_approx_sum(revenue)
FROM transactions
WHERE month = '2023-01'
WITH epsilon = 0.5,
     sensitivity = 100000  -- Max possible sum for one month
     ;
```

**Tradeoff Considerations:**
- *Pros*: Provable privacy guarantees, prevents certain types of re-identification
- *Cons*: Reduced data utility, complex parameter tuning, performance overhead for noise calculation
- *When to use*: For aggregate statistics, research data, or when precise individual data isn't needed

---

## Implementation Guide: Putting It All Together

Here's a step-by-step approach to implementing privacy approaches in your system:

### 1. Privacy-First Requirements Gathering

Before writing code, conduct a privacy impact assessment:

```python
# Example privacy assessment questionnaire
def assess_privacy_requirements(data_type):
    questions = {
        "legally_required": "Is this data legally required to be stored?",
        "retention_period": "How long must we retain this data?",
        "sharing_parties": "Who must we share this data with?",
        "access_requirements": "What access patterns are expected?",
        "compliance_standards": "What regulations apply?",
        "utility_requirements": "What analysis will be performed?",
        "minimization_feasible": "Can we design for data minimization?"
    }

    # Implement this as a form or interview process
    return {q: input(f"{q}: ") for q in questions.keys()}
```

### 2. Schema Design with Privacy in Mind

1. Start with minimal fields (apply "precision principle")
2. Consider temporal partitioning for old data
3. Normalize sensitive data into separate tables
4. Document all sensitive fields

```sql
-- Example schema diagram documentation
/*
PATIENTS Table (minimal PII)
  - id (primary key)
  - hashed_email (hashed email address)
  - encryption_key_id (reference to key vault)
  - account_status (active/inactive)

PATIENT_PROFILES (non-sensitive)
  - patient_id (foreign key)
  - first_name
  - last_name
  - preferred_language

HEALTH_RECORDS (sensitive)
  - record_id (primary key)
  - patient_id (foreign key)
  - doctor_id (foreign key)
  - diagnosis (structured codes)
  - treatment_plans (reference to treatments table)
  - created_at
*/
```

### 3. Access Control Implementation

1. Implement at least two levels of security:
   - Database-level (RLS)
   - Application-level (policy enforcement)

2. Use a central auth system:
```python
# Example auth context setup
from fastapi import Request
from starlette.contextmanager import contextmanager

@contextmanager
def set_auth_context(request: Request):
    user = request.state.user  # From JWT/OAuth etc.
    current.doctor_id = None

    if user.role == 'doctor':
        current.doctor_id = user.doctor_id
    elif user.role == 'patient':
        current.patient_id = user.user_id

    yield

    # Clean up
    del current.doctor_id
    del current.patient_id
```

### 4. Data Processing with Privacy

1. Apply differential privacy to sensitive aggregations
2. Use field-level encryption for sensitive fields
3. Implement proper logging of data access

```python
# Example of field-level encryption/decryption
from cryptography.fernet import Fernet

class FieldEncryptor:
    def __init__(self, key_path: str):
        self.key = load_key(key_path)

    def encrypt(self, field_value: str) -> str:
        return Fernet(self.key).encrypt(field_value.encode()).decode()

    def decrypt(self, encrypted_value: str) -> str:
        return Fernet(self.key).decrypt(encrypted_value.encode()).decode()

# Usage in model
class UserModel:
    def __init__(self, db_connection, field_encryptor):
        self.db = db_connection
        self.encryptor = field_encryptor

    def create(self, user_data):
        encrypted_ssn = self.encryptor.encrypt(user_data['ssn'])
        self.db.execute(
            "INSERT INTO users (email, ssn_encrypted) VALUES (%s, %s)",
            (user_data['email'], encrypted_ssn)
        )
```

### 5. Monitoring and Auditing

Implement comprehensive logging of data access:

```python
# Example audit logging middleware
from datetime import datetime
import logging
from functools import wraps

logger = logging.getLogger("audit")

def audit_logged(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()  # From security context
        result = func(*args, **kwargs)

        # Log the access pattern
        if hasattr(func, '__name__'):
            access_pattern = f"{func.__module__}.{func.__name__}"
        else:
            access_pattern = str(func)

        logger.info(
            f"AUDIT {user.id} {user.role} {access_pattern} "
            f"RESOURCE {kwargs.get('resource_id', 'N/A')}"
        )

        return result
    return wrapper

# Example usage
class PatientService:
    @audit_logged
    def get_medical_history(self, patient_id: int, doctor_id: int):
        # Implementation...
```

---

## Common Mistakes to Avoid

1. **Over-collecting Data**
   - *Mistake*: Keeping all possible fields from forms
   - *Solution*: Implement a data minimization review process
   - *Check*: For every field, ask "Is this needed for our primary use case?"

2. **Inconsistent Security Models**
   - *Mistake*: Mixing database permissions with application logic
   - *Solution*: Standardize on one approach (database RLS or application policies)
   - *Check*: Ensure your access control layer is the single source of truth

3. **Ignoring Temporal Data**
   - *Mistake*: Keeping old data indefinitely
   - *Solution*: Implement automatic data retention policies
   - *Check*: Document and enforce retention periods

4. **Underestimating Differential Privacy**
   - *Mistake*: Applying DP only to small datasets
   - *Solution*: Start with small privacy budgets and increase as needed
   - *Check*: Measure the impact of noise on your analysis

5. **Security Through Obscurity**
   - *Mistake*: Hiding security in undocumented "features"
   - *Solution*: Make privacy design explicit and transparent
   - *Check*: Document