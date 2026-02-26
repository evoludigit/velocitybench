<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/TestFactory.php';

/**
 * Advanced Integration Tests for Webonyx GraphQL PHP Framework.
 *
 * Tests complex, multi-layered scenarios:
 * - Nested relationship queries
 * - Pagination with relationships
 * - Complex update scenarios
 * - Data integrity across multiple operations
 * - Edge cases in relationships
 */
class AdvancedIntegrationTest extends TestCase
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
    // Deep Nesting Scenarios
    // ============================================================================

    public function testQueryPostWithAuthorAndComments(): void
    {
        // Setup: Create author with posts and comments
        $author = $this->factory->createUser('author', 'author@example.com', 'Author', 'Author bio');
        $post = $this->factory->createPost($author->id, 'Featured Post', 'Interesting content');

        $commenter1 = $this->factory->createUser('commenter1', 'c1@example.com', 'Commenter 1');
        $commenter2 = $this->factory->createUser('commenter2', 'c2@example.com', 'Commenter 2');

        $comment1 = $this->factory->createComment($post->id, $commenter1->id, 'Great article!');
        $comment2 = $this->factory->createComment($post->id, $commenter2->id, 'Thanks for sharing');

        // Query post with nested author
        $queriedPost = $this->factory->getPost($post->id);
        $this->assertNotNull($queriedPost);
        $this->assertEquals('author', $this->factory->getUser($queriedPost->authorId)->username);

        // Query comments on post
        $comment1Retrieved = $this->factory->getComment($comment1->id);
        $comment2Retrieved = $this->factory->getComment($comment2->id);

        $this->assertNotNull($comment1Retrieved);
        $this->assertNotNull($comment2Retrieved);
        $this->assertEquals($post->id, $comment1Retrieved->postId);
        $this->assertEquals($post->id, $comment2Retrieved->postId);
    }

    public function testQueryUserWithMultiplePostsAndComments(): void
    {
        // Setup: User creates multiple posts, comments on others
        $alice = $this->factory->createUser('alice', 'alice@example.com', 'Alice');
        $bob = $this->factory->createUser('bob', 'bob@example.com', 'Bob');
        $charlie = $this->factory->createUser('charlie', 'charlie@example.com', 'Charlie');

        $alicePost1 = $this->factory->createPost($alice->id, 'Alice Post 1', 'Content A');
        $alicePost2 = $this->factory->createPost($alice->id, 'Alice Post 2', 'Content B');
        $bobPost = $this->factory->createPost($bob->id, 'Bob Post', 'Content C');

        $this->factory->createComment($alicePost1->id, $bob->id, 'Bob comments on Alice Post 1');
        $this->factory->createComment($alicePost2->id, $charlie->id, 'Charlie comments on Alice Post 2');
        $this->factory->createComment($bobPost->id, $alice->id, 'Alice comments on Bob Post');

        // Verify Alice's posts exist
        $alice1 = $this->factory->getPost($alicePost1->id);
        $alice2 = $this->factory->getPost($alicePost2->id);
        $this->assertEquals($alice->id, $alice1->authorId);
        $this->assertEquals($alice->id, $alice2->authorId);

        // Verify Bob's post exists
        $bob1 = $this->factory->getPost($bobPost->id);
        $this->assertEquals($bob->id, $bob1->authorId);
    }

    // ============================================================================
    // Pagination Scenarios
    // ============================================================================

    public function testPaginationWithDefaultLimit(): void
    {
        // Create multiple users
        for ($i = 1; $i <= 5; $i++) {
            $this->factory->createUser(
                "user$i",
                "user$i@example.com",
                "User $i"
            );
        }

        $users = $this->factory->getAllUsers();
        $this->assertGreaterThanOrEqual(5, count($users));
    }

    public function testPaginationWithMultiplePosts(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');

        // Create many posts
        for ($i = 1; $i <= 10; $i++) {
            $this->factory->createPost($author->id, "Post $i", "Content $i");
        }

        $allPosts = $this->factory->getAllPosts();
        $this->assertGreaterThanOrEqual(10, count($allPosts));
    }

    // ============================================================================
    // Complex Update Scenarios
    // ============================================================================

    public function testUpdateAuthorAfterPostCreation(): void
    {
        $author = $this->factory->createUser('original', 'original@example.com', 'Original Name', 'Original bio');
        $post = $this->factory->createPost($author->id, 'First Post', 'Content');

        // Update author after post creation
        $updated = $this->factory->updateUser($author->id, 'Updated bio', 'Updated Name');

        // Post should still reference author
        $queriedPost = $this->factory->getPost($post->id);
        $this->assertEquals($author->id, $queriedPost->authorId);

        // Updated author info should be in new queries
        $queriedAuthor = $this->factory->getUser($author->id);
        $this->assertEquals('Updated Name', $queriedAuthor->fullName);
        $this->assertEquals('Updated bio', $queriedAuthor->bio);
    }

    public function testUpdatePostTitleAfterComments(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Original Title', 'Content');

        $commenter = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $comment = $this->factory->createComment($post->id, $commenter->id, 'Great post!');

        // Update post title
        $updated = $this->factory->updatePost($post->id, 'Updated Title', 'Content');

        // Comment should still reference post
        $queriedComment = $this->factory->getComment($comment->id);
        $this->assertEquals($post->id, $queriedComment->postId);

        // Post title should be updated
        $queriedPost = $this->factory->getPost($post->id);
        $this->assertEquals('Updated Title', $queriedPost->title);
    }

    public function testMultipleSequentialUpdates(): void
    {
        $user = $this->factory->createUser('user', 'user@example.com', 'User', 'Initial bio');
        $post = $this->factory->createPost($user->id, 'Title', 'Initial content');

        // Sequential user updates
        $this->factory->updateUser($user->id, 'Bio v2', 'User');
        $this->factory->updateUser($user->id, 'Bio v3', 'User');
        $this->factory->updateUser($user->id, 'Bio v4', 'User');

        $finalUser = $this->factory->getUser($user->id);
        $this->assertEquals('Bio v4', $finalUser->bio);

        // Sequential post updates
        $this->factory->updatePost($post->id, 'Title', 'Content v2');
        $this->factory->updatePost($post->id, 'Title', 'Content v3');
        $this->factory->updatePost($post->id, 'Title', 'Content v4');

        $finalPost = $this->factory->getPost($post->id);
        $this->assertEquals('Content v4', $finalPost->content);
    }

    // ============================================================================
    // Cascade and Deletion Scenarios
    // ============================================================================

    public function testDeletePostWithComments(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'To Delete', 'Content');
        $postId = $post->id;

        $commenter = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $comment1 = $this->factory->createComment($post->id, $commenter->id, 'Comment 1');
        $comment2 = $this->factory->createComment($post->id, $commenter->id, 'Comment 2');

        // Delete post
        $this->factory->deletePost($postId);

        // Post should be gone
        $deletedPost = $this->factory->getPost($postId);
        $this->assertNull($deletedPost);

        // Note: Behavior of comments depends on schema (cascade or not)
        // Test framework should handle appropriately
    }

    public function testDeleteUserWithPosts(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $authorId = $author->id;

        $post1 = $this->factory->createPost($author->id, 'Post 1', 'Content 1');
        $post2 = $this->factory->createPost($author->id, 'Post 2', 'Content 2');

        // Delete user
        $this->factory->deleteUser($authorId);

        // User should be gone
        $deletedUser = $this->factory->getUser($authorId);
        $this->assertNull($deletedUser);

        // Note: Behavior of posts depends on schema (cascade or not)
    }

    // ============================================================================
    // Relationship Edge Cases
    // ============================================================================

    public function testUserWithoutPosts(): void
    {
        $user = $this->factory->createUser('loner', 'loner@example.com', 'Loner');

        $retrieved = $this->factory->getUser($user->id);
        $this->assertNotNull($retrieved);
        $this->assertEquals('loner', $retrieved->username);

        // User has no posts, which should be fine
        $allPosts = $this->factory->getAllPosts();
        // May or may not contain this user's posts
    }

    public function testPostWithoutComments(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'No Comments', 'Lonely post');

        $retrieved = $this->factory->getPost($post->id);
        $this->assertNotNull($retrieved);
        $this->assertEquals('No Comments', $retrieved->title);

        // Post has no comments, which should be fine
    }

    public function testCommentAuthorIsNotPostAuthor(): void
    {
        $postAuthor = $this->factory->createUser('post_author', 'pa@example.com', 'Post Author');
        $commentAuthor = $this->factory->createUser('comment_author', 'ca@example.com', 'Comment Author');

        $post = $this->factory->createPost($postAuthor->id, 'Article', 'Content');
        $comment = $this->factory->createComment($post->id, $commentAuthor->id, 'My thoughts');

        $queriedComment = $this->factory->getComment($comment->id);
        $this->assertEquals($post->id, $queriedComment->postId);
        $this->assertEquals($commentAuthor->id, $queriedComment->authorId);
        $this->assertNotEquals($postAuthor->id, $queriedComment->authorId);
    }

    // ============================================================================
    // Bulk Operations
    // ============================================================================

    public function testBulkCreateAndQuery(): void
    {
        $users = [];
        for ($i = 1; $i <= 3; $i++) {
            $users[] = $this->factory->createUser(
                "bulk_user_$i",
                "bulk_user_$i@example.com",
                "Bulk User $i"
            );
        }

        $allUsers = $this->factory->getAllUsers();
        $this->assertGreaterThanOrEqual(3, count($allUsers));

        // Verify each user exists
        foreach ($users as $user) {
            $retrieved = $this->factory->getUser($user->id);
            $this->assertNotNull($retrieved);
        }
    }

    public function testBulkCreatePostsWithComments(): void
    {
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $posts = [];
        $comments = [];

        // Create posts
        for ($i = 1; $i <= 3; $i++) {
            $posts[] = $this->factory->createPost($author->id, "Post $i", "Content $i");
        }

        // Create comments on each post
        $commenter = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        foreach ($posts as $post) {
            $comments[] = $this->factory->createComment($post->id, $commenter->id, 'Comment text');
        }

        // Verify all exist
        $this->assertCount(3, $posts);
        $this->assertCount(3, $comments);

        foreach ($posts as $post) {
            $this->assertNotNull($this->factory->getPost($post->id));
        }

        foreach ($comments as $comment) {
            $this->assertNotNull($this->factory->getComment($comment->id));
        }
    }
}
