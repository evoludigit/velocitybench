```markdown
# **"Virtual Machines Convention": How to Design APIs That Understand Your Business Logic**

*Stop writing APIs that feel like a series of random endpoints—build a system that thinks like your domain.*

You’ve spent months designing a robust backend. You’ve optimized your database schema, implemented microservices, and built a sleek API layer. But when your frontend or business logic team tries to consume it, they’re getting a tower of undocumented endpoints, inconsistent data shapes, and behavior that feels more like a "treat it like a black box" approach.

The problem? Your API—however technically sound—doesn’t directly *align with how your business operates*.

This is where the **Virtual Machines Convention** pattern comes in. Inspired by [Domain-Driven Design](https://domainlanguage.com/ddd/) and refined through lessons learned in enterprise systems, this pattern elevates your API design from a mere service layer to a **self-documenting interface for business domains**.

---

## **The Problem: APIs That Feel Like Puzzles**

Let’s walk through an example that most of us have experienced.

Consider a **ride-sharing app**—a seemingly simple domain, but with many subtleties. Here’s a typical API design for a basic "ride" functionality without any conventions:

```http
# Register a new user
POST /users
{
  "name": "Alice",
  "email": "alice@example.com",
  "wallet": { "balance": 100.00 }
}

# Create a new ride
POST /rides
{
  "userId": "abc123",
  "pickupLocation": { "lat": 37.7749, "lng": -122.4194 },
  "destination": { "lat": 40.7128, "lng": -74.0060 },
  "price": 25.50
}

# Confirm a ride
POST /rides/abc123/confirm
{
  "driverId": "def456"
}

# Get ride status
GET /rides/abc123
```

### **Why This Feels Wrong**
1. **No Semantic Clarity**
   - How does the frontend knows that `POST /rides` is only for *creating* rides? What about `PATCH /rides/abc123` for updates?
   - The `wallet` field under `/users` suggests financial operations, but how does it interact with rides?

2. **Hidden Workflow Logic**
   - A ride can’t be confirmed until a driver is assigned. This business rule isn’t reflected in the API structure.
   - What about "ride cancellation"? Should it be `/rides/abc123/cancel`?

3. **Inconsistent Data Shapes**
   - `POST /rides` expects `userId` and `price`, but a ride *also* needs payment processing. Is that handled under `/rides` or `/payments`?

4. **No "Virtual Machine" for Business Objects**
   - A ride isn’t just a JSON payload—it’s a **state machine**:
     - **Draft** → **Driver Assigned** → **In Progress** → **Completed** → **Cancelled**
   - Yet, the API treats it like a static resource.

---

## **The Solution: Designing APIs as Virtual Machines**

The **Virtual Machines Convention** treats your API endpoints as **controlled interfaces** for your domain’s core objects. It enforces:
- **Explicit workflows** (e.g., `ride.create()`, `ride.confirm()`, `ride.cancel()`).
- **Consistent data models** tied to business entities (e.g., `ride.status` instead of inferring it).
- **Idempotency and immutability** by default (or explicit mutability).
- **Self-documenting paths** that make sense to the business team.

### **Key Insights**
1. **Paths are Nouns + Verbs**
   Avoid RESTful "resource collection" anti-patterns like `/users` or `/rides`.
   Instead, use **action-oriented paths** that describe intent:
   ```http
   POST /rides/{rideId}/confirm
   ```

2. **Data Shapes Mirror Business Identity**
   Every API request includes the **entity’s identity** (`rideId`, `userId`) and **only the fields needed for the specific action**.

3. **Business Events = API Events**
   Changes to a ride (`ride.confirmed`, `ride.started`) are treated as **events**, not just mutations.

---

## **Implementation Guide: Ride-Sharing Example**

Let’s redesign the ride-sharing API using the Virtual Machines Convention.

### **Core Domain Objects**
We’ll define three "virtual machines":
1. **User**
2. **Ride**
3. **Payment**

#### **1. User Virtual Machine**
```http
# Register a new user
POST /users/register
{
  "name": "Alice",
  "email": "alice@example.com"
}

# Get user profile (read-only)
GET /users/{userId}
```

**Why This Works:**
- `/users/register` explicitly signals the **intent to create a user**.
- No wallet in the registration payload—it’s a separate action.

#### **2. Ride Virtual Machine**
```http
# Create a draft ride (starts in "pending" state)
POST /rides/{userId}/create
{
  "pickupLocation": { "lat": 37.7749, "lng": -122.4194 },
  "destination": { "lat": 40.7128, "lng": -74.0060 },
  "estimatedPrice": 25.50
}

# Confirm ride (assigns a driver)
POST /rides/{rideId}/confirm
{
  "driverId": "def456"
}

# Start ride (changes status to "in_progress")
POST /rides/{rideId}/start
{
  "startTime": "2024-06-12T12:00:00Z"
}

# Complete ride (finalizes payment)
POST /rides/{rideId}/complete
{
  "endTime": "2024-06-12T12:30:00Z"
}

# Cancel ride (optional)
POST /rides/{rideId}/cancel
{
  "reason": "cancelled_by_user"
}
```

**Why This Works:**
- Every action is **explicit** (`create`, `confirm`, `start`).
- The `rideId` is passed in the path, ensuring immutability for other fields.
- No "magic" operations—every step requires an explicit call.

#### **3. Payment Virtual Machine**
```http
# Initiate payment for a completed ride
POST /rides/{rideId}/payments/initiate
{
  "amount": 25.50,
  "paymentMethod": "credit_card"
}

# Refund partial payment (optional)
POST /rides/{rideId}/payments/refund
{
  "amount": 15.00
}
```

**Why This Works:**
- Payments are **tied to rides**, not separate from them.
- Only `completed` rides can be paid.

---

## **Code Examples: Backend Implementation**

Let’s implement this in **Node.js + Express**, using **Typescript** for type safety.

### **1. User Virtual Machine**
```typescript
// src/routes/users.ts
import { Router } from "express";
import { UserService } from "../services/UserService";

const router = Router();
const userService = new UserService();

router.post("/register", async (req, res) => {
  const { name, email } = req.body;

  try {
    const user = await userService.registerUser({ name, email });
    res.status(201).json(user);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

export default router;
```

### **2. Ride Virtual Machine**
```typescript
// src/routes/rides.ts
import { Router } from "express";
import { RideService } from "../services/RideService";

const router = Router();
const rideService = new RideService();

// Create a new ride (draft)
router.post("/:userId/create", async (req, res) => {
  const { userId } = req.params;
  const { pickupLocation, destination, estimatedPrice } = req.body;

  try {
    const ride = await rideService.createDraftRide(userId, {
      pickupLocation,
      destination,
      estimatedPrice,
    });
    res.status(201).json(ride);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Confirm ride (assign driver)
router.post("/:rideId/confirm", async (req, res) => {
  const { rideId } = req.params;
  const { driverId } = req.body;

  try {
    const ride = await rideService.confirmRide(rideId, driverId);
    res.json(ride);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Start ride
router.post("/:rideId/start", async (req, res) => {
  const { rideId } = req.params;
  const { startTime } = req.body;

  try {
    const ride = await rideService.startRide(rideId, { startTime });
    res.json(ride);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

export default router;
```

### **3. Payment Virtual Machine**
```typescript
// src/routes/payments.ts
import { Router } from "express";
import { PaymentService } from "../services/PaymentService";

const router = Router();
const paymentService = new PaymentService();

router.post("/rides/:rideId/payments/initiate", async (req, res) => {
  const { rideId } = req.params;
  const { amount, paymentMethod } = req.body;

  try {
    const payment = await paymentService.initiatePayment(rideId, {
      amount,
      paymentMethod,
    });
    res.status(201).json(payment);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

export default router;
```

---

## **Database Schema (PostgreSQL)**

To support this design, we need tables that mirror the **stateful nature of rides**:

```sql
-- Users table (simple)
CREATE TABLE users (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rides table (with state tracking)
CREATE TABLE rides (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'driver_assigned', 'in_progress', 'completed', 'cancelled')),
  pickup_location JSONB NOT NULL,
  destination JSONB NOT NULL,
  estimated_price DECIMAL(10, 2) NOT NULL,
  payment_amount DECIMAL(10, 2),
  driver_id UUID REFERENCES users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payments table (linked to rides)
CREATE TABLE payments (
  id UUID PRIMARY KEY,
  ride_id UUID REFERENCES rides(id),
  amount DECIMAL(10, 2) NOT NULL,
  method VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## **Common Mistakes to Avoid**

1. **Overloading Paths with Multiple Actions**
   ❌ Bad: `POST /rides/{rideId}` → should handle both updates and mutations.
   ✅ Better: `POST /rides/{rideId}/confirm`, `PATCH /rides/{rideId}` for updates.

2. **Letting the API Invent Business Rules**
   ❌ Bad: Users can "confirm" a ride without a driver assigned.
   ✅ Better: Enforce **validations at the API level** (e.g., `ride.status !== 'draft'`).

3. **Ignoring State Machines in the Database**
   ❌ Bad: Rides can have arbitrary statuses with no constraints.
   ✅ Better: Use **PostgreSQL CHECK constraints** or a state transition service.

4. **Assuming Frontend Devs Understand the Pattern**
   🔹 Always **document the "virtual machine"** as a simple diagram or OpenAPI spec.

---

## **Key Takeaways**

✅ **APIs Should Reflect Business Workflows**
   - Endpoints should map to **actions**, not just resources.

✅ **Explicit > Implicit**
   - Always **declare intent** in the path (e.g., `/rides/{rideId}/confirm`).

✅ **Data Models Tie to Business Identity**
   - Fields like `rideId` and `userId` should **never be optional** in relevant endpoints.

✅ **States Are First-Class Citizens**
   - Use **status fields** and **transition endpoints** (`/confirm`, `/start`).

✅ **Self-Documenting APIs**
   - If a dev asks "How do I [X]?", they should be able to **navigate to the correct path**.

✅ **Tradeoffs: Slightly Longer Paths = Fewer Headaches**
   - Yes, `/rides/{rideId}/confirm` is longer than `/rides/{rideId}`.
   - But it **reduces bugs** by making the API’s intent crystal clear.

---

## **Conclusion: APIs as Domain Contracts**

The **Virtual Machines Convention** shifts your API design from a **procedural** approach to a **declarative** one. Instead of exposing raw tables or collections, you’re building **a controlled interface for your business logic**.

This isn’t just about cleaner code—it’s about **reducing friction** between frontend, backend, and business teams. When your API feels like a **well-defined machine** rather than a chaotic black box, you’ll see:
- Fewer "how do I do X?" questions.
- Easier onboarding for new developers.
- Fewer runtime errors due to misaligned assumptions.

**Try it in your next project.** Start with one domain (e.g., "orders" or "payments"), and watch how the clarity improves.

---

### **Further Reading**
- [Domain-Driven Design by Eric Evans](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215)
- ["API Design Patterns" by J.J. Geewax](https://www.amazon.com/Design-Web-APIs-Architecture-Leverage/dp/1119279658)
- [RESTful API Design Rules](https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api)
```

---
**Final Note:** This pattern works best when adopted **early** in the project lifecycle. If your API already feels like a "data dump," refactoring may require some creative path aliases—but the payoff is worth it!