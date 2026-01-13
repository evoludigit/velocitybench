---
# **[Pattern] Reference Guide: Hospitality Domain Patterns**

---
## **Overview**
Hospitality Domain Patterns (HDP) provide a structured approach to modeling and implementing software systems for hotels, resorts, and other hospitality enterprises. These patterns address core challenges—such as reservation management, guest lifecycle, pricing, and revenue optimization—while ensuring scalability, maintainability, and compliance with industry standards (e.g., **IATA, ISO 15709, or Open Travel Alliance**).

HDP emphasizes **domain-driven design** principles, separating business logic from technical infrastructure. Key benefits include:
✔ **Modularity**: Isolate subdomains (e.g., reservations, housekeeping) for independent evolution.
✔ **Flexibility**: Adaptable to proprietary (e.g., hotel chains) or third-party systems (e.g., **PMS, CRS, or OTA integrations**).
✔ **Standards Compliance**: Aligns with **EDIFACT, XML schema (HOTELS XML), or RESTful APIs** for interoperability.
✔ **Performance**: Optimized for high-concurrency scenarios (e.g., parallel bookings, dynamic pricing).

This guide covers **conceptual models, schema references, query patterns, and integration best practices** to implement HDP effectively.

---

---
## **Schema Reference**
Below are core domain entities and their relationships. Use these as foundational schemas for databases (e.g., PostgreSQL, MongoDB) or message brokers (e.g., Kafka, RabbitMQ).

| **Entity**               | **Fields**                                                                       | **Description**                                                                                     | **Examples**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Guest**                | `guestId` (UUID), `firstName`, `lastName`, `email`, `phone`, `createdAt`       | Represents a guest or customer record.                                                               | `guestId: abc123-xyz-456`, `firstName: "John"`, `email: "john@hotel.com"`                      |
| **Reservation**          | `reservationId` (UUID), `guestId`, `checkInDate`, `checkOutDate`, `status`        | Core reservation record with lifecycle (e.g., **confirmed, cancelled, checked-in**).                | `status: "confirmed"`, `checkInDate: "2024-05-15"`                                                |
| **RoomType**             | `roomTypeId`, `name`, `description`, `basePricePerNight`, `amenities`          | Defines room categories (e.g., **Standard, Suite, Luxury**).                                       | `amenities: ["WiFi", "Minibar", "Balcony"]`                                                      |
| **Room**                 | `roomId`, `roomTypeId`, `roomNumber`, `floor`, `status` (`available`, `booked`) | Instance of a room in a hotel.                                                                    | `roomNumber: "101"`, `status: "available"`                                                        |
| **Booking**              | `bookingId`, `reservationId`, `roomId`, `adults`, `children`, `totalPrice`       | Maps a reservation to a specific room and guest count.                                              | `adults: 2`, `children: 1`, `totalPrice: $349.99`                                                |
| **Payment**              | `paymentId`, `bookingId`, `amount`, `method` (`credit_card`, `paypal`, `cash`), `status` | Tracks payment transactions and refunds.                                                            | `method: "credit_card"`, `status: "completed"`                                                   |
| **RatePlan**             | `ratePlanId`, `name`, `description`, `price`, `discountPercentage`, `validityPeriod` | Defines pricing tiers (e.g., **Weekend Discount, Last-Minute Deal**).                               | `discountPercentage: 15%`, `validityPeriod: "Weekend"`                                            |
| **GuestHistory**         | `guestId`, `checkInDate`, `checkOutDate`, `totalSpent`, `loyaltyPoints`          | Audit trail for guest interactions and spending.                                                    | `totalSpent: $1250`, `loyaltyPoints: 150`                                                        |
| **Promotion**            | `promotionId`, `name`, `description`, `discount`, `startDate`, `endDate`          | Time-bound offers (e.g., **Black Friday Sale**).                                                    | `discount: $50 off`, `startDate: "2024-11-20"`                                                  |
| **Housekeeping**         | `roomId`, `status` (`clean`, `dirty`, `under_maintenance`), `lastInspection`    | Tracks room maintenance and cleaning status.                                                       | `status: "clean"`, `lastInspection: "2024-05-14T10:00:00Z"`                                      |
| **CheckIn**              | `checkInId`, `bookingId`, `guestId`, `roomId`, `arrivalTime`, `status`             | Records guest check-in events.                                                                    | `status: "completed"`, `arrivalTime: "14:30"`                                                    |
| **CheckOut**             | `checkOutId`, `bookingId`, `guestId`, `roomId`, `departureTime`, `status`        | Records guest departure.                                                                           | `status: "completed"`, `departureTime: "09:00"`                                                  |
| **Review**               | `reviewId`, `bookingId`, `guestId`, `rating` (1-5), `comment`, `published`         | Guest feedback on stay.                                                                           | `rating: 5`, `comment: "Excellent service!"`                                                     |
| **CancellationPolicy**   | `policyId`, `reservationId`, `cancellationFee`, `deadline`                     | Defines cancellation terms (e.g., **24-hour rule**).                                               | `cancellationFee: 50%`, `deadline: "12:00 AM"`                                                  |
| **Integration**          | `integrationId`, `provider` (e.g., `PMS`, `CRS`, `OTA`), `apiEndpoint`, `status` | Tracks external system connections (e.g., **Cloudbeds, Booking.com**).                               | `provider: "Booking.com"`, `status: "active"`                                                    |

---
### **Relationships**
1. **One-to-Many**:
   - `Guest` **has many** `Reservations`.
   - `Reservation` **has one** `Booking` (one room per reservation).
   - `RoomType` **has many** `Rooms`.
   - `RatePlan` **belongs to** `RoomType`.

2. **Many-to-Many** (via junction tables):
   - `Reservation` **can apply to** multiple `Promotions`.
   - `Booking` **can involve** multiple `Payments`.

3. **Lifecycle States**:
   - `Reservation` → `checkIn` → `CheckOut` → `CancellationPolicy`.
   - `Room` status transitions: `available` → `booked` → `clean` → `dirty`.

---
## **Query Examples**
### **1. Reservations for a Guest**
**Query (SQL):**
```sql
SELECT r.reservationId, r.checkInDate, r.checkOutDate, rt.name AS roomType,
       b.roomId, b.totalPrice
FROM Reservations r
JOIN Bookings b ON r.reservationId = b.reservationId
JOIN Rooms rm ON b.roomId = rm.roomId
JOIN RoomTypes rt ON rm.roomTypeId = rt.roomTypeId
WHERE r.guestId = 'abc123-xyz-456';
```
**Query (MongoDB):**
```javascript
db.reservations.find(
  { guestId: "abc123-xyz-456" },
  {
    reservationId: 1,
    checkInDate: 1,
    checkOutDate: 1,
    booking: {
      $elemMatch: {
        roomId: 1,
        totalPrice: 1,
        "room.roomType": 1
      }
    }
  }
);
```

### **2. Available Rooms for a Date Range**
**Query (SQL):**
```sql
SELECT rm.roomId, rt.name, rt.basePricePerNight, hk.status
FROM Rooms rm
JOIN RoomTypes rt ON rm.roomTypeId = rt.roomTypeId
LEFT JOIN Housekeeping hk ON rm.roomId = hk.roomId
WHERE rm.status = 'available'
  AND NOT EXISTS (
    SELECT 1 FROM Bookings b
    WHERE b.roomId = rm.roomId
      AND (checkInDate < '2024-05-15' AND checkOutDate > '2024-05-15')
  );
```

### **3. Applied Promotions for a Booking**
**Query (SQL):**
```sql
SELECT p.promotionId, p.name, p.discount
FROM Bookings b
JOIN Reservations r ON b.reservationId = r.reservationId
JOIN Promotions rp ON r.reservationId = rp.reservationId
WHERE r.checkInDate BETWEEN p.startDate AND p.endDate
  AND b.bookingId = '789def-ghi-123';
```

### **4. Guest Loyalty Points Calculation**
**Query (SQL):**
```sql
SELECT gh.guestId, SUM(b.totalPrice * 0.01) AS loyaltyPoints
FROM GuestHistory gh
JOIN Reservations r ON gh.guestId = r.guestId
JOIN Bookings b ON r.reservationId = b.reservationId
WHERE gh.checkInDate >= DATEADD(year, -1, GETDATE())
GROUP BY gh.guestId;
```

### **5. Real-Time Room Status Check (WebSocket Example)**
**Event (JSON):**
```json
{
  "event": "room_status_update",
  "roomId": "101",
  "status": "dirty",
  "updatedAt": "2024-05-14T16:45:00Z",
  "inspectedBy": "housekeeping@hotel.com"
}
```

---
## **Best Practices**
1. **Idempotency for Reservations**:
   - Use **idempotency keys** (e.g., `reservationId`) to prevent duplicate bookings via APIs.
   - Example:
     ```http
     PATCH /reservations/abc123-xyz-456
     Header: Idempotency-Key: "unique-session-12345"
     Body: { "status": "cancelled" }
     ```

2. **Optimistic Concurrency Control**:
   - Track `version` or `lastUpdated` fields to handle race conditions during room updates.
   - Example:
     ```sql
     UPDATE Rooms
     SET status = 'booked', version = version + 1
     WHERE roomId = '101' AND version = 2;
     ```

3. **Dynamic Pricing Integration**:
   - Cache rate plans in Redis with **TTL** (e.g., 1 hour) to reduce database load.
   - Example (Python):
     ```python
     import redis
     r = redis.Redis()
     rate_plan_cache_key = f"rate_plan:{roomTypeId}"
     rate_plan = r.get(rate_plan_cache_key)
     if not rate_plan:
         rate_plan = fetch_from_db(roomTypeId)
         r.setex(rate_plan_cache_key, 3600, rate_plan)
     ```

4. **Audit Logging**:
   - Log all state changes (e.g., `status: "booked" → "cancelled"`) in a **separate `AuditLog` table**.
   - Example:
     ```sql
     INSERT INTO AuditLog (entityType, entityId, oldValue, newValue, changedBy, timestamp)
     VALUES ('Reservation', 'abc123', 'confirmed', 'cancelled', 'system', NOW());
     ```

5. **OTA API Sync**:
   - Use **Change Data Capture (CDC)** tools (e.g., Debezium) to sync reservations between **PMS (Property Management System)** and **CRS (Central Reservation System)**.
   - Example Kafka topic:
     ```json
     {
       "topic": "hotel.reservationsync",
       "partition": 0,
       "message": {
         "reservationId": "abc123",
         "action": "UPDATE",
         "changes": {
           "checkOutDate": "2024-05-16"
         }
       }
     }
     ```

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Risk**                                                                 | **Mitigation**                                                                                     |
|---------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Race Conditions in Room Booking**   | Overbooking due to concurrent requests.                                  | Use **pessimistic locks** (SQL `SELECT FOR UPDATE`) or **distributed locks** (Redis).                 |
| **Inconsistent Rate Plans**          | Stale pricing data across systems.                                      | Sync rate plans via **event sourcing** or **CQRS**.                                               |
| **API Latency in OTA Integrations**  | Slow responses from third-party APIs (e.g., Booking.com).              | Implement **circuit breakers** (e.g., Hystrix) and **local caching**.                               |
| **Loyalty Points Calculation Errors**| Incorrect points for promotions or cancellations.                        | Use **transactional outbox pattern** to track points in a separate service.                         |
| **Compliance Violations**            | Failure to meet **GDPR** or **PCI-DSS** for guest data.               | Encrypt PII (e.g., `phone`, `credit_card`) and tokenize sensitive fields.                           |

---

## **Related Patterns**
1. **[Event Sourcing for Reservations]**
   - Replace relational snapshots with an **append-only log** of reservation events (e.g., `ReservationCreated`, `StatusUpdated`).
   - **Use Case**: Audit trails, time-travel debugging.
   - **Tools**: EventStoreDB, Apache Kafka.

2. **[CQRS for Housekeeping]**
   - Separate **write models** (e.g., `Housekeeping` updates) from **read models** (e.g., `RoomStatusDashboard`).
   - **Use Case**: Real-time status tracking for staff.

3. **[Saga Pattern for Payments]**
   - Manage **distributed transactions** across payment processors (e.g., Stripe, PayPal) and reservation systems.
   - **Example**:
     1. `ReservationCreated` → `PaymentInitiated`.
     2. If `PaymentFailed`, roll back with `ReservationCancelled`.

4. **[Dynamic Pricing with Reinforcement Learning]**
   - Use ML models (e.g., **TensorFlow**) to adjust rates based on demand forecasts.
   - **Integration**: Fetch historical data from `GuestHistory` and `Promotions`.

5. **[PMS-CRS Bridge Pattern]**
   - Sync data between **Property Management Systems** (e.g., Cloudbeds) and **Central Reservation Systems** (e.g., Amdocs).
   - **Tools**: Apache Kafka, SQL Server CDC.

6. **[Guest Self-Service API]**
   - Expose a **graphQL API** for guests to manage bookings, check-in remotely, or view loyalty points.
   - **Example Query**:
     ```graphql
     query {
       guest(guestId: "abc123") {
         reservations {
           checkInDate
           room {
             roomType { name }
           }
         }
         loyaltyPoints
       }
     }
     ```

---

## **Further Reading**
- **Standards**:
  - [IATA Travel Technology Guideline (ITTG)](https://www.iata.org)
  - [Open Travel Alliance (OTA) XML Schema](https://www.opentravel.org)
- **Frameworks**:
  - [DDD in Practice (Vaughn Vernon)](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215)
  - [Event-Driven Microservices (Chris Richardson)](https://www.infoq.com/articles/microservices-event-driven-architecture/)
- **Tools**:
  - **Database**: PostgreSQL (for ACID compliance), MongoDB (for flexibility).
  - **Caching**: Redis, Memcached.
  - **Messaging**: Apache Kafka, RabbitMQ.
  - **API Gateways**: Kong, AWS API Gateway.

---
## **Contributors**
- **Domain Experts**: Hospitality industry consultants (e.g., **Hilton, Marriott**).
- **Tech Leads**: Software architects from **PMS vendors** (e.g., **Mews, Cloudbeds**).

---
**Last Updated**: 2024-05-15
**Version**: 1.2

---
*This document is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*