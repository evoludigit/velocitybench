# Phase 6: PHP Backend

## Objective

Build PHP-based backends using FraiseQL's PHP generator, creating Laravel, Symfony, and Slim implementations with equivalent functionality to other language backends.

## Success Criteria

- [ ] Laravel + FraiseQL backend functional
- [ ] Symfony + FraiseQL backend functional
- [ ] Slim + FraiseQL backend functional
- [ ] All share identical schema from Phase 1
- [ ] Common test suite passes
- [ ] PHP 8.3+ strict types enforced
- [ ] Zero warnings with phpstan level 9
- [ ] All types generated from FraiseQL schema

## TDD Cycles

### Cycle 1: PHP Schema Generation

**RED**: Test PHP schema generator produces valid types
```php
// tests/SchemaGenerationTest.php
namespace Tests;

use PHPUnit\Framework\TestCase;
use FraiseQL\Schema\FraiseQLSchema;

class SchemaGenerationTest extends TestCase {
    public function testSchemaLoads(): void {
        $schema = FraiseQLSchema::load();
        $this->assertNotNull($schema);
        $this->assertNotNull($schema->types);
        $this->assertArrayHasKey('User', $schema->types);
    }

    public function testSchemaExportsJSON(): void {
        FraiseQLSchema::export('schema.json');
        $this->assertFileExists('schema.json');
    }
}
```

**GREEN**: Minimal PHP schema definitions
```php
// fraiseql-schema/schema.fraiseql.php
<?php

declare(strict_types=1);

namespace FraiseQL\Schema;

use FraiseQL\Attributes\Type;
use FraiseQL\Attributes\Field;
use FraiseQL\Attributes\Query;
use FraiseQL\Attributes\Mutation;

#[Type]
class User {
    #[Field]
    public int $id;

    #[Field]
    public string $name;

    #[Field(nullable: true)]
    public ?string $email;

    #[Field]
    public string $createdAt;

    #[Field]
    public bool $isActive;
}

#[Type]
class Post {
    #[Field]
    public int $id;

    #[Field]
    public string $title;

    #[Field]
    public string $content;

    #[Field]
    public int $authorId;

    #[Field]
    public bool $published;

    #[Field]
    public User $author;
}

class Schema {
    #[Query(sqlSource: 'v_users')]
    public function users(int $limit = 10): array {
        return [];
    }

    #[Mutation(sqlSource: 'fn_create_user')]
    public function createUser(string $name, string $email): User {
        return new User();
    }
}
```

**REFACTOR**: Add proper attribute implementations, metadata

**CLEANUP**: Verify schema generates correctly

---

### Cycle 2: Laravel + FraiseQL Integration

**RED**: Test Laravel GraphQL endpoint uses FraiseQL
```php
// tests/Feature/GraphQLEndpointTest.php
namespace Tests\Feature;

use Tests\TestCase;

class GraphQLEndpointTest extends TestCase {
    public function test_graphql_query(): void {
        $response = $this->postJson('/graphql', [
            'query' => '{ users { id name } }'
        ]);

        $response->assertStatus(200)
            ->assertJsonStructure(['data' => ['users']])
            ->assertJsonCount(1, 'data.users.0');
    }

    public function test_graphql_mutation(): void {
        $response = $this->postJson('/graphql', [
            'query' => 'mutation { createUser(name: "Test", email: "test@example.com") { id } }'
        ]);

        $response->assertStatus(200)
            ->assertJsonPath('data.createUser.id', fn($id) => is_int($id));
    }
}
```

**GREEN**: Laravel + FraiseQL endpoint
```php
// app/Http/Controllers/GraphQLController.php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use FraiseQL\Runtime\FraiseQLRuntime;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class GraphQLController extends Controller {
    public function __construct(
        private FraiseQLRuntime $runtime
    ) {}

    public function execute(Request $request): JsonResponse {
        try {
            $query = $request->input('query');
            $variables = $request->input('variables', []);

            $result = $this->runtime->execute($query, $variables);

            return response()->json(['data' => $result]);
        } catch (\Exception $e) {
            return response()->json(
                ['errors' => [['message' => $e->getMessage()]]],
                400
            );
        }
    }
}
```

**REFACTOR**: Add middleware, validation, error handling

**CLEANUP**: Follow Laravel conventions

---

### Cycle 3: Symfony + FraiseQL Integration

**RED**: Test Symfony GraphQL endpoint
```php
// tests/Controller/GraphQLControllerTest.php
namespace App\Tests\Controller;

use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;

class GraphQLControllerTest extends WebTestCase {
    public function testGraphQLQuery(): void {
        $client = static::createClient();
        $client->request('POST', '/graphql', [], [], [
            'CONTENT_TYPE' => 'application/json',
        ], json_encode(['query' => '{ users { id } }']));

        $this->assertResponseStatusCodeSame(200);
    }
}
```

**GREEN**: Symfony + FraiseQL endpoint
```php
// src/Controller/GraphQLController.php
<?php

declare(strict_types=1);

namespace App\Controller;

use FraiseQL\Runtime\FraiseQLRuntime;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/graphql', methods: ['POST'])]
class GraphQLController extends AbstractController {
    public function __construct(
        private FraiseQLRuntime $runtime
    ) {}

    public function execute(Request $request): JsonResponse {
        try {
            $data = json_decode($request->getContent(), true);
            $result = $this->runtime->execute(
                $data['query'],
                $data['variables'] ?? []
            );

            return new JsonResponse(['data' => $result]);
        } catch (\Exception $e) {
            return new JsonResponse(
                ['errors' => [['message' => $e->getMessage()]]],
                JsonResponse::HTTP_BAD_REQUEST
            );
        }
    }
}
```

**REFACTOR**: Add Symfony validation, events

**CLEANUP**: Follow Symfony patterns

---

### Cycle 4: Slim + FraiseQL Integration

**RED**: Test Slim GraphQL endpoint
```php
// tests/GraphQLTest.php
namespace Tests;

use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ServerRequestInterface as Request;

class GraphQLTest extends TestCase {
    private \Slim\App $app;

    protected function setUp(): void {
        $this->app = require __DIR__ . '/../src/app.php';
    }

    public function testGraphQLQuery(): void {
        $request = $this->createRequest('POST', '/graphql', [
            'query' => '{ users { id } }'
        ]);

        $response = $this->app->handle($request);
        $this->assertSame(200, $response->getStatusCode());
    }

    private function createRequest(string $method, string $path, array $data): Request {
        // Create PSR-7 request
    }
}
```

**GREEN**: Slim + FraiseQL endpoint
```php
// src/app.php
<?php

declare(strict_types=1);

use FraiseQL\Runtime\FraiseQLRuntime;
use Slim\Factory\AppFactory;

$app = AppFactory::create();
$runtime = new FraiseQLRuntime('schema.compiled.json');

$app->post('/graphql', function ($request, $response) use ($runtime) {
    try {
        $data = json_decode($request->getBody(), true);
        $result = $runtime->execute(
            $data['query'] ?? '',
            $data['variables'] ?? []
        );

        $response->getBody()->write(json_encode(['data' => $result]));
        return $response->withHeader('Content-Type', 'application/json');
    } catch (\Exception $e) {
        $response->getBody()->write(json_encode([
            'errors' => [['message' => $e->getMessage()]]
        ]));
        return $response
            ->withStatus(400)
            ->withHeader('Content-Type', 'application/json');
    }
});

return $app;
```

**REFACTOR**: Add middleware, better error handling

**CLEANUP**: Follow Slim conventions

---

### Cycle 5: Shared Test Suite for PHP

**RED**: All common tests pass against PHP backends
```php
// tests/Feature/ParityTest.php
namespace Tests\Feature;

use PHPUnit\Framework\TestCase;

/**
 * @dataProvider frameworkProvider
 */
public function testUserQuery(string $framework): void {
    $client = $this->getClient($framework);
    $response = $client->query('{ users { id name } }');

    $this->assertIsArray($response['data']);
    $this->assertIsArray($response['data']['users']);
    $this->assertCount(1, $response['data']['users']);
}

public static function frameworkProvider(): array {
    return [
        ['laravel'],
        ['symfony'],
        ['slim'],
    ];
}
```

**GREEN**: Create test client factory
```php
// tests/GraphQLClient.php
<?php

declare(strict_types=1);

namespace Tests;

class GraphQLClient {
    public function __construct(
        private string $baseUrl
    ) {}

    public function query(string $query): array {
        $response = $this->post('/graphql', ['query' => $query]);
        return json_decode($response, true);
    }

    private function post(string $endpoint, array $payload): string {
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => json_encode($payload),
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_RETURNTRANSFER => true,
        ]);

        return curl_exec($ch);
    }
}
```

**REFACTOR**: Add mutation support, variable handling

**CLEANUP**: Ensure all tests pass

---

### Cycle 6: PHP Static Analysis & Performance

**RED**: All tests pass with strict PHPStan analysis
```php
public function testPHPStanLevel9(): void {
    // phpstan analyse --level=9 src/
    // Should produce zero errors
}

public function benchmarkFrameworks(): void {
    $frameworks = ['laravel', 'symfony', 'slim'];
    foreach ($frameworks as $framework) {
        $client = $this->getClient($framework);
        // Should match other languages
    }
}
```

**GREEN**: Enable strict type checking
```php
<?php
// phpstan.neon
parameters:
    level: 9
    paths:
        - src
        - tests
    treatPhpDocTypesAsCertainTypes: true
    checkImplicitMixed: true
```

**REFACTOR**: Fix any type issues

**CLEANUP**: Verify all analysis passes

---

## Directory Structure (PHP)

```
frameworks/
└── fraiseql-php/
    ├── shared/
    │   ├── src/
    │   │   └── FraiseQL/
    │   │       ├── Runtime/
    │   │       ├── Client/
    │   │       └── Types/              # Generated types
    │   ├── composer.json
    │   └── phpstan.neon
    │
    ├── laravel/
    │   ├── app/
    │   │   ├── Http/Controllers/GraphQLController.php
    │   │   └── Providers/
    │   ├── routes/api.php
    │   ├── tests/Feature/
    │   ├── composer.json
    │   └── phpstan.neon
    │
    ├── symfony/
    │   ├── src/
    │   │   └── Controller/GraphQLController.php
    │   ├── config/routes.yaml
    │   ├── tests/
    │   ├── composer.json
    │   └── phpstan.neon
    │
    └── slim/
        ├── src/
        │   └── app.php
        ├── tests/
        ├── composer.json
        └── phpstan.neon
```

## Build Strategy

```bash
# Install dependencies
composer install

# Run tests
composer test

# Static analysis
composer analyse

# Code formatting
composer format

# Performance profiling
composer profile
```

## PHP Version

- Minimum: PHP 8.3
- Target: Latest stable (8.4+)
- Strict types: `declare(strict_types=1);` on all files

## Dependencies

- Requires: Phase 1 (schema complete)
- Requires: FraiseQL PHP generator v2.0.0-a1+
- Blocks: Phase 7 (cross-language testing)

## Performance Goals

- **Laravel**: ≥3,000 req/s
- **Symfony**: ≥2,500 req/s
- **Slim**: ≥4,000 req/s

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- All types generated from FraiseQL attributes
- PHP 8.3+ attributes for type definitions
- Strict type checking enforced
- PHPStan level 9 required
- Common test suite validates parity across frameworks
- Laravel, Symfony, and Slim maintain framework idioms
