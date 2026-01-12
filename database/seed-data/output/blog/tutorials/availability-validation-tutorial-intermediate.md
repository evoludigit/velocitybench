```markdown
# **Availability Validation: Ensuring Data Integrity Before Commit**

*How to prevent race conditions, stale data, and inconsistent states in distributed systems—before they happen*

---

## **Introduction**

When building scalable backend systems, you’ve likely faced the classic **"lost update" problem**—where concurrent modifications to the same resource lead to data corruption. Maybe you’ve seen this in your own applications:

- A user’s bank account balance gets reduced twice because two transactions processed simultaneously.
- An e-commerce product’s inventory count drops below zero due to overlapping purchase requests.
- A flight seat reservation system allows overbooking because it doesn’t account for real-time availability.

These issues aren’t just theoretical—they cost businesses money, frustrate users, and expose your application to reputational damage. **Availability validation** is a pattern that helps avoid these problems by enforcing constraints *before* data is committed to the database.

In this guide, we’ll explore how this pattern works, where it’s applicable, and how to implement it effectively—with real-world examples in SQL and application code.

---

## **The Problem: When Race Conditions Ruin Your Data**

Let’s start with a concrete scenario: **airline seat reservations**.

### **Example: The Overbooking Nightmare**
Imagine an airline’s backend system allows passengers to book seats in a flight. But because the system is distributed (or even just multi-threaded), two requests can arrive simultaneously:

1. **Request 1:** Checks seat availability (100 seats left) → Books 20 seats → Updates database.
2. **Request 2:** Checks seat availability (still sees 100 seats left) → Books 30 seats → Updates database.

**Result:** 50 seats are now "booked," but the flight only has 40 available. **Overbooking!**

This is a **race condition**—where the outcome depends on the timing of concurrent operations. Worse, it happens silently because the system only checks availability at the moment of booking, not *after*.

### **Other Real-World Scenarios**
- **Banking:** Two debit transactions on the same account can overspend the balance.
- **E-commerce:** A product’s stock count isn’t atomically decremented, leading to negative inventory.
- **Game Leaderboards:** Concurrent updates can corrupt player stats.

### **Why Traditional Locks Aren’t Enough**
You might think:
*"Just use a database lock!"*

But locks introduce:
- **Performance bottlenecks** (contention on hot records).
- **Deadlocks** (if locks aren’t acquired in a consistent order).
- **Increased complexity** (lock timeouts, retries, and application logic).

Availability validation is a **preventive** approach—it ensures constraints are met *before* any locks are acquired or transactions begin.

---

## **The Solution: Availability Validation**

The **availability validation pattern** works like this:
1. **Check availability** (e.g., "Are there enough seats?")
2. **Reserve the resource** (e.g., "Mark seats as reserved")
3. **Validate again** (ensure no one else modified the data)
4. **Commit or roll back**

This creates a **"check-then-reserve-then-commit"** flow that prevents race conditions.

### **Key Principles**
✅ **Atomicity** – The entire operation succeeds or fails as a unit.
✅ **Isolation** – Other transactions can’t interfere mid-operation.
✅ **Consistency** – Data remains valid at all times.

---

## **Components of the Pattern**

### **1. Availability Check**
Before modifying data, verify if the operation is possible.
**Example:** *"Does the flight have enough seats?"*

### **2. Resource Reservation**
Temporarily "reserve" the resource (e.g., lock a row or set a flag).
**Example:** *"Mark 20 seats as reserved."*

### **3. Validation & Commit**
Re-check availability (to handle concurrent changes) and finalize the transaction.

### **4. Fallback (Rollback)**
If validation fails, undo any reservations.

---

## **Code Examples: Implementing Availability Validation**

Let’s build a **flight seat reservation system** using PostgreSQL and Python (FastAPI).

### **Database Schema**
```sql
CREATE TABLE flights (
    flight_id SERIAL PRIMARY KEY,
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    total_seats INT NOT NULL
);

CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    flight_id INT REFERENCES flights(flight_id),
    passenger_count INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'confirmed', 'cancelled'
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Step 1: Check Availability**
```python
def check_seat_availability(flight_id: int, passenger_count: int) -> bool:
    """Check if a flight has enough available seats."""
    with db_session() as session:
        flight = session.query(Flights).filter_by(id=flight_id).first()
        if not flight:
            return False

        # Calculate available seats (total - reserved)
        available_seats = flight.total_seats - session.query(func.count()).filter(
            Reservations.flight_id == flight_id,
            Reservations.status != 'cancelled'
        ).scalar()

        return available_seats >= passenger_count
```

### **Step 2: Reserve Seats (Optimistic Locking)**
To prevent race conditions, we use **optimistic concurrency control** (a version column).

```sql
ALTER TABLE reservations ADD COLUMN version INT DEFAULT 0;
```

Now, modify the reservation logic:
```python
from sqlalchemy.orm import Session
from sqlalchemy import func, select

def reserve_seats(flight_id: int, passenger_count: int, session: Session) -> bool:
    """Reserve seats for a flight, using optimistic locking."""
    # Check availability first
    available_seats = session.scalar(
        select(func.count())
        .where(
            Reservations.flight_id == flight_id,
            Reservations.status != 'cancelled'
        )
        .correlate(session)
    )

    if available_seats < passenger_count:
        return False

    # Try to reserve (optimistic lock)
    try:
        res = session.execute(
            """
            INSERT INTO reservations (flight_id, passenger_count, status)
            VALUES (:flight_id, :passenger_count, 'pending')
            ON CONFLICT (flight_id) DO UPDATE
            SET passenger_count = reservations.passenger_count + EXCLUDED.passenger_count,
                status = 'pending',
                reserved_at = CURRENT_TIMESTAMP
            WHERE reservations.version = EXCLUDED.version
            RETURNING version
            """,
            {"flight_id": flight_id, "passenger_count": passenger_count}
        )
        reserved_version = res.fetchone()[0]
        return True
    except Exception as e:
        session.rollback()
        return False
```

### **Step 3: Full Reservation Flow (FastAPI Endpoint)**
```python
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import datetime

app = FastAPI()

@app.post("/reserve-seats/")
async def reserve_seats(
    request: Request,
    flight_id: int,
    passenger_count: int,
    db: Annotated[Session, Depends(get_db)]
):
    """End-to-end seat reservation with availability validation."""
    if passenger_count <= 0:
        raise HTTPException(status_code=400, detail="Invalid passenger count")

    # Step 1: Check initial availability (could also use PessimisticLocking)
    if not check_seat_availability(flight_id, passenger_count):
        raise HTTPException(status_code=400, detail="Not enough seats")

    # Step 2: Attempt reservation (optimistic lock)
    if not reserve_seats(flight_id, passenger_count, db):
        raise HTTPException(status_code=409, detail="Race condition detected. Try again.")

    # Step 3: Final validation (to handle concurrent changes)
    available_seats = db.scalar(
        select(func.count())
        .where(
            Reservations.flight_id == flight_id,
            Reservations.status != 'cancelled'
        )
    )

    if available_seats < passenger_count:
        # Undo reservation
        db.execute(
            """
            UPDATE reservations
            SET status = 'cancelled'
            WHERE passenger_count = %s AND flight_id = %s
            """,
            (passenger_count, flight_id)
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Seats no longer available")

    # Step 4: Commit the reservation
    db.commit()
    return {"status": "success", "message": "Seats reserved"}
```

---

## **Implementation Guide: When and How to Use It**

### **When to Apply Availability Validation**
| Scenario | Suitable? | Notes |
|----------|-----------|-------|
| **Low-contention operations** (e.g., reading user profiles) | ❌ No | Overkill for simple read-heavy apps. |
| **High-contention operations** (e.g., seat reservations) | ✅ Yes | Critical for correctness. |
| **Distributed systems** (multiple services) | ✅ Yes | Prevents inconsistencies across services. |
| **Batch processing** (e.g., analytics) | ⚠️ Caution | May need bulk locking or queue-based processing. |

### **Tradeoffs to Consider**
| **Pros** | **Cons** |
|----------|----------|
| Prevents race conditions at the application level. | Slightly more complex than simple locks. |
| Reduces database contention (no long-held locks). | May require retry logic for failures. |
| Works well in distributed systems. | Not a silver bullet—still needs proper concurrency controls. |

### **Alternatives & Complements**
- **Pessimistic Locking (Database-level)** – Use when you *must* prevent concurrent modifications (e.g., financial transactions).
- **Distributed Locks (Redis)** – Good for distributed coordination but adds latency.
- **Eventual Consistency (CQRS)** – Accept temporary inconsistencies for scalability (use cautiously!).

---

## **Common Mistakes to Avoid**

### **1. Skipping the Final Validation**
❌ *Problem:* You reserve seats but don’t check if another transaction canceled them mid-operation.
✅ *Solution:* Always validate **before** committing.

### **2. Using Long Transactions**
❌ *Problem:* Holding a reservation for too long blocks other operations.
✅ *Solution:* Keep transactions short and use timeouts.

### **3. Ignoring Retry Logic**
❌ *Problem:* Race conditions can still happen—your code should retry on failure.
✅ *Solution:*
```python
def reserve_with_retry(flight_id, passenger_count, max_retries=3):
    for _ in range(max_retries):
        if reserve_seats(flight_id, passenger_count):
            return True
        time.sleep(0.1)  # Backoff
    return False
```

### **4. Not Handling Partial Failures**
❌ *Problem:* If a reservation fails mid-way, the system might leave data in an invalid state.
✅ *Solution:* Use **saga patterns** or **compensating transactions** for complex workflows.

### **5. Overusing Locks**
❌ *Problem:* Over-reliance on database locks kills performance.
✅ *Solution:* Use availability validation where possible, and only lock when necessary.

---

## **Key Takeaways**

✔ **Availability validation prevents race conditions** by ensuring constraints are met before committing.
✔ **Use optimistic locking (version columns)** to handle concurrent updates gracefully.
✔ **Always validate twice** (before reservation and before commit) to account for changes.
✔ **Keep transactions short** to avoid blocking other operations.
✔ **Combine with retries** for resilience against transient failures.
✔ **Don’t overuse locks**—prefer validation when possible.
✔ **Test under load**—race conditions often appear only in high-concurrency scenarios.

---

## **Conclusion**

Availability validation is a **powerful but often underutilized** pattern for maintaining data integrity in distributed systems. Unlike traditional locking, it:
- **Reduces contention** by avoiding long-held locks.
- **Works well in microservices** where database-level coordination is tricky.
- **Provides clear error handling** when constraints are violated.

However, it’s not a one-size-fits-all solution. **Use it where race conditions are a risk**, but don’t over-engineer simple read-heavy applications.

### **Next Steps**
- Try implementing availability validation in your own system where race conditions are a concern.
- Experiment with **pessimistic locking** vs. **optimistic locking** to see which fits your workload.
- Consider **saga patterns** if your transactions span multiple services.

By mastering this pattern, you’ll build systems that are **correct, scalable, and resilient**—even under heavy load.

---
**Happy coding!**
```