# Phase 5: Java Backend

## Objective

Build Java-based backends using FraiseQL's Java generator, creating Spring Boot and Quarkus implementations with equivalent functionality to other language backends.

## Success Criteria

- [ ] Spring Boot + FraiseQL backend functional
- [ ] Quarkus + FraiseQL backend functional
- [ ] Micronaut + FraiseQL backend functional
- [ ] All share identical schema from Phase 1
- [ ] Common test suite passes
- [ ] Zero warnings with strict compilation
- [ ] JVM performance benchmarks established
- [ ] All types generated from FraiseQL schema

## TDD Cycles

### Cycle 1: Java Schema Generation

**RED**: Test Java schema generator produces valid types
```java
// tests/SchemaGenerationTest.java
import com.fraiseql.schema.FraiseQLSchema;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class SchemaGenerationTest {
    @Test
    public void testSchemaLoads() {
        FraiseQLSchema schema = FraiseQLSchema.load();
        assertNotNull(schema);
        assertNotNull(schema.getTypes());
        assertTrue(schema.getTypes().containsKey("User"));
    }

    @Test
    public void testSchemaExportsJSON() throws IOException {
        FraiseQLSchema.export("schema.json");
        assertTrue(Files.exists(Paths.get("schema.json")));
    }
}
```

**GREEN**: Minimal Java schema definitions
```java
// fraiseql-schema/schema/FraiseQLSchema.java
package com.fraiseql.schema;

import com.fraiseql.annotations.*;
import java.time.LocalDateTime;
import java.util.List;

@FraiseQLType
public class User {
    @Field
    private int id;

    @Field
    private String name;

    @Field(nullable = true)
    private String email;

    @Field
    private LocalDateTime createdAt;

    @Field
    private boolean isActive;

    // Getters
}

@FraiseQLType
public class Post {
    @Field
    private int id;

    @Field
    private String title;

    @Field
    private String content;

    @Field
    private int authorId;

    @Field
    private boolean published;

    @Field
    private User author;

    @Field
    private List<Comment> comments;
}

public class Schema {
    @Query(sqlSource = "v_users")
    public List<User> users(int limit) { return null; }

    @Mutation(sqlSource = "fn_create_user")
    public User createUser(String name, String email) { return null; }
}
```

**REFACTOR**: Add proper annotations, metadata

**CLEANUP**: Verify schema generates correctly

---

### Cycle 2: Spring Boot + FraiseQL Integration

**RED**: Test Spring Boot GraphQL endpoint uses FraiseQL
```java
// tests/SpringBootGraphQLTest.java
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.hamcrest.Matchers.containsString;

@SpringBootTest
@AutoConfigureMockMvc
public class SpringBootGraphQLTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    public void testGraphQLQuery() throws Exception {
        mockMvc.perform(post("/graphql")
            .contentType("application/json")
            .content("{\"query\":\"{ users { id name } }\"}"))
            .andExpect(status().isOk())
            .andExpect(content().string(containsString("users")));
    }
}
```

**GREEN**: Spring Boot + FraiseQL GraphQL endpoint
```java
// frameworks/fraiseql-java/spring-boot/src/main/java/com/fraiseql/GraphQLController.java
package com.fraiseql;

import com.fraiseql.runtime.FraiseQLRuntime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/graphql")
public class GraphQLController {
    @Autowired
    private FraiseQLRuntime runtime;

    @PostMapping
    public Map<String, Object> executeQuery(@RequestBody GraphQLRequest request) {
        try {
            Object result = runtime.execute(request.getQuery(), request.getVariables());
            return Map.of("data", result);
        } catch (Exception e) {
            return Map.of("errors", List.of(Map.of("message", e.getMessage())));
        }
    }
}

class GraphQLRequest {
    private String query;
    private Map<String, Object> variables;
    // Getters/setters
}
```

**REFACTOR**: Add Spring Boot GraphQL support, validation

**CLEANUP**: Ensure proper Spring conventions

---

### Cycle 3: Quarkus + FraiseQL Integration

**RED**: Test Quarkus GraphQL endpoint
```java
// tests/QuarkusGraphQLTest.java
@QuarkusTest
public class QuarkusGraphQLTest {
    @Test
    public void testGraphQLQuery() {
        given()
            .contentType("application/json")
            .body("{\"query\":\"{ users { id } }\"}")
            .when()
            .post("/graphql")
            .then()
            .statusCode(200)
            .body("data.users", notNullValue());
    }
}
```

**GREEN**: Quarkus + FraiseQL endpoint
```java
// frameworks/fraiseql-java/quarkus/src/main/java/com/fraiseql/GraphQLResource.java
package com.fraiseql;

import com.fraiseql.runtime.FraiseQLRuntime;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import java.util.*;

@Path("/graphql")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class GraphQLResource {
    @Inject
    FraiseQLRuntime runtime;

    @POST
    public Map<String, Object> execute(GraphQLRequest request) {
        try {
            Object result = runtime.execute(request.query, request.variables);
            return Map.of("data", result);
        } catch (Exception e) {
            return Map.of("errors", List.of(
                Map.of("message", e.getMessage())
            ));
        }
    }

    public static class GraphQLRequest {
        public String query;
        public Map<String, Object> variables;
    }
}
```

**REFACTOR**: Add Quarkus-specific optimizations

**CLEANUP**: Follow Quarkus patterns

---

### Cycle 4: Micronaut + FraiseQL Integration

**RED**: Test Micronaut GraphQL endpoint
```java
@MicronautTest
public class MicronautGraphQLTest {
    @Inject
    EmbeddedServer server;

    @Inject
    RxHttpClient client;

    @Test
    public void testGraphQLQuery() {
        String response = client.retrieve(
            HttpRequest.POST("/graphql", "{\"query\":\"{ users { id } }\"}")
                .contentType("application/json"),
            String.class
        ).blockingFirst();

        assertContains(response, "data");
    }
}
```

**GREEN**: Micronaut + FraiseQL endpoint
```java
// frameworks/fraiseql-java/micronaut/src/main/java/com/fraiseql/GraphQLController.java
package com.fraiseql;

import com.fraiseql.runtime.FraiseQLRuntime;
import io.micronaut.http.annotation.*;
import jakarta.inject.Inject;
import java.util.*;

@Controller("/graphql")
public class GraphQLController {
    @Inject
    private FraiseQLRuntime runtime;

    @Post(consumes = "application/json", produces = "application/json")
    public Map<String, Object> execute(@Body GraphQLRequest request) {
        try {
            Object result = runtime.execute(request.query, request.variables);
            return Map.of("data", result);
        } catch (Exception e) {
            return Map.of("errors", List.of(
                Map.of("message", e.getMessage())
            ));
        }
    }

    public static class GraphQLRequest {
        public String query;
        public Map<String, Object> variables;
    }
}
```

**REFACTOR**: Add Micronaut optimization

**CLEANUP**: Follow Micronaut conventions

---

### Cycle 5: Shared Test Suite for Java

**RED**: All common tests pass against Java backends
```java
// tests/common/JavaParityTest.java
@ParameterizedTest
@ValueSource(strings = {"spring-boot", "quarkus", "micronaut"})
public void testUserQuery(String framework) throws Exception {
    GraphQLClient client = getClient(framework);
    QueryResult result = client.query("{ users { id name } }");

    assertNotNull(result.data);
    assertNotNull(result.data.users);
    assertTrue(result.data.users.size() > 0);
}

@ParameterizedTest
@ValueSource(strings = {"spring-boot", "quarkus", "micronaut"})
public void testMutations(String framework) throws Exception {
    GraphQLClient client = getClient(framework);
    MutationResult result = client.mutate(
        "mutation { createUser(name: \"Test\", email: \"test@example.com\") { id } }"
    );

    assertNotNull(result.data.createUser.id);
}
```

**GREEN**: Create test client factory
```java
// tests/common/GraphQLClient.java
public class GraphQLClient {
    private String baseUrl;

    public QueryResult query(String query) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        String body = "{\"query\":\"" + query.replace("\"", "\\\"") + "\"}";

        HttpRequest request = HttpRequest.newBuilder()
            .uri(new URI(baseUrl + "/graphql"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body))
            .build();

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        return parseResponse(response.body(), QueryResult.class);
    }
}
```

**REFACTOR**: Add mutation support, variable handling

**CLEANUP**: Ensure all tests pass

---

### Cycle 6: Java Compilation & Performance

**RED**: All tests pass with strict compilation
```java
public class CompilationTest {
    @Test
    public void testCompilationWarnings() throws Exception {
        // mvn clean compile -Werror
        // Should produce zero warnings
    }

    @Benchmark
    public void benchmarkJavaFrameworks() {
        for (String framework : List.of("spring-boot", "quarkus", "micronaut")) {
            GraphQLClient client = getClient(framework);
            // Should match Python/TypeScript performance
        }
    }
}
```

**GREEN**: Build with strict compilation flags
```xml
<!-- pom.xml -->
<properties>
    <maven.compiler.source>21</maven.compiler.source>
    <maven.compiler.target>21</maven.compiler.target>
    <maven.compiler.parameters>true</maven.compiler.parameters>
</properties>

<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <configuration>
        <compilerArgs>
            <arg>-Xlint:all</arg>
            <arg>-Xlint:-processing</arg>
            <arg>-Werror</arg>
        </compilerArgs>
    </configuration>
</plugin>
```

**REFACTOR**: Fix any compilation warnings

**CLEANUP**: Verify clean builds

---

## Directory Structure (Java)

```
frameworks/
└── fraiseql-java/
    ├── shared/
    │   ├── src/main/java/com/fraiseql/
    │   │   ├── runtime/FraiseQLRuntime.java
    │   │   ├── client/GraphQLClient.java
    │   │   └── types/                    # Generated types
    │   └── pom.xml
    │
    ├── spring-boot/
    │   ├── src/main/java/com/fraiseql/
    │   │   ├── GraphQLController.java
    │   │   ├── config/GraphQLConfig.java
    │   │   └── Application.java
    │   ├── src/test/java/
    │   ├── pom.xml
    │   └── application.yml
    │
    ├── quarkus/
    │   ├── src/main/java/com/fraiseql/
    │   │   ├── GraphQLResource.java
    │   │   └── Application.java
    │   ├── pom.xml
    │   └── application.yml
    │
    └── micronaut/
        ├── src/main/java/com/fraiseql/
        │   ├── GraphQLController.java
        │   └── Application.java
        ├── pom.xml
        └── application.yml
```

## Build Strategy

```bash
# Build all Java frameworks
mvn clean install -DskipTests

# Run tests with coverage
mvn test -DforkCount=1

# Static analysis
mvn sonar:sonar

# Performance benchmarks
mvn jmh:benchmark
```

## Performance Goals

- **Spring Boot**: ≥5,000 req/s
- **Quarkus**: ≥8,000 req/s (native mode: ≥15,000 req/s)
- **Micronaut**: ≥6,000 req/s

## Dependencies

- Requires: Phase 1 (schema complete)
- Requires: FraiseQL Java generator v2.0.0-a1+
- Blocks: Phase 7 (cross-language testing)

## Java Version

- Minimum: Java 21
- Target: Latest LTS (21+)
- All projects use record types and sealed classes

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- All types generated from FraiseQL annotations
- No custom resolver logic
- Maven-based build system
- Spring Boot 3.x, Quarkus 3.x, Micronaut 4.x
- Common test suite validates parity across JVM implementations
