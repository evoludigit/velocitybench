<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/TestFactory.php';

/**
 * Integration Tests for Webonyx GraphQL PHP Framework.
 *
 * Tests multi-step scenarios combining multiple operations:
 * - Create user → create post → add comment flow
 * - Query relationships
 * - Verify data consistency across operations
 * - Update cascade effects
 */
class IntegrationTest extends TestCase
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
    // User → Post → Comment Flow
    // ============================================================================

    public function testCompleteContentCreationFlow(): void
    {
        // Step 1: Create user
        $author = $this->factory->createUser('alice', 'alice@example.com', 'Alice Smith', 'Software developer');
        $this->assertNotNull($author);
        $this->assertEquals('alice', $author->username);

        // Step 2: Create post by user
        $post = $this->factory->createPost($author->id, 'First Blog Post', 'This is my first post on the platform');
        $this->assertNotNull($post);
        $this->assertEquals('First Blog Post', $post->title);

        // Step 3: Retrieve post and verify author relationship
        $retrievedPost = $this->factory->getPost($post->id);
        $this->assertNotNull($retrievedPost);
        $this->assertEquals($author->id, $retrievedPost->authorId);

        // Step 4: Create comment on post
        $commenter = $this->factory->createUser('bob', 'bob@example.com', 'Bob Johnson');
        $comment = $this->factory->createComment($post->id, $commenter->id, 'Great post! I really enjoyed reading this.');
        $this->assertNotNull($comment);

        // Step 5: Retrieve comment and verify relationships
        $retrievedComment = $this->factory->getComment($comment->id);
        $this->assertNotNull($retrievedComment);
        $this->assertEquals($post->id, $retrievedComment->postId);
        $this->assertEquals($commenter->id, $retrievedComment->authorId);
    }

    public function testMultipleCommentsOnSinglePost(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Popular Post', 'This post gets many comments');

        // Create multiple comments from different users
        $commenter1 = $this->factory->createUser('user1', 'user1@example.com', 'User 1');
        $commenter2 = $this->factory->createUser('user2', 'user2@example.com', 'User 2');
        $commenter3 = $this->factory->createUser('user3', 'user3@example.com', 'User 3');

        $comment1 = $this->factory->createComment($post->id, $commenter1->id, 'First comment');
        $comment2 = $this->factory->createComment($post->id, $commenter2->id, 'Second comment');
        $comment3 = $this->factory->createComment($post->id, $commenter3->id, 'Third comment');

        // Verify all comments exist
        $retrieved1 = $this->factory->getComment($comment1->id);
        $retrieved2 = $this->factory->getComment($comment2->id);
        $retrieved3 = $this->factory->getComment($comment3->id);

        $this->assertNotNull($retrieved1);
        $this->assertNotNull($retrieved2);
        $this->assertNotNull($retrieved3);

        // Verify each comment is associated with the correct post
        $this->assertEquals($post->id, $retrieved1->postId);
        $this->assertEquals($post->id, $retrieved2->postId);
        $this->assertEquals($post->id, $retrieved3->postId);
    }

    public function testMultiplePostsByUser(): void
    {
        $author = $this->factory->createUser('prolific', 'prolific@example.com', 'Prolific Writer');

        $post1 = $this->factory->createPost($author->id, 'First Post', 'Content 1');
        $post2 = $this->factory->createPost($author->id, 'Second Post', 'Content 2');
        $post3 = $this->factory->createPost($author->id, 'Third Post', 'Content 3');

        // Verify all posts exist and are associated with correct author
        $retrieved1 = $this->factory->getPost($post1->id);
        $retrieved2 = $this->factory->getPost($post2->id);
        $retrieved3 = $this->factory->getPost($post3->id);

        $this->assertEquals($author->id, $retrieved1->authorId);
        $this->assertEquals($author->id, $retrieved2->authorId);
        $this->assertEquals($author->id, $retrieved3->authorId);
    }

    // ============================================================================
    // Update Operations with Relationships
    // ============================================================================

    public function testUpdateUserDoesNotAffectPosts(): void
    {
        $author = $this->factory->createUser('original', 'original@example.com', 'Original Name');
        $post = $this->factory->createPost($author->id, 'Title', 'Content');
        $originalPostId = $post->id;

        // Update user profile
        $this->factory->updateUser($author->id, 'Updated bio', 'Updated Name');

        // Post should still exist and be unchanged
        $retrievedPost = $this->factory->getPost($originalPostId);
        $this->assertNotNull($retrievedPost);
        $this->assertEquals('Title', $retrievedPost->title);
        $this->assertEquals('Content', $retrievedPost->content);
    }

    public function testUpdatePostDoesNotAffectAuthor(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Original Title', 'Original Content');

        // Update post
        $this->factory->updatePost($post->id, 'Updated Title', 'Updated Content');

        // Author should remain unchanged
        $retrievedAuthor = $this->factory->getUser($author->id);
        $this->assertNotNull($retrievedAuthor);
        $this->assertEquals('author', $retrievedAuthor->username);
        $this->assertEquals('Author', $retrievedAuthor->fullName);
    }

    // ============================================================================
    // Query and Filter Integration
    // ============================================================================

    public function testListAllUsersAfterCreation(): void
    {
        $this->factory->createUser('alice', 'alice@example.com', 'Alice');
        $this->factory->createUser('bob', 'bob@example.com', 'Bob');
        $this->factory->createUser('charlie', 'charlie@example.com', 'Charlie');

        $allUsers = $this->factory->getAllUsers();
        $this->assertGreaterThanOrEqual(3, count($allUsers));
    }

    public function testListAllPostsAfterCreation(): void
    {
        $author1 = $this->factory->createUser('author1', 'author1@example.com', 'Author 1');
        $author2 = $this->factory->createUser('author2', 'author2@example.com', 'Author 2');

        $this->factory->createPost($author1->id, 'Post 1', 'Content 1');
        $this->factory->createPost($author2->id, 'Post 2', 'Content 2');

        $allPosts = $this->factory->getAllPosts();
        $this->assertGreaterThanOrEqual(2, count($allPosts));
    }

    // ============================================================================
    // Transaction-like Behavior
    // ============================================================================

    public function testCreateAndDeleteUser(): void
    {
        $user = $this->factory->createUser('temporary', 'temporary@example.com', 'Temporary User');
        $userId = $user->id;

        $retrieved = $this->factory->getUser($userId);
        $this->assertNotNull($retrieved);

        $this->factory->deleteUser($userId);

        $deleted = $this->factory->getUser($userId);
        $this->assertNull($deleted);
    }

    public function testCreateDeleteCreateSameUser(): void
    {
        $user1 = $this->factory->createUser('username', 'user1@example.com', 'User 1');
        $this->factory->deleteUser($user1->id);

        // Can create new user with same username but different email
        $user2 = $this->factory->createUser('username', 'user2@example.com', 'User 2');
        $this->assertNotNull($user2);
        $this->assertEquals('username', $user2->username);
        $this->assertEquals('user2@example.com', $user2->email);
    }

    // ============================================================================
    // Complex Scenarios
    // ============================================================================

    public function testCommentThreadSimulation(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Discussion Topic', "Let's discuss this...");

        $user1 = $this->factory->createUser('user1', 'user1@example.com', 'User 1');
        $user2 = $this->factory->createUser('user2', 'user2@example.com', 'User 2');
        $user3 = $this->factory->createUser('user3', 'user3@example.com', 'User 3');

        // Create initial comment
        $comment1 = $this->factory->createComment($post->id, $user1->id, 'I think ...');
        $this->assertNotNull($comment1);

        // User 2 responds
        $comment2 = $this->factory->createComment($post->id, $user2->id, 'I agree, but also ...');
        $this->assertNotNull($comment2);

        // User 3 adds another perspective
        $comment3 = $this->factory->createComment($post->id, $user3->id, 'Different angle: ...');
        $this->assertNotNull($comment3);

        // All comments should reference the same post
        $this->assertEquals($post->id, $this->factory->getComment($comment1->id)->postId);
        $this->assertEquals($post->id, $this->factory->getComment($comment2->id)->postId);
        $this->assertEquals($post->id, $this->factory->getComment($comment3->id)->postId);
    }
}
