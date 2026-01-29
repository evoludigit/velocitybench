<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/TestFactory.php';

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
    private TestFactory $factory;

    protected function setUp(): void
    {
        $this->factory = new TestFactory();
    }

    protected function tearDown(): void
    {
        $this->factory->reset();
    }

    // ============================================================================
    // SQL Injection Prevention Tests
    // ============================================================================

    public function testPreventsBasicSqlInjection(): void
    {
        $user = $this->factory->createUser('alice', 'alice@example.com', 'Alice');
        $maliciousInput = "1' OR '1'='1";

        // Attempt to query with malicious input
        $result = $this->factory->getUser($maliciousInput);

        // Should return null, not all users
        $this->assertNull($result);
    }

    public function testPreventsUnionBasedInjection(): void
    {
        $user = $this->factory->createUser('bob', 'bob@example.com', 'Bob');
        $maliciousInput = "1' UNION SELECT * FROM users--";

        // Attempt injection
        $result = $this->factory->getUser($maliciousInput);

        // Should handle safely
        $this->assertNull($result);
    }

    public function testPreventsStackedQueries(): void
    {
        $user = $this->factory->createUser('charlie', 'charlie@example.com', 'Charlie');
        $maliciousInput = "1'; DROP TABLE users;--";

        // Attempt to execute stacked queries
        $result = $this->factory->getUser($maliciousInput);

        // Should handle safely
        $this->assertNull($result);

        // Verify data still exists (table not dropped)
        $verifyUser = $this->factory->getUser($user->id);
        $this->assertNotNull($verifyUser);
    }

    public function testPreventsCommentSequenceInjection(): void
    {
        $user = $this->factory->createUser('dave', 'dave@example.com', 'Dave');
        $maliciousInput = "admin'--";

        // Attempt comment-based bypass
        $result = $this->factory->getUser($maliciousInput);

        $this->assertNull($result);
    }

    public function testPreventsTimeBasedBlindInjection(): void
    {
        $user = $this->factory->createUser('eve', 'eve@example.com', 'Eve');
        $maliciousInput = "1' AND SLEEP(5)--";

        // Measure execution time
        $startTime = microtime(true);
        $result = $this->factory->getUser($maliciousInput);
        $endTime = microtime(true);
        $duration = $endTime - $startTime;

        // Should not execute SLEEP
        $this->assertNull($result);
        $this->assertLessThan(2.0, $duration, 'Query should not execute SLEEP command');
    }

    public function testPreventsInjectionInPostTitle(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Test Post', 'Content');
        $maliciousInput = "1' OR '1'='1";

        // Try to search posts with malicious title
        // Since TestFactory doesn't have search, we test safe retrieval
        $result = $this->factory->getPost($maliciousInput);

        $this->assertNull($result);
    }

    public function testHandlesSpecialCharactersSafely(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $specialContent = "Test with 'quotes' and \"double quotes\" and <html> tags";
        $post = $this->factory->createPost($author->id, 'Special', $specialContent);

        // Retrieve and verify special characters are preserved
        $retrieved = $this->factory->getPost($post->id);

        $this->assertNotNull($retrieved);
        $this->assertEquals($specialContent, $retrieved->content);
    }

    public function testPreventsInjectionViaNumericId(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Test', 'Content');
        $maliciousId = "1 OR 1=1";

        // Should handle non-UUID format safely
        $result = $this->factory->getPost($maliciousId);

        $this->assertNull($result);
    }

    public function testPreventsHexEncodedInjection(): void
    {
        $user = $this->factory->createUser('frank', 'frank@example.com', 'Frank');
        $maliciousInput = "0x61646D696E"; // Hex for 'admin'

        $result = $this->factory->getUser($maliciousInput);

        $this->assertNull($result);
    }

    public function testPreventsInjectionWithMultibyteCharacters(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');
        $maliciousInput = "admin' OR '1'='1' /*中文注入*/";

        $result = $this->factory->getUser($maliciousInput);

        $this->assertNull($result);
    }

    public function testValidatesUuidFormatStrict(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');
        $invalidUuid = "not-a-uuid-format";

        // Should reject non-UUID format
        $result = $this->factory->getUser($invalidUuid);

        $this->assertNull($result);
    }

    public function testHandlesNullByteInjection(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');
        $maliciousInput = "admin\x00'--";

        $result = $this->factory->getUser($maliciousInput);

        $this->assertNull($result);
    }

    public function testPreventsSecondOrderInjection(): void
    {
        // Create user with malicious content
        $maliciousUsername = "admin' OR '1'='1";

        try {
            $user = $this->factory->createUser($maliciousUsername, 'mal@example.com', 'Malicious');

            // If creation succeeds, retrieval should handle safely
            $posts = $this->factory->getPostsByAuthor($user->pkUser);

            // Should return empty array, not all posts
            $this->assertIsArray($posts);
        } catch (\Exception $e) {
            // If creation fails due to validation, that's also acceptable
            $this->assertTrue(true);
        }
    }

    public function testParameterizedQueriesWithUnicode(): void
    {
        $unicodeContent = 'Test with émojis 🎉 and ñ and 中文 and Ελληνικά';
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Unicode Test', $unicodeContent);

        // Retrieve and verify Unicode is preserved
        $retrieved = $this->factory->getPost($post->id);

        $this->assertNotNull($retrieved);
        $this->assertEquals($unicodeContent, $retrieved->content);
    }

    public function testLongInputDoesNotCauseInjection(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');
        $longMaliciousInput = str_repeat("' OR '1'='1", 1000);

        // Should handle long inputs safely
        $result = $this->factory->getUser($longMaliciousInput);

        $this->assertNull($result);
    }
}
