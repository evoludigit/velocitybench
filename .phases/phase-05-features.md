# Phase 5: Feature Enhancements & Best Practices

## Objective

Add advanced features to framework blueprints based on benchmark results, demonstrating production-ready patterns without significantly impacting performance baseline.

## Success Criteria

- [ ] Authentication pattern implemented in all 5 frameworks
- [ ] Caching layer added (optional, benchmarked separately)
- [ ] Error handling improvements
- [ ] Request validation enhancements
- [ ] Documentation updated with feature examples
- [ ] No feature regression in Phase 4 benchmarks

## Features to Add

### Core Features (All Frameworks)

**Authentication**
- API key validation
- JWT token support
- Role-based access control
- Request context propagation

**Improved Error Handling**
- Custom error types
- User-friendly error messages
- Error logging and tracking
- Error rate monitoring

**Request Validation**
- Schema validation
- Input sanitization
- Rate limiting support
- Query complexity analysis

**Observability**
- Structured logging
- Request tracing
- Performance monitoring
- Health checks

### Optional Performance Features

**Caching** (measured separately)
- Response caching
- Query result caching
- Cache invalidation

**Request Batching** (GraphQL batching)
- Multiple queries in single request
- Reduced network overhead

## Enhancement Areas (Per Language)

### Python FastAPI
```python
# Add authentication middleware
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    # Validate JWT or API key
    pass

@app.post("/graphql")
async def graphql(
    request: GraphQLRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    # Forward with auth context
    pass

# Add rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/graphql")
@limiter.limit("100/minute")
async def graphql(...):
    pass

# Add caching (optional)
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

@app.post("/graphql")
@cached(expire=300)
async def graphql(request: GraphQLRequest):
    pass
```

### TypeScript Express
```typescript
// Add authentication middleware
import jwt from 'jsonwebtoken';

app.use((req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) {
    return res.status(401).json({ errors: [{ message: 'Unauthorized' }] });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    res.status(401).json({ errors: [{ message: 'Invalid token' }] });
  }
});

// Add rate limiting
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100
});

app.post('/graphql', limiter, async (req, res) => {
  // ...
});

// Add caching (optional)
import redis from 'redis';

const cache = redis.createClient();
```

### Go Gin
```go
// Add authentication middleware
func AuthMiddleware() gin.HandlerFunc {
  return func(c *gin.Context) {
    token := c.GetHeader("Authorization")
    if token == "" {
      c.JSON(401, gin.H{"errors": []string{"Unauthorized"}})
      c.Abort()
      return
    }

    // Validate token
    claims, err := validateToken(token)
    if err != nil {
      c.JSON(401, gin.H{"errors": []string{"Invalid token"}})
      c.Abort()
      return
    }

    c.Set("user", claims)
    c.Next()
  }
}

router.POST("/graphql", AuthMiddleware(), handleGraphQL)

// Add rate limiting
import "github.com/ulule/limiter/v3"

limiter := limiter.New(limiter.RateLimit(100, time.Minute))
router.POST("/graphql", adapter.Gin(), handleGraphQL)
```

### Java Spring Boot
```java
// Add authentication
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests()
            .antMatchers("/graphql").authenticated()
            .and()
            .addFilter(new JwtAuthenticationFilter(authenticationManager()));
    }
}

// Add rate limiting
@RestController
public class GraphQLController {
    @RateLimiter(name = "graphql", fallbackMethod = "rateLimitFallback")
    @PostMapping("/graphql")
    public ResponseEntity<?> graphql(@RequestBody GraphQLRequest request) {
        // ...
    }
}

// Add caching (optional)
@Cacheable(value = "graphql", key = "#request.query")
public ResponseEntity<?> graphql(GraphQLRequest request) {
    // ...
}
```

### PHP Laravel
```php
// Add authentication middleware
Route::post('/graphql', [GraphQLController::class, 'execute'])
    ->middleware(['api', 'auth:api']);

// Add rate limiting
Route::post('/graphql', function (Request $request) {
    // Laravel includes built-in rate limiting
})->middleware('throttle:100,1');

// Add caching
Route::post('/graphql', function (Request $request) {
    $cacheKey = 'graphql:' . md5($request->query);
    if (Cache::has($cacheKey)) {
        return Cache::get($cacheKey);
    }

    $result = forwardToFraiseQL($request);
    Cache::put($cacheKey, $result, 300);
    return $result;
});
```

## Implementation Plan

### Phase 5a: Core Features (All Languages)
1. **Authentication**: Implement JWT validation
2. **Error Handling**: Consistent error responses
3. **Logging**: Structured logging setup
4. **Validation**: Request validation schema

### Phase 5b: Performance Features (Optional)
1. **Caching**: Add and benchmark separately
2. **Batching**: Support GraphQL batching
3. **Query Limits**: Complexity analysis

### Phase 5c: Documentation
1. Feature guides for each language
2. Example implementations
3. Best practices documentation

## Testing Strategy

```python
# Each feature is tested independently
def test_authentication_required():
    response = client.post("/graphql", json={...})
    assert response.status_code == 401

def test_valid_token_accepted():
    token = create_valid_token()
    response = client.post(
        "/graphql",
        headers={"Authorization": f"Bearer {token}"},
        json={...}
    )
    assert response.status_code == 200

def test_rate_limiting():
    for i in range(101):
        response = client.post("/graphql", json={...})
        if i < 100:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Too Many Requests

def test_caching_transparent(benchmark):
    """Caching adds minimal overhead."""
    # First request: no cache
    result1 = benchmark(lambda: client.post("/graphql", json={...}))

    # Second request: cached
    result2 = benchmark(lambda: client.post("/graphql", json={...}))

    # Cached response should be significantly faster
    assert result2["latency"] < result1["latency"] * 0.5
```

## Deliverables

```
frameworks/
├── fraiseql-python/fastapi/
│   ├── app.py                  # With auth, rate limiting
│   ├── auth.py                 # Authentication module
│   ├── cache.py                # Caching (optional)
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_rate_limiting.py
│   │   └── test_caching.py
│   └── docs/FEATURES.md        # Feature documentation
│
├── fraiseql-typescript/express/
│   ├── src/app.ts
│   ├── src/middleware/
│   │   ├── auth.ts
│   │   ├── rateLimit.ts
│   │   └── cache.ts (optional)
│   └── docs/FEATURES.md
│
└── [Go, Java, PHP - same pattern]
```

## Performance Baseline Validation

After adding features, re-run Phase 4 benchmarks:

```python
def test_feature_overhead_acceptable():
    """New features don't significantly impact performance."""
    baseline_latency = 23.1  # From Phase 4 (FastAPI)

    # With auth
    with_auth = benchmark_framework("FastAPI", auth=True)
    assert with_auth < baseline_latency * 1.1  # < 10% overhead

    # With logging
    with_logging = benchmark_framework("FastAPI", logging=True)
    assert with_logging < baseline_latency * 1.05  # < 5% overhead

    # Combined (auth + logging + validation)
    full_featured = benchmark_framework("FastAPI", full_features=True)
    assert full_featured < baseline_latency * 1.2  # < 20% overhead
```

## Dependencies

- Requires: Phase 4 (benchmarks establish baseline)
- Blocks: Phase 6 (validation confirms feature quality)

## Parallel Execution

Phase 5 can be executed in parallel for all 5 languages, with each language team implementing features independently.

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- Features are additive; benchmarks capture cumulative overhead
- Caching is optional; measured separately to avoid confounding
- Authentication is core; every framework must support it
- Performance remains within acceptable bounds (< 20% overhead)
