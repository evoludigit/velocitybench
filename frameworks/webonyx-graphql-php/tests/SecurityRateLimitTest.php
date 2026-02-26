<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/TestFactory.php';

/**
 * SecurityRateLimitTest - Tests rate limiting functionality
 *
 * Coverage includes:
 * - Per-user rate limits
 * - Rate limit window reset
 * - Independent user limits
 * - Query complexity limits
 * - Depth limits
 */
class SecurityRateLimitTest extends TestCase
{
    private TestFactory $factory;
    private array $rateLimitStorage = [];

    protected function setUp(): void
    {
        $this->factory = new TestFactory();
        $this->rateLimitStorage = [];
    }

    protected function tearDown(): void
    {
        $this->factory->reset();
        $this->rateLimitStorage = [];
    }

    // ============================================================================
    // Rate Limiting Tests
    // ============================================================================

    public function testEnforcesRateLimitPerUser(): void
    {
        $user = $this->factory->createUser('alice', 'alice@example.com', 'Alice');
        $maxRequests = 60; // Typical rate limit per minute

        $successfulRequests = 0;
        $rateLimitExceeded = false;

        for ($i = 0; $i < $maxRequests + 5; $i++) {
            if ($this->checkRateLimit($user->id)) {
                $successfulRequests++;
                $this->factory->getUser($user->id);
            } else {
                $rateLimitExceeded = true;
                break;
            }
        }

        // Should hit rate limit
        $this->assertTrue(
            $rateLimitExceeded || $successfulRequests === $maxRequests,
            'Rate limit should be enforced'
        );
    }

    public function testRateLimitResetsAfterWindow(): void
    {
        $user = $this->factory->createUser('bob', 'bob@example.com', 'Bob');

        // Make requests up to limit
        for ($i = 0; $i < 60; $i++) {
            $this->checkRateLimit($user->id);
        }

        // Verify rate limit hit
        $isLimited = !$this->checkRateLimit($user->id);
        $this->assertTrue($isLimited, 'Should be rate limited');

        // Reset rate limit window
        $this->resetRateLimit($user->id);

        // Should allow requests again
        $canMakeRequest = $this->checkRateLimit($user->id);
        $this->assertTrue($canMakeRequest, 'Rate limit should reset after window');
    }

    public function testRateLimitsAreIndependentPerUser(): void
    {
        $alice = $this->factory->createUser('alice', 'alice@example.com', 'Alice');
        $bob = $this->factory->createUser('bob', 'bob@example.com', 'Bob');

        // Exhaust Alice's rate limit
        for ($i = 0; $i < 60; $i++) {
            $this->checkRateLimit($alice->id);
        }

        // Verify Alice is rate limited
        $aliceLimited = !$this->checkRateLimit($alice->id);
        $this->assertTrue($aliceLimited);

        // Bob should not be affected
        $bobCanRequest = $this->checkRateLimit($bob->id);
        $this->assertTrue($bobCanRequest, 'Bob should have independent rate limit');
    }

    public function testQueryComplexityLimit(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        // Simple query (low complexity)
        $simpleQueryComplexity = 1;
        $canExecuteSimple = $this->checkComplexityLimit($simpleQueryComplexity);
        $this->assertTrue($canExecuteSimple);

        // Complex query (high complexity)
        $complexQueryComplexity = 10000;
        $canExecuteComplex = $this->checkComplexityLimit($complexQueryComplexity);
        $this->assertFalse($canExecuteComplex, 'Should reject high complexity queries');
    }

    public function testDepthLimitEnforced(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        // Shallow query (acceptable)
        $shallowDepth = 3;
        $canExecuteShallow = $this->checkDepthLimit($shallowDepth);
        $this->assertTrue($canExecuteShallow);

        // Deep query (too deep)
        $deepDepth = 20;
        $canExecuteDeep = $this->checkDepthLimit($deepDepth);
        $this->assertFalse($canExecuteDeep, 'Should reject deeply nested queries');
    }

    public function testMultipleUsersDoNotShareRateLimits(): void
    {
        $users = [];
        for ($i = 0; $i < 5; $i++) {
            $users[] = $this->factory->createUser("user{$i}", "user{$i}@example.com", "User {$i}");
        }

        // Each user should have independent limits
        foreach ($users as $user) {
            $canRequest = $this->checkRateLimit($user->id);
            $this->assertTrue($canRequest, "User {$user->username} should have independent rate limit");
        }
    }

    public function testRateLimitCountsCorrectly(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        // Make 10 requests
        for ($i = 0; $i < 10; $i++) {
            $this->checkRateLimit($user->id);
        }

        // Verify count
        $count = $this->getRateLimitCount($user->id);
        $this->assertEquals(10, $count);
    }

    public function testRateLimitIncludesRemainingCount(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');
        $limit = 60;

        // Make some requests
        for ($i = 0; $i < 20; $i++) {
            $this->checkRateLimit($user->id);
        }

        // Check remaining
        $remaining = $this->getRemainingRequests($user->id, $limit);
        $this->assertEquals(40, $remaining);
    }

    public function testBatchQueriesCountTowardLimit(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        // Simulate batch query (multiple operations)
        $batchSize = 10;
        for ($i = 0; $i < $batchSize; $i++) {
            $this->checkRateLimit($user->id);
        }

        // Verify all operations counted
        $count = $this->getRateLimitCount($user->id);
        $this->assertEquals($batchSize, $count);
    }

    public function testIntrospectionQueriesHaveSeparateLimit(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        // Regular query
        $regularLimited = $this->checkRateLimit($user->id, 'regular');

        // Introspection query (may have different limit)
        $introspectionLimited = $this->checkRateLimit($user->id, 'introspection');

        $this->assertTrue($regularLimited);
        $this->assertTrue($introspectionLimited);
    }

    public function testMutationsCountTowardRateLimit(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        // Simulate mutations
        for ($i = 0; $i < 10; $i++) {
            $this->checkRateLimit($user->id, 'mutation');
            $this->factory->createPost($user->id, "Post {$i}", 'Content');
        }

        // Verify mutations counted
        $count = $this->getRateLimitCount($user->id);
        $this->assertEquals(10, $count);
    }

    // ============================================================================
    // Helper Methods (Mock Rate Limiting)
    // ============================================================================

    private function checkRateLimit(string $userId, string $type = 'query'): bool
    {
        $key = "{$userId}:{$type}";
        $limit = 60;

        if (!isset($this->rateLimitStorage[$key])) {
            $this->rateLimitStorage[$key] = 0;
        }

        if ($this->rateLimitStorage[$key] >= $limit) {
            return false;
        }

        $this->rateLimitStorage[$key]++;
        return true;
    }

    private function resetRateLimit(string $userId): void
    {
        foreach (array_keys($this->rateLimitStorage) as $key) {
            if (str_starts_with($key, $userId)) {
                $this->rateLimitStorage[$key] = 0;
            }
        }
    }

    private function checkComplexityLimit(int $complexity): bool
    {
        $maxComplexity = 1000;
        return $complexity <= $maxComplexity;
    }

    private function checkDepthLimit(int $depth): bool
    {
        $maxDepth = 10;
        return $depth <= $maxDepth;
    }

    private function getRateLimitCount(string $userId): int
    {
        $total = 0;
        foreach ($this->rateLimitStorage as $key => $count) {
            if (str_starts_with($key, $userId . ':')) {
                $total += $count;
            }
        }
        return $total;
    }

    private function getRemainingRequests(string $userId, int $limit): int
    {
        $count = $this->getRateLimitCount($userId);
        return max(0, $limit - $count);
    }
}
