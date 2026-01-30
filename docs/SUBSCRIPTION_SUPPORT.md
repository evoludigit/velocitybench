# GraphQL Subscription Support Assessment

## Executive Summary

**Current State**: VelocityBench does not currently implement GraphQL subscriptions across any frameworks.

**Rationale**: Subscriptions add significant complexity and are not the primary focus of benchmarking REST/GraphQL query performance. The project prioritizes fair, reproducible benchmarks of standard request/response patterns.

**Future Recommendation**: Implement subscriptions as a separate benchmark profile (Phase 2) after establishing baseline REST/query benchmarks.

## Why Subscriptions Are Not Currently Implemented

### 1. Complexity vs Benchmark Goals

Subscriptions require:
- **WebSocket/SSE infrastructure**: Long-lived connections
- **Connection pooling**: Managing thousands of concurrent connections
- **State management**: Tracking active subscriptions per client
- **Event dispatching**: Broadcasting updates to relevant subscribers
- **Connection lifecycle**: Handling connects, disconnects, reconnects

**Impact on benchmarking**:
- Significantly different performance characteristics than request/response
- Requires separate load testing methodology
- Connection overhead dominates measurement
- Difficult to create fair cross-framework comparisons

### 2. Benchmark Focus

VelocityBench prioritizes:
- ✅ **REST API performance**: Request/response latency, throughput
- ✅ **GraphQL query performance**: Query complexity, N+1 detection
- ✅ **Database optimization**: Query patterns, connection pooling
- ✅ **Fair comparisons**: Standardized workloads across frameworks

Subscriptions would require:
- ❌ **Different workload patterns**: Event streams vs request/response
- ❌ **Connection-based metrics**: Active connections, message throughput
- ❌ **Event source simulation**: Generating realistic event streams
- ❌ **Separate benchmark infrastructure**: WebSocket load testing tools

### 3. Rapid Setup Constraint

The Trinity Pattern enables:
- Quick database setup (<5 minutes)
- Reproducible seed data
- Standardized schema across frameworks

Subscriptions would require:
- Event source infrastructure (message broker, pub/sub)
- Real-time data generation
- Coordination between publishers and subscribers
- Additional operational complexity

### 4. Framework Variability

Not all frameworks have equal subscription support:
- Some frameworks lack native subscription support
- Implementation patterns vary widely (WebSocket vs SSE vs long-polling)
- Subscription resolver patterns differ significantly
- Some require external message brokers (Redis, RabbitMQ)

This makes fair comparisons difficult.

## Framework Subscription Capability Matrix

| Framework | Native Support | Transport | Complexity | Notes |
|-----------|----------------|-----------|------------|-------|
| **Python** | | | | |
| Strawberry GraphQL | ✅ Yes | WebSocket | Medium | Built-in WebSocket support |
| Graphene | ⚠️ Limited | WebSocket | High | Requires graphene-django channels |
| FraiseQL | ✅ Yes | WebSocket | Medium | Custom subscription implementation |
| ASGI-GraphQL | ✅ Yes | WebSocket | Medium | ASGI-native subscriptions |
| **TypeScript** | | | | |
| Apollo Server | ✅ Yes | WebSocket | Low | Excellent built-in support |
| GraphQL Yoga | ✅ Yes | WebSocket/SSE | Low | Multiple transport options |
| Mercurius | ✅ Yes | WebSocket | Low | Fastify WebSocket integration |
| Express GraphQL | ⚠️ Limited | WebSocket | High | Requires graphql-ws middleware |
| **Go** | | | | |
| gqlgen | ✅ Yes | WebSocket | Medium | Go WebSocket support |
| graphql-go | ❌ No | N/A | N/A | No subscription support |
| **Rust** | | | | |
| async-graphql | ✅ Yes | WebSocket | Medium | Async streams |
| **Java** | | | | |
| Spring GraphQL | ✅ Yes | WebSocket | Medium | Spring WebSocket |
| **C#** | | | | |
| HotChocolate | ✅ Yes | WebSocket | Low | Excellent support |

**Summary**:
- ✅ Full support: 10 frameworks (26%)
- ⚠️ Limited support: 3 frameworks (8%)
- ❌ No support: 26 frameworks (66%)

## Subscription Transport Protocols

### WebSocket

**Pros**:
- Full-duplex communication
- Low latency
- Efficient binary protocol
- Wide framework support

**Cons**:
- Connection overhead
- Load balancer complexity
- Stateful (harder to scale horizontally)
- Requires connection pooling

**Best for**:
- Real-time chat applications
- Live data feeds
- Collaborative editing
- Gaming

### Server-Sent Events (SSE)

**Pros**:
- Simpler than WebSocket (HTTP)
- Automatic reconnection
- Browser EventSource API
- Works with standard HTTP infrastructure

**Cons**:
- Unidirectional (server → client only)
- Limited browser support for custom headers
- Text-based (less efficient than WebSocket)

**Best for**:
- Notifications
- Live scores/updates
- Progress indicators
- News feeds

### Long Polling

**Pros**:
- Works everywhere (standard HTTP)
- No special server support needed
- Firewall-friendly

**Cons**:
- Inefficient (constant reconnections)
- High latency
- Resource-intensive
- Not a true real-time solution

**Best for**:
- Legacy browser support
- Simple notification systems
- Infrequent updates

## Implementation Recommendations

### Phase 1: Current State (Established)
✅ Focus on REST/GraphQL query benchmarks
✅ Optimize request/response patterns
✅ Establish baseline performance metrics

### Phase 2: Subscription Benchmarking (Future)

If subscriptions are added, implement as a **separate benchmark profile**:

#### Architecture
```
benchmarks/
├── standard/          # Current REST/query benchmarks
│   ├── read-heavy
│   ├── write-heavy
│   └── mixed
└── subscriptions/     # New subscription benchmarks
    ├── chat-room      # Many-to-many messaging
    ├── live-feed      # One-to-many broadcasting
    └── notifications  # Targeted updates
```

#### Infrastructure Requirements

1. **Message Broker** (Redis Pub/Sub or similar):
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

2. **Event Generator**:
```python
# Generate realistic event streams
async def event_generator():
    while True:
        event = generate_event()
        await redis.publish("events", event)
        await asyncio.sleep(0.1)  # 10 events/sec
```

3. **Subscription Load Tester**:
- Use tools like `websocket-bench` or custom scripts
- Measure: connections, messages/sec, latency distribution
- Monitor: memory per connection, CPU usage

#### Benchmark Scenarios

**Scenario 1: Chat Room** (Many-to-many)
```graphql
subscription OnNewMessage($roomId: ID!) {
  messageAdded(roomId: $roomId) {
    id
    content
    user {
      id
      username
    }
    timestamp
  }
}
```

**Metrics**:
- Concurrent connections: 100, 1000, 10000
- Message broadcast latency (p50, p95, p99)
- Memory per connection
- CPU utilization

**Scenario 2: Live Feed** (One-to-many)
```graphql
subscription OnPostCreated {
  postCreated {
    id
    title
    author {
      username
    }
  }
}
```

**Metrics**:
- Fan-out performance (1 event → N subscribers)
- Broadcast latency
- Connection overhead

**Scenario 3: Targeted Notifications** (One-to-one)
```graphql
subscription OnUserNotification($userId: ID!) {
  userNotification(userId: $userId) {
    id
    type
    message
    timestamp
  }
}
```

**Metrics**:
- Targeted delivery latency
- Subscription filtering efficiency
- Scalability with many unique subscriptions

#### Implementation Example (Strawberry + Redis)

```python
# frameworks/strawberry/subscriptions.py
import asyncio
import strawberry
from typing import AsyncGenerator
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost")

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def message_added(
        self, room_id: str
    ) -> AsyncGenerator[Message, None]:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"room:{room_id}")

        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                yield Message(**data)
```

#### Subscription-Specific Metrics

| Metric | Description | Good | Warning | Critical |
|--------|-------------|------|---------|----------|
| **Connection Time** | Time to establish WebSocket | <100ms | <500ms | >1s |
| **Message Latency** | Event → delivery time | <50ms | <200ms | >500ms |
| **Fan-out Time** | 1 event → N subscribers | <100ms | <500ms | >1s |
| **Memory/Connection** | Memory per active connection | <1MB | <5MB | >10MB |
| **Max Connections** | Concurrent connections supported | >10k | >5k | <1k |
| **Reconnection Time** | Time to reconnect after disconnect | <1s | <5s | >10s |

## Benchmarking Challenges

### 1. State Management
- WebSocket connections are stateful
- Load balancers need sticky sessions or connection tracking
- Horizontal scaling is more complex than stateless REST

### 2. Connection Overhead
- Initial WebSocket handshake adds latency
- Connection pool exhaustion
- File descriptor limits (ulimit)

### 3. Event Source Simulation
- Generating realistic event patterns
- Coordinating publishers and subscribers
- Avoiding artificial bottlenecks

### 4. Framework-Specific Implementations
- Apollo: `graphql-ws` protocol
- Relay: Custom subscription protocol
- Some frameworks use custom transports

**Solution**: Standardize on `graphql-ws` protocol where possible

### 5. Testing Infrastructure
- JMeter doesn't natively support WebSocket subscriptions well
- Need specialized tools:
  - `websocket-bench`
  - `Artillery` (with WebSocket plugin)
  - Custom Python/Go load generator

## Alternative: Mock Subscription Endpoint

For basic subscription testing without full infrastructure:

```python
@app.get("/subscribe/posts")
async def subscribe_posts():
    """Mock subscription via SSE"""
    async def event_generator():
        for i in range(10):
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'id': i, 'title': f'Post {i}'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

**Pros**:
- Simple to implement
- No external dependencies
- Easy to benchmark

**Cons**:
- Not real GraphQL subscriptions
- Limited to SSE semantics
- Doesn't test actual subscription resolvers

## Decision Matrix: When to Add Subscriptions

| Factor | Add Subscriptions? | Rationale |
|--------|-------------------|-----------|
| Primary focus is REST benchmarks | ❌ No | Subscriptions add unrelated complexity |
| Want to benchmark real-time features | ✅ Yes | Subscriptions are essential for real-time |
| Limited infrastructure budget | ❌ No | Requires message broker, complex setup |
| Comparing frameworks with native sub support | ✅ Yes | Fair comparison possible |
| Mixed framework support levels | ❌ No | Unfair comparisons |
| Want production-ready observability | ⚠️ Maybe | Health checks more important initially |

## Current Recommendation

**Do NOT implement subscriptions** for VelocityBench v1.0:

1. **Out of scope**: Primary goal is REST/query benchmarking
2. **Complexity**: Subscriptions require significant infrastructure
3. **Unfair comparisons**: Not all frameworks have equal support
4. **Tooling**: Current benchmark tools (JMeter) not subscription-optimized

**Future consideration**: If community requests subscription benchmarks:
- Create separate benchmark profile
- Establish infrastructure (Redis, WebSocket load tester)
- Implement in frameworks with native support first
- Document limitations and caveats

## Related Work

- [Apollo Federation Subscriptions](https://www.apollographql.com/docs/federation/subscriptions/)
- [graphql-ws Protocol](https://github.com/enisdenjo/graphql-ws)
- [WebSocket Benchmarking Tools](https://github.com/observing/websocket-bench)
- [GraphQL Subscriptions Best Practices](https://www.howtographql.com/graphql-js/7-subscriptions/)

## See Also

- [ADR-007: Framework Selection Criteria](adr/007-framework-selection-criteria.md)
- [ADR-010: Benchmarking Methodology](adr/010-benchmarking-methodology.md)
- [HEALTH_CHECKS.md](HEALTH_CHECKS.md) - Production observability implementation
