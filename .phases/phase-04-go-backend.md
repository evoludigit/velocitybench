# Phase 4: Go Backend

## Objective

Build Go-based backends using FraiseQL's Go generator, creating Gin, Echo, and Fiber implementations with equivalent functionality to Python and TypeScript backends.

## Success Criteria

- [ ] Gin + FraiseQL backend functional
- [ ] Echo + FraiseQL backend functional
- [ ] Fiber + FraiseQL backend functional
- [ ] All share identical schema from Phase 1
- [ ] Common test suite passes
- [ ] Performance meets or exceeds Python/TypeScript
- [ ] Zero compiler warnings with strict linting
- [ ] All types derived from FraiseQL schema

## TDD Cycles

### Cycle 1: Go Schema Generation

**RED**: Test Go schema generator produces correct types
```go
// tests/go_test.go
package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
    schema "github.com/fraiseql/go/schema"
)

func TestGoSchemaGeneration(t *testing.T) {
    s := schema.LoadSchema()
    assert.NotNil(t, s)

    user := s.Types["User"]
    assert.NotNil(t, user)
    assert.Equal(t, "int", user.Fields["id"].Type)
}

func TestSchemaExportsJSON(t *testing.T) {
    err := schema.ExportSchema("schema.json")
    assert.NoError(t, err)
}
```

**GREEN**: Minimal Go schema generation
```go
// fraiseql-schema/schema.fraiseql.go
package schema

import "github.com/fraiseql/go/fraiseql"

type User struct {
    ID        int     `fraiseql:"id"`
    Name      string  `fraiseql:"name"`
    Email     *string `fraiseql:"email"`
    CreatedAt string  `fraiseql:"createdAt"`
    IsActive  bool    `fraiseql:"isActive"`
}

type Post struct {
    ID        int    `fraiseql:"id"`
    Title     string `fraiseql:"title"`
    Content   string `fraiseql:"content"`
    AuthorID  int    `fraiseql:"authorId"`
    Published bool   `fraiseql:"published"`
    Author    User   `fraiseql:"author,relation"`
}

type Schema struct {
    Users fraiseql.Query[[]User] `fraiseql:"query,sql_source=v_users"`
    Posts fraiseql.Query[[]Post] `fraiseql:"query,sql_source=v_posts"`
}

func ExportSchema(path string) error {
    return fraiseql.Export(&Schema{}, path)
}
```

**REFACTOR**: Add proper struct tags, validation

**CLEANUP**: Verify schema generates correct JSON

---

### Cycle 2: Gin + FraiseQL Integration

**RED**: Test Gin serves FraiseQL GraphQL queries
```go
import (
    "testing"
    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
)

func TestGinGraphQLEndpoint(t *testing.T) {
    router := setupGinRouter()

    req, _ := http.NewRequest(
        "POST",
        "/graphql",
        strings.NewReader(`{"query":"{ users { id name } }"}`),
    )
    req.Header.Set("Content-Type", "application/json")

    w := httptest.NewRecorder()
    router.ServeHTTP(w, req)

    assert.Equal(t, 200, w.Code)
    assert.Contains(t, w.Body.String(), "data")
}
```

**GREEN**: Minimal Gin + FraiseQL server
```go
// frameworks/fraiseql-go/gin/main.go
package main

import (
    "github.com/gin-gonic/gin"
    "github.com/fraiseql/go/runtime"
)

func main() {
    router := gin.Default()
    rt := runtime.NewRuntime("schema.compiled.json")

    router.POST("/graphql", func(c *gin.Context) {
        var req struct {
            Query string                 `json:"query"`
            Variables map[string]interface{} `json:"variables"`
        }

        c.BindJSON(&req)
        result, err := rt.Execute(req.Query, req.Variables)

        if err != nil {
            c.JSON(400, gin.H{"errors": []string{err.Error()}})
            return
        }

        c.JSON(200, gin.H{"data": result})
    })

    router.Run(":8080")
}
```

**REFACTOR**: Add error handling, middleware, validation

**CLEANUP**: Ensure Gin conventions followed

---

### Cycle 3: Echo + FraiseQL Integration

**RED**: Test Echo serves FraiseQL queries
```go
func TestEchoGraphQL(t *testing.T) {
    e := setupEchoServer()

    req := httptest.NewRequest(
        echo.POST,
        "/graphql",
        strings.NewReader(`{"query":"{ users { id } }"}`),
    )
    req.Header.Set("Content-Type", "application/json")

    w := httptest.NewRecorder()
    e.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
}
```

**GREEN**: Minimal Echo + FraiseQL
```go
// frameworks/fraiseql-go/echo/main.go
package main

import (
    "github.com/labstack/echo/v4"
    "github.com/fraiseql/go/runtime"
)

func main() {
    e := echo.New()
    rt := runtime.NewRuntime("schema.compiled.json")

    e.POST("/graphql", func(c echo.Context) error {
        var req struct {
            Query     string                 `json:"query"`
            Variables map[string]interface{} `json:"variables"`
        }

        c.Bind(&req)
        result, err := rt.Execute(req.Query, req.Variables)

        if err != nil {
            return c.JSON(400, map[string]interface{}{
                "errors": []string{err.Error()},
            })
        }

        return c.JSON(200, map[string]interface{}{"data": result})
    })

    e.Logger.Fatal(e.Start(":8080"))
}
```

**REFACTOR**: Add proper error handling, middleware

**CLEANUP**: Follow Echo patterns

---

### Cycle 4: Fiber + FraiseQL Integration

**RED**: Test Fiber serves FraiseQL queries
```go
func TestFiberGraphQL(t *testing.T) {
    app := setupFiberApp()

    req := httptest.NewRequest(
        "POST",
        "/graphql",
        strings.NewReader(`{"query":"{ users { id } }"}`),
    )
    req.Header.Set("Content-Type", "application/json")

    resp, err := app.Test(req)
    assert.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode)
}
```

**GREEN**: Minimal Fiber + FraiseQL
```go
// frameworks/fraiseql-go/fiber/main.go
package main

import (
    "github.com/gofiber/fiber/v2"
    "github.com/fraiseql/go/runtime"
)

func main() {
    app := fiber.New()
    rt := runtime.NewRuntime("schema.compiled.json")

    app.Post("/graphql", func(c *fiber.Ctx) error {
        var req struct {
            Query     string                 `json:"query"`
            Variables map[string]interface{} `json:"variables"`
        }

        c.BodyParser(&req)
        result, err := rt.Execute(req.Query, req.Variables)

        if err != nil {
            return c.Status(400).JSON(fiber.Map{
                "errors": []string{err.Error()},
            })
        }

        return c.JSON(fiber.Map{"data": result})
    })

    app.Listen(":8080")
}
```

**REFACTOR**: Add middleware, error handling

**CLEANUP**: Follow Fiber conventions

---

### Cycle 5: Shared Test Suite for Go

**RED**: All common tests pass against Go backends
```go
// tests/common/parity_test.go
package common

import (
    "testing"
)

var frameworks = []struct {
    name   string
    setup  func() *http.Client
}{
    {"gin", setupGinClient},
    {"echo", setupEchoClient},
    {"fiber", setupFiberClient},
}

func TestUsersQuery(t *testing.T) {
    for _, framework := range frameworks {
        t.Run(framework.name, func(t *testing.T) {
            client := framework.setup()
            resp, err := client.Post(
                "http://localhost:8080/graphql",
                "application/json",
                strings.NewReader(`{"query":"{ users { id name } }"}`),
            )

            assert.NoError(t, err)
            assert.Equal(t, 200, resp.StatusCode)
        })
    }
}
```

**GREEN**: Create test utilities
```go
// tests/common/client.go
package common

type GraphQLClient struct {
    baseURL string
    client  *http.Client
}

func (c *GraphQLClient) Query(query string) (map[string]interface{}, error) {
    req, _ := http.NewRequest(
        "POST",
        c.baseURL + "/graphql",
        strings.NewReader(fmt.Sprintf(`{"query":"%s"}`, query)),
    )
    req.Header.Set("Content-Type", "application/json")

    resp, err := c.client.Do(req)
    if err != nil {
        return nil, err
    }

    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    return result, nil
}
```

**REFACTOR**: Add mutation support, variable handling

**CLEANUP**: Ensure all tests pass

---

### Cycle 6: Go Performance & Strict Linting

**RED**: All tests pass with strict Go linting
```go
func TestAllLintsPass(t *testing.T) {
    // Run: golangci-lint run ./...
    // Should produce zero warnings
}

func BenchmarkGoFrameworks(b *testing.B) {
    client := getGoClient()

    b.Run("gin", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            client.Query("{ users { id } }")
        }
    })

    // Should match or exceed Python/TypeScript performance
}
```

**GREEN**: Build all frameworks with strict linting
```bash
# golangci-lint configuration
linters:
  enable:
    - staticcheck
    - vet
    - goimports
    - ineffassign
    - unparam
    - deadcode
    - unused
```

**REFACTOR**: Fix any lint warnings

**CLEANUP**: Verify all lints pass

---

## Directory Structure (Go)

```
frameworks/
└── fraiseql-go/
    ├── shared/
    │   ├── runtime.go              # FraiseQL runtime
    │   ├── client.go               # HTTP client
    │   ├── middleware.go           # Auth, logging
    │   └── types.go                # Generated types
    │
    ├── gin/
    │   ├── main.go                 # Gin server
    │   ├── handlers.go             # HTTP handlers
    │   ├── go.mod
    │   ├── go.sum
    │   └── tests/
    │
    ├── echo/
    │   ├── main.go                 # Echo server
    │   ├── handlers.go
    │   ├── go.mod
    │   └── tests/
    │
    └── fiber/
        ├── main.go                 # Fiber server
        ├── handlers.go
        ├── go.mod
        └── tests/
```

## Build Strategy

```bash
# Build all Go frameworks
make build-go

# Run tests with coverage
go test -v -cover ./...

# Lint everything
golangci-lint run ./...

# Benchmark
go test -bench=. -benchmem ./...
```

## Dependencies

- Requires: Phase 1 (schema complete)
- Requires: FraiseQL Go generator v2.0.0-a1+
- Blocks: Phase 7 (cross-language testing)

## Performance Goals

- **Throughput**: ≥10,000 req/s per framework (bare metal)
- **Latency**: <10ms p99 for simple queries
- **Memory**: <50MB per instance

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- All types generated from FraiseQL schema
- No custom resolver logic in handlers
- Strict linting required - zero warnings
- Go idioms take priority over consistency with other languages
- Common test suite validates cross-language parity
