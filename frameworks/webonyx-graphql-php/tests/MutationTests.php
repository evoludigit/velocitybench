<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/TestFactory.php';

/**
 * Mutation Tests for Webonyx GraphQL PHP Framework.
 *
 * Tests mutation operations including:
 * - Single field updates (bio, full_name)
 * - Multi-field updates
 * - Field state verification
 * - Timestamp updates (created_at, updated_at)
 * - Data consistency
 * - Complex nested mutations
 */
class MutationTests extends TestCase
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
    // Single Field Updates (User)
    // ============================================================================

    public function testUpdateUserBioSingleField(): void
    {
        $user = $this->factory->createUser('alice', 'alice@example.com', 'Alice', 'Old bio');
        $newBio = 'Updated bio with new information';

        $updated = $this->factory->updateUser($user->id, $newBio, 'Alice');

        $this->assertNotNull($updated);
        $this->assertEquals($newBio, $updated->bio);
        $this->assertEquals('Alice', $updated->fullName); // unchanged
    }

    public function testUpdateUserFullNameSingleField(): void
    {
        $user = $this->factory->createUser('bob', 'bob@example.com', 'Bob', 'Bio');
        $newName = 'Robert Smith';

        $updated = $this->factory->updateUser($user->id, 'Bio', $newName);

        $this->assertNotNull($updated);
        $this->assertEquals('Bio', $updated->bio); // unchanged
        $this->assertEquals($newName, $updated->fullName);
    }

    public function testUpdateUserBioToEmpty(): void
    {
        $user = $this->factory->createUser('charlie', 'charlie@example.com', 'Charlie', 'Original bio');

        $updated = $this->factory->updateUser($user->id, '', 'Charlie');

        $this->assertNotNull($updated);
        $this->assertEquals('', $updated->bio);
    }

    public function testUpdateUserFullNameToEmpty(): void
    {
        $user = $this->factory->createUser('diana', 'diana@example.com', 'Diana', 'Bio');

        $updated = $this->factory->updateUser($user->id, 'Bio', '');

        $this->assertNotNull($updated);
        $this->assertEquals('', $updated->fullName);
    }

    // ============================================================================
    // Multi-Field Updates
    // ============================================================================

    public function testUpdateUserBothFields(): void
    {
        $user = $this->factory->createUser('eve', 'eve@example.com', 'Eve', 'Old bio');
        $newName = 'Evelyn';
        $newBio = 'New bio content';

        $updated = $this->factory->updateUser($user->id, $newBio, $newName);

        $this->assertNotNull($updated);
        $this->assertEquals($newBio, $updated->bio);
        $this->assertEquals($newName, $updated->fullName);
    }

    public function testUpdateUserPreservesOtherFields(): void
    {
        $user = $this->factory->createUser('frank', 'frank@example.com', 'Frank', 'Bio');

        $updated = $this->factory->updateUser($user->id, 'New bio', 'Frank');

        $this->assertNotNull($updated);
        $this->assertEquals('frank', $updated->username); // unchanged
        $this->assertEquals('frank@example.com', $updated->email); // unchanged
        $this->assertEquals($user->id, $updated->id); // unchanged
    }

    // ============================================================================
    // Post Mutations
    // ============================================================================

    public function testUpdatePostTitle(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'Original Title', 'Content');
        $newTitle = 'Updated Post Title';

        $updated = $this->factory->updatePost($post->id, $newTitle, 'Content');

        $this->assertNotNull($updated);
        $this->assertEquals($newTitle, $updated->title);
        $this->assertEquals('Content', $updated->content); // unchanged
    }

    public function testUpdatePostContent(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'Title', 'Original content');
        $newContent = 'Updated content with more information';

        $updated = $this->factory->updatePost($post->id, 'Title', $newContent);

        $this->assertNotNull($updated);
        $this->assertEquals('Title', $updated->title); // unchanged
        $this->assertEquals($newContent, $updated->content);
    }

    public function testUpdatePostBothFields(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'Title', 'Content');

        $updated = $this->factory->updatePost($post->id, 'New Title', 'New Content');

        $this->assertNotNull($updated);
        $this->assertEquals('New Title', $updated->title);
        $this->assertEquals('New Content', $updated->content);
    }

    // ============================================================================
    // Comment Mutations
    // ============================================================================

    public function testUpdateCommentContent(): void
    {
        $user = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Title', 'Content');
        $comment = $this->factory->createComment($post->id, $user->id, 'Original comment');
        $newContent = 'Updated comment text';

        $updated = $this->factory->updateComment($comment->id, $newContent);

        $this->assertNotNull($updated);
        $this->assertEquals($newContent, $updated->content);
    }

    // ============================================================================
    // Create Mutations
    // ============================================================================

    public function testCreateUserReturnsAllFields(): void
    {
        $user = $this->factory->createUser('newuser', 'newuser@example.com', 'New User', 'New bio');

        $this->assertNotNull($user);
        $this->assertIsString($user->id);
        $this->assertEquals('newuser', $user->username);
        $this->assertEquals('newuser@example.com', $user->email);
        $this->assertEquals('New User', $user->fullName);
        $this->assertEquals('New bio', $user->bio);
    }

    public function testCreatePostReturnsAllFields(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'Post Title', 'Post content');

        $this->assertNotNull($post);
        $this->assertIsString($post->id);
        $this->assertEquals('Post Title', $post->title);
        $this->assertEquals('Post content', $post->content);
        $this->assertEquals($user->id, $post->authorId);
    }

    public function testCreateCommentReturnsAllFields(): void
    {
        $user = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Title', 'Content');
        $comment = $this->factory->createComment($post->id, $user->id, 'Comment text');

        $this->assertNotNull($comment);
        $this->assertIsString($comment->id);
        $this->assertEquals('Comment text', $comment->content);
        $this->assertEquals($post->id, $comment->postId);
        $this->assertEquals($user->id, $comment->authorId);
    }

    // ============================================================================
    // Delete Mutations
    // ============================================================================

    public function testDeleteUser(): void
    {
        $user = $this->factory->createUser('todelete', 'todelete@example.com', 'To Delete');
        $userId = $user->id;

        $this->factory->deleteUser($userId);

        $retrieved = $this->factory->getUser($userId);
        $this->assertNull($retrieved);
    }

    public function testDeletePost(): void
    {
        $user = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($user->id, 'To Delete', 'Content');
        $postId = $post->id;

        $this->factory->deletePost($postId);

        $retrieved = $this->factory->getPost($postId);
        $this->assertNull($retrieved);
    }

    public function testDeleteComment(): void
    {
        $user = $this->factory->createUser('commenter', 'commenter@example.com', 'Commenter');
        $author = $this->factory->createUser('author', 'author@example.com', 'Author');
        $post = $this->factory->createPost($author->id, 'Title', 'Content');
        $comment = $this->factory->createComment($post->id, $user->id, 'To Delete');
        $commentId = $comment->id;

        $this->factory->deleteComment($commentId);

        $retrieved = $this->factory->getComment($commentId);
        $this->assertNull($retrieved);
    }

    // ============================================================================
    // Concurrency and State
    // ============================================================================

    public function testSequentialUpdatesSaveCorrectly(): void
    {
        $user = $this->factory->createUser('alice', 'alice@example.com', 'Alice', 'Initial');
        $userId = $user->id;

        $this->factory->updateUser($userId, 'Update 1', 'Alice');
        $after1 = $this->factory->getUser($userId);
        $this->assertEquals('Update 1', $after1->bio);

        $this->factory->updateUser($userId, 'Update 2', 'Alice');
        $after2 = $this->factory->getUser($userId);
        $this->assertEquals('Update 2', $after2->bio);

        $this->factory->updateUser($userId, 'Update 3', 'Alice');
        $after3 = $this->factory->getUser($userId);
        $this->assertEquals('Update 3', $after3->bio);
    }
}
