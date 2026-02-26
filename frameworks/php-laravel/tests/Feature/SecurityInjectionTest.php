<?php

namespace Tests\Feature;

use Tests\TestCase;
use Tests\Traits\DatabaseTrait;

/**
 * SecurityInjectionTest - Tests SQL injection prevention
 *
 * Coverage includes:
 * - Basic OR injection attempts
 * - UNION-based injection attempts
 * - Stacked queries
 * - Comment sequence injection
 * - Time-based blind injection attempts
 */
class SecurityInjectionTest extends TestCase
{
    use DatabaseTrait;

    // ========================================================================
    // SQL Injection Prevention Tests
    // ========================================================================

    public function test_prevents_basic_sql_injection_in_user_query(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $maliciousInput = "1' OR '1'='1";

        // Act - Try to inject via username parameter
        $response = $this->getJson("/api/users?username=" . urlencode($maliciousInput));

        // Assert - Should not return all users or cause error
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertIsArray($data);
        // Should return empty array or specific error, not all users
        $this->assertCount(0, $data);
    }

    public function test_prevents_union_based_injection(): void
    {
        // Arrange
        $user = $this->createTestUser('bob', 'bob@example.com', 'Bob');
        $maliciousInput = "1' UNION SELECT * FROM users--";

        // Act
        $response = $this->getJson("/api/users?username=" . urlencode($maliciousInput));

        // Assert - Should handle safely
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertIsArray($data);
        $this->assertCount(0, $data);
    }

    public function test_prevents_stacked_queries(): void
    {
        // Arrange
        $user = $this->createTestUser('charlie', 'charlie@example.com', 'Charlie');
        $maliciousInput = "1'; DROP TABLE users;--";

        // Act
        $response = $this->getJson("/api/users?username=" . urlencode($maliciousInput));

        // Assert - Should handle safely
        $response->assertStatus(200);

        // Verify users table still exists by creating another user
        $testUser = $this->createTestUser('test', 'test@example.com', 'Test');
        $this->assertNotNull($testUser);
    }

    public function test_prevents_comment_sequence_injection(): void
    {
        // Arrange
        $user = $this->createTestUser('dave', 'dave@example.com', 'Dave');
        $maliciousInput = "admin'--";

        // Act
        $response = $this->getJson("/api/users?username=" . urlencode($maliciousInput));

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(0, $data);
    }

    public function test_prevents_time_based_blind_injection(): void
    {
        // Arrange
        $user = $this->createTestUser('eve', 'eve@example.com', 'Eve');
        $maliciousInput = "1' AND SLEEP(5)--";

        // Act
        $startTime = microtime(true);
        $response = $this->getJson("/api/users?username=" . urlencode($maliciousInput));
        $endTime = microtime(true);
        $duration = $endTime - $startTime;

        // Assert - Should not execute SLEEP, response should be fast
        $response->assertStatus(200);
        $this->assertLessThan(2.0, $duration, 'Query should not execute SLEEP command');
    }

    public function test_prevents_injection_in_post_search(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');
        $maliciousInput = "1' OR '1'='1";

        // Act
        $response = $this->getJson("/api/posts?title=" . urlencode($maliciousInput));

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertIsArray($data);
        $this->assertCount(0, $data);
    }

    public function test_prevents_injection_via_post_id(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');
        $maliciousId = "1 OR 1=1";

        // Act
        $response = $this->getJson("/api/posts/" . urlencode($maliciousId));

        // Assert - Should return 404 or handle safely
        $this->assertTrue(
            $response->status() === 404 || $response->status() === 400,
            'Should reject malicious ID with 404 or 400'
        );
    }

    public function test_parametrized_queries_with_special_chars(): void
    {
        // Arrange - Create user with SQL-like characters in name
        $specialName = "O'Brien <script>alert('xss')</script>";
        $user = $this->createTestUser('obrien', 'obrien@example.com', $specialName);

        // Act - Retrieve by ID (should use parameterized query)
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert - Should retrieve correctly without injection
        $response->assertStatus(200)
            ->assertJson([
                'id' => $user->id,
                'fullName' => $specialName,
            ]);
    }

    public function test_prevents_injection_in_pagination_params(): void
    {
        // Arrange
        for ($i = 0; $i < 5; $i++) {
            $this->createTestUser("user{$i}", "user{$i}@example.com");
        }
        $maliciousLimit = "10; DROP TABLE users";

        // Act
        $response = $this->getJson("/api/users?size=" . urlencode($maliciousLimit));

        // Assert - Should handle safely
        $this->assertTrue(
            $response->status() === 200 || $response->status() === 400,
            'Should handle malicious pagination parameter safely'
        );
    }

    public function test_prevents_hex_encoded_injection(): void
    {
        // Arrange
        $user = $this->createTestUser('frank', 'frank@example.com', 'Frank');
        $maliciousInput = "0x61646D696E"; // Hex for 'admin'

        // Act
        $response = $this->getJson("/api/users?username=" . urlencode($maliciousInput));

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(0, $data);
    }
}
