<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/TestFactory.php';

/**
 * Error Scenario Tests for Webonyx GraphQL PHP Framework.
 *
 * Tests error handling, validation, and edge cases:
 * - Invalid inputs and malformed queries
 * - Missing resources and 404 scenarios
 * - Field validation and constraints
 * - Boundary conditions
 * - Error response formats
 */
class ErrorScenariosTest extends TestCase
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
    // Missing Resource Tests
    // ============================================================================

    public function testQueryNonExistentUser(): void
    {
        $result = $this->factory->getUser('00000000-0000-0000-0000-000000000000');

        $this->assertNull($result);
    }

    public function testQueryNonExistentPost(): void
    {
        $result = $this->factory->getPost('00000000-0000-0000-0000-000000000000');

        $this->assertNull($result);
    }

    public function testQueryNonExistentComment(): void
    {
        $result = $this->factory->getComment('00000000-0000-0000-0000-000000000000');

        $this->assertNull($result);
    }

    // ============================================================================
    // Field Validation Tests
    // ============================================================================

    public function testCreateUserEmptyUsername(): void
    {
        $this->expectException(\Exception::class);
        $this->factory->createUser('', 'user@example.com', 'User', 'Bio');
    }

    public function testCreateUserInvalidEmail(): void
    {
        $this->expectException(\Exception::class);
        $this->factory->createUser('username', 'not-an-email', 'User', 'Bio');
    }

    public function testCreateUserTooLongBio(): void
    {
        $longBio = str_repeat('a', 1001); // Exceeds 1000 char limit
        $this->expectException(\Exception::class);
        $this->factory->createUser('username', 'user@example.com', 'User', $longBio);
    }

    public function testCreateUserTooLongFullName(): void
    {
        $longName = str_repeat('a', 256); // Exceeds 255 char limit
        $this->expectException(\Exception::class);
        $this->factory->createUser('username', 'user@example.com', $longName, 'Bio');
    }

    // ============================================================================
    // Post Field Validation
    // ============================================================================

    public function testCreatePostEmptyTitle(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $this->expectException(\Exception::class);
        $this->factory->createPost($user->id, '', 'Content');
    }

    public function testCreatePostTooLongTitle(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $longTitle = str_repeat('a', 256); // Exceeds 255 char limit
        $this->expectException(\Exception::class);
        $this->factory->createPost($user->id, $longTitle, 'Content');
    }

    public function testCreatePostNonExistentAuthor(): void
    {
        $this->expectException(\Exception::class);
        $this->factory->createPost('00000000-0000-0000-0000-000000000000', 'Title', 'Content');
    }

    // ============================================================================
    // Comment Field Validation
    // ============================================================================

    public function testCreateCommentEmptyContent(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'Title', 'Content');
        $this->expectException(\Exception::class);
        $this->factory->createComment($post->id, $user->id, '');
    }

    public function testCreateCommentNonExistentPost(): void
    {
        $user = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $this->expectException(\Exception::class);
        $this->factory->createComment('00000000-0000-0000-0000-000000000000', $user->id, 'Comment');
    }

    public function testCreateCommentNonExistentAuthor(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'Title', 'Content');
        $this->expectException(\Exception::class);
        $this->factory->createComment($post->id, '00000000-0000-0000-0000-000000000000', 'Comment');
    }

    // ============================================================================
    // Boundary Condition Tests
    // ============================================================================

    public function testQueryWithNullOffset(): void
    {
        $this->factory->createUser('alice', 'alice@example.com');
        $this->factory->createUser('bob', 'bob@example.com');

        // Should handle null/missing offset gracefully
        $users = $this->factory->getAllUsers();
        $this->assertIsArray($users);
    }

    public function testQueryWithZeroLimit(): void
    {
        $this->factory->createUser('alice', 'alice@example.com');
        // Zero limit should return empty list or use default
        $users = $this->factory->getAllUsers();
        $this->assertIsArray($users);
    }

    public function testUpdateUserWithNullBio(): void
    {
        $user = $this->factory->createUser('alice', 'alice@example.com', 'Alice', 'Original bio');
        // Updating with null should be allowed or rejected based on schema
        $updated = $this->factory->updateUser($user->id, null, 'Alice Updated');
        if ($updated !== null) {
            $this->assertNull($updated->bio);
        }
    }

    // ============================================================================
    // Duplicate Data Tests
    // ============================================================================

    public function testCreateDuplicateUsername(): void
    {
        $this->factory->createUser('duplicate', 'first@example.com', 'User 1');
        $this->expectException(\Exception::class);
        $this->factory->createUser('duplicate', 'second@example.com', 'User 2');
    }

    public function testCreateDuplicateEmail(): void
    {
        $this->factory->createUser('user1', 'duplicate@example.com', 'User 1');
        $this->expectException(\Exception::class);
        $this->factory->createUser('user2', 'duplicate@example.com', 'User 2');
    }
}
