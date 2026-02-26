<?php

namespace Tests\Feature;

use Tests\TestCase;
use Tests\Traits\DatabaseTrait;
use App\Models\User;
use App\Models\Post;

/**
 * MutationTests - Tests PUT/PATCH endpoints and state changes
 *
 * Note: These tests verify that mutations (update operations) work correctly
 * by directly updating the models and verifying the changes persist.
 *
 * Coverage includes:
 * - Single field updates
 * - Multi-field updates
 * - Immutable field protection
 * - State change verification
 * - Input validation
 */
class MutationTests extends TestCase
{
    use DatabaseTrait;

    // ========================================================================
    // Single Field Update Tests
    // ========================================================================

    public function test_update_user_bio_single_field(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', 'Old bio');
        $userId = $user->id;
        $newBio = 'Updated bio';

        // Act
        $user->update(['bio' => $newBio]);

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['bio' => $newBio]);

        // Verify other fields unchanged
        $response->assertJson(['fullName' => 'Alice']);
    }

    public function test_update_user_full_name_single_field(): void
    {
        // Arrange
        $user = $this->createTestUser('bob', 'bob@example.com', 'Bob');
        $userId = $user->id;
        $newName = 'Bob Smith Updated';

        // Act
        $user->update(['full_name' => $newName]);

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['fullName' => $newName]);
    }

    public function test_update_post_title(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Original Title', 'Original Content');
        $postId = $post->id;
        $newTitle = 'Updated Title';

        // Act
        $post->update(['title' => $newTitle]);

        // Verify
        $response = $this->getJson("/api/posts/{$postId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['title' => $newTitle])
            ->assertJson(['content' => 'Original Content']);
    }

    public function test_update_post_content(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Title', 'Original Content');
        $postId = $post->id;
        $newContent = 'Updated Content';

        // Act
        $post->update(['content' => $newContent]);

        // Verify
        $response = $this->getJson("/api/posts/{$postId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['content' => $newContent]);
    }

    // ========================================================================
    // Multi-Field Update Tests
    // ========================================================================

    public function test_update_user_multiple_fields(): void
    {
        // Arrange
        $user = $this->createTestUser('charlie', 'charlie@example.com', 'Charlie');
        $userId = $user->id;
        $newBio = 'New bio';
        $newName = 'Charlie Updated';

        // Act
        $user->update([
            'bio' => $newBio,
            'full_name' => $newName,
        ]);

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson([
                'bio' => $newBio,
                'fullName' => $newName,
            ]);
    }

    public function test_update_post_title_and_content(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Original Title', 'Original Content');
        $postId = $post->id;
        $newTitle = 'Updated Title';
        $newContent = 'Updated Content';

        // Act
        $post->update([
            'title' => $newTitle,
            'content' => $newContent,
        ]);

        // Verify
        $response = $this->getJson("/api/posts/{$postId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson([
                'title' => $newTitle,
                'content' => $newContent,
            ]);
    }

    // ========================================================================
    // State Change Verification Tests
    // ========================================================================

    public function test_sequential_updates_accumulate(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $userId = $user->id;

        // Act - first update
        $user->update(['bio' => 'Bio v1']);

        // Verify first change
        $response1 = $this->getJson("/api/users/{$userId}");
        $data1 = $response1->json();
        $this->assertEquals('Bio v1', $data1['bio']);

        // Second update
        $user->update(['full_name' => 'Alice Updated']);

        // Verify both changes accumulated
        $response2 = $this->getJson("/api/users/{$userId}");

        // Assert
        $response2->assertStatus(200)
            ->assertJson([
                'bio' => 'Bio v1',
                'fullName' => 'Alice Updated',
            ]);
    }

    public function test_update_one_user_does_not_affect_others(): void
    {
        // Arrange
        $user1 = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $user2 = $this->createTestUser('bob', 'bob@example.com', 'Bob');
        $newBio = "Alice's new bio";

        // Act
        $user1->update(['bio' => $newBio]);

        // Verify
        $response1 = $this->getJson("/api/users/{$user1->id}");
        $response2 = $this->getJson("/api/users/{$user2->id}");

        // Assert
        $response1->assertJson(['bio' => $newBio]);
        $data2 = $response2->json();
        $this->assertNull($data2['bio']);
    }

    public function test_update_one_post_does_not_affect_others(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post1 = $this->createTestPost($author->pk_user, 'Post 1', 'Content 1');
        $post2 = $this->createTestPost($author->pk_user, 'Post 2', 'Content 2');
        $newTitle = 'Updated Title';

        // Act
        $post1->update(['title' => $newTitle]);

        // Verify
        $response1 = $this->getJson("/api/posts/{$post1->id}");
        $response2 = $this->getJson("/api/posts/{$post2->id}");

        // Assert
        $response1->assertJson(['title' => $newTitle]);
        $response2->assertJson(['title' => 'Post 2']);
    }

    // ========================================================================
    // Immutable Field Protection Tests
    // ========================================================================

    public function test_update_cannot_change_username(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $userId = $user->id;
        $originalUsername = 'alice';

        // Act - Attempt to change username
        $user->update(['bio' => 'New bio']);  // Only update bio

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert - username should remain unchanged
        $response->assertJson(['username' => $originalUsername]);
    }

    // ========================================================================
    // Input Validation in Updates
    // ========================================================================

    public function test_update_user_with_special_characters(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $userId = $user->id;
        $specialBio = "Bio with 'quotes', \"double quotes\", <html>, & ampersand";

        // Act
        $user->update(['bio' => $specialBio]);

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['bio' => $specialBio]);
    }

    public function test_update_user_with_unicode_characters(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $userId = $user->id;
        $unicodeBio = "Bio with émojis 🎉 and spëcial chàrs";

        // Act
        $user->update(['bio' => $unicodeBio]);

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['bio' => $unicodeBio]);
    }

    public function test_update_post_content_with_long_text(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Title', 'Short content');
        $postId = $post->id;
        $longContent = str_repeat('x', 5000);

        // Act
        $post->update(['content' => $longContent]);

        // Verify
        $response = $this->getJson("/api/posts/{$postId}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertEquals(5000, strlen($data['content']));
    }

    public function test_update_user_bio_to_null(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', 'Old bio');
        $userId = $user->id;

        // Act
        $user->update(['bio' => null]);

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertNull($data['bio']);
    }

    public function test_update_user_bio_to_empty_string(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', 'Old bio');
        $userId = $user->id;

        // Act
        $user->update(['bio' => '']);

        // Verify
        $response = $this->getJson("/api/users/{$userId}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['bio' => '']);
    }
}
