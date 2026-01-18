<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/TestFactory.php';

class ResolverTest extends TestCase
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
    // User Query Tests
    // ============================================================================

    public function testQueryUserByUuid(): void
    {
        $user = $this->factory->createUser('alice', 'alice@example.com', 'Alice Smith', 'Hello!');

        $result = $this->factory->getUser($user->id);

        $this->assertNotNull($result);
        $this->assertEquals($user->id, $result->id);
        $this->assertEquals('alice', $result->username);
        $this->assertEquals('Alice Smith', $result->fullName);
        $this->assertEquals('Hello!', $result->bio);
    }

    public function testQueryUsersReturnsList(): void
    {
        $this->factory->createUser('alice', 'alice@example.com', 'Alice');
        $this->factory->createUser('bob', 'bob@example.com', 'Bob');
        $this->factory->createUser('charlie', 'charlie@example.com', 'Charlie');

        $users = $this->factory->getAllUsers();

        $this->assertCount(3, $users);
    }

    public function testQueryUserNotFound(): void
    {
        $result = $this->factory->getUser('non-existent-id');

        $this->assertNull($result);
    }

    // ============================================================================
    // Post Query Tests
    // ============================================================================

    public function testQueryPostById(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'Test Post', 'Test content');

        $result = $this->factory->getPost($post->id);

        $this->assertNotNull($result);
        $this->assertEquals('Test Post', $result->title);
        $this->assertEquals('Test content', $result->content);
    }

    public function testQueryPostsByAuthor(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $this->factory->createPost($user->id, 'Post 1', 'Content 1');
        $this->factory->createPost($user->id, 'Post 2', 'Content 2');

        $posts = $this->factory->getPostsByAuthor($user->pkUser);

        $this->assertCount(2, $posts);
    }

    // ============================================================================
    // Comment Query Tests
    // ============================================================================

    public function testQueryCommentById(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Test Post', 'Content');
        $commenter = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $comment = $this->factory->createComment($commenter->id, $post->id, 'Great post!');

        $result = $this->factory->getComment($comment->id);

        $this->assertNotNull($result);
        $this->assertEquals('Great post!', $result->content);
    }

    public function testQueryCommentsByPost(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Test Post', 'Content');
        $commenter = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $this->factory->createComment($commenter->id, $post->id, 'Comment 1');
        $this->factory->createComment($commenter->id, $post->id, 'Comment 2');

        $comments = $this->factory->getCommentsByPost($post->pkPost);

        $this->assertCount(2, $comments);
    }

    // ============================================================================
    // Relationship Tests
    // ============================================================================

    public function testUserPostsRelationship(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post1 = $this->factory->createPost($user->id, 'Post 1', 'Content 1');
        $post2 = $this->factory->createPost($user->id, 'Post 2', 'Content 2');

        $posts = $this->factory->getPostsByAuthor($user->pkUser);

        $this->assertCount(2, $posts);
        $postIds = array_map(fn($p) => $p->id, $posts);
        $this->assertContains($post1->id, $postIds);
        $this->assertContains($post2->id, $postIds);
    }

    public function testPostAuthorRelationship(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Test Post', 'Content');

        $this->assertNotNull($post->author);
        $this->assertEquals($author->pkUser, $post->author->pkUser);
    }

    public function testCommentAuthorRelationship(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Test Post', 'Content');
        $commenter = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $comment = $this->factory->createComment($commenter->id, $post->id, 'Great!');

        $this->assertNotNull($comment->author);
        $this->assertEquals($commenter->pkUser, $comment->author->pkUser);
    }

    // ============================================================================
    // Edge Case Tests
    // ============================================================================

    public function testNullBio(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        $this->assertNull($user->bio);
    }

    public function testEmptyPostsList(): void
    {
        $user = $this->factory->createUser('newuser', 'new@example.com', 'New User');

        $posts = $this->factory->getPostsByAuthor($user->pkUser);

        $this->assertEmpty($posts);
    }

    public function testSpecialCharactersInContent(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $specialContent = "Test with 'quotes' and \"double quotes\" and <html>";
        $post = $this->factory->createPost($user->id, 'Special', $specialContent);

        $this->assertEquals($specialContent, $post->content);
    }

    public function testUnicodeContent(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $unicodeContent = 'Test with émojis 🎉 and ñ and 中文';
        $post = $this->factory->createPost($user->id, 'Unicode', $unicodeContent);

        $this->assertEquals($unicodeContent, $post->content);
    }

    // ============================================================================
    // Performance Tests
    // ============================================================================

    public function testCreateManyPosts(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');

        for ($i = 0; $i < 50; $i++) {
            $this->factory->createPost($user->id, "Post {$i}", 'Content');
        }

        $posts = $this->factory->getPostsByAuthor($user->pkUser);
        $this->assertCount(50, $posts);
    }

    public function testReset(): void
    {
        $this->factory->createUser('user1', 'user1@example.com', 'User 1');
        $this->factory->createUser('user2', 'user2@example.com', 'User 2');

        $this->factory->reset();

        $this->assertEmpty($this->factory->getAllUsers());
    }

    // ============================================================================
    // Validation Tests
    // ============================================================================

    public function testValidUuid(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        $this->assertTrue(ValidationHelper::isValidUuid($user->id));
    }

    public function testCreatePostWithInvalidAuthor(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Author not found');

        $this->factory->createPost('invalid-author', 'Test', 'Content');
    }

    public function testCreateCommentWithInvalidPost(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User');

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Post not found');

        $this->factory->createComment($user->id, 'invalid-post', 'Content');
    }

    public function testLongContent(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $longContent = DataGenerator::generateLongString(100000);
        $post = $this->factory->createPost($user->id, 'Long', $longContent);

        $this->assertEquals(100000, strlen($post->content));
    }
}
