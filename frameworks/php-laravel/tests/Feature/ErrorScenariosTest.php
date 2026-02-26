<?php

namespace Tests\Feature;

use Tests\TestCase;
use Tests\Traits\DatabaseTrait;
use App\Models\User;
use Illuminate\Support\Str;

/**
 * ErrorScenariosTest - Tests error handling and edge cases
 *
 * Coverage includes:
 * - 404 Not Found errors
 * - Invalid input handling
 * - Null/optional field handling
 * - Unicode and special character handling
 * - Boundary conditions
 */
class ErrorScenariosTest extends TestCase
{
    use DatabaseTrait;

    // ========================================================================
    // 404 Not Found Tests
    // ========================================================================

    public function test_get_nonexistent_user_returns_404(): void
    {
        // Arrange
        $nonexistentId = Str::uuid();

        // Act
        $response = $this->getJson("/api/users/{$nonexistentId}");

        // Assert
        $response->assertStatus(404);
    }

    public function test_get_nonexistent_post_returns_404(): void
    {
        // Arrange
        $nonexistentId = Str::uuid();

        // Act
        $response = $this->getJson("/api/posts/{$nonexistentId}");

        // Assert
        $response->assertStatus(404);
    }

    public function test_get_posts_by_nonexistent_author_returns_empty(): void
    {
        // Arrange
        $nonexistentId = Str::uuid();

        // Act
        $response = $this->getJson("/api/posts/by-author/{$nonexistentId}");

        // Assert
        $response->assertStatus(404);
    }

    // ========================================================================
    // Invalid Input Tests
    // ========================================================================

    public function test_list_users_with_invalid_page_parameter(): void
    {
        // Arrange
        $this->createTestUser('alice', 'alice@example.com', 'Alice');

        // Act
        $response = $this->getJson('/api/users?page=invalid&size=10');

        // Assert - Should handle gracefully (0-value or ignore)
        $response->assertStatus(200);
    }

    public function test_list_users_with_zero_size(): void
    {
        // Arrange
        for ($i = 0; $i < 5; $i++) {
            $this->createTestUser("user{$i}", "user{$i}@example.com");
        }

        // Act
        $response = $this->getJson('/api/users?page=0&size=0');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(0, $data);
    }

    public function test_list_users_with_negative_page(): void
    {
        // Arrange
        $this->createTestUser('alice', 'alice@example.com', 'Alice');

        // Act
        $response = $this->getJson('/api/users?page=-1&size=10');

        // Assert
        $response->assertStatus(200);
    }

    // ========================================================================
    // Null/Optional Field Tests
    // ========================================================================

    public function test_user_without_bio_returns_null(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', null);

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertNull($data['bio']);
    }

    public function test_user_with_empty_bio_returns_empty_string(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', '');

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertSame('', $data['bio']);
    }

    // ========================================================================
    // Special Character Handling Tests
    // ========================================================================

    public function test_user_bio_with_special_characters(): void
    {
        // Arrange
        $specialBio = "Bio with 'quotes' and \"double quotes\" and <html>";
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', $specialBio);

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['bio' => $specialBio]);
    }

    public function test_user_with_emoji_in_bio(): void
    {
        // Arrange
        $emojiBio = "Bio with emoji 🎉 and 💚";
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', $emojiBio);

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['bio' => $emojiBio]);
    }

    public function test_user_with_unicode_characters(): void
    {
        // Arrange
        $unicodeName = "Àlice Müller";
        $user = $this->createTestUser('alice', 'alice@example.com', $unicodeName);

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['fullName' => $unicodeName]);
    }

    public function test_post_content_with_special_characters(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $specialContent = "Content with 'quotes' and \"double quotes\" and <html>";
        $post = $this->createTestPost($author->pk_user, 'Special Post', $specialContent);

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['content' => $specialContent]);
    }

    public function test_post_content_with_emoji(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $emojiContent = "Content with emoji 🚀 and ✨";
        $post = $this->createTestPost($author->pk_user, 'Emoji Post', $emojiContent);

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['content' => $emojiContent]);
    }

    // ========================================================================
    // Boundary Condition Tests
    // ========================================================================

    public function test_very_long_bio_text(): void
    {
        // Arrange
        $longBio = str_repeat('x', 5000);
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', $longBio);

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertEquals(5000, strlen($data['bio']));
    }

    public function test_very_long_post_content(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $longContent = str_repeat('x', 5000);
        $post = $this->createTestPost($author->pk_user, 'Long Post', $longContent);

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertEquals(5000, strlen($data['content']));
    }

    public function test_list_users_with_large_limit(): void
    {
        // Arrange
        for ($i = 0; $i < 10; $i++) {
            $this->createTestUser("user{$i}", "user{$i}@example.com");
        }

        // Act
        $response = $this->getJson('/api/users?page=0&size=1000');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(10, $data);
    }

    public function test_multiple_users_have_unique_ids(): void
    {
        // Arrange
        $user1 = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $user2 = $this->createTestUser('bob', 'bob@example.com', 'Bob');
        $user3 = $this->createTestUser('charlie', 'charlie@example.com', 'Charlie');

        // Act
        $ids = [$user1->id, $user2->id, $user3->id];

        // Assert
        $this->assertCount(3, $ids);
        $this->assertCount(3, array_unique($ids));
    }
}
