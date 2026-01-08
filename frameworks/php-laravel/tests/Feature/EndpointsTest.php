<?php

namespace Tests\Feature;

use Tests\TestCase;
use Tests\Traits\DatabaseTrait;
use App\Models\User;
use App\Models\Post;

/**
 * EndpointsTest - Tests GET /users and GET /posts endpoints
 *
 * Coverage includes:
 * - List endpoints with pagination
 * - Detail endpoints
 * - Relationship includes
 * - Nested relationships
 */
class EndpointsTest extends TestCase
{
    use DatabaseTrait;

    // ========================================================================
    // GET /users Tests
    // ========================================================================

    public function test_list_users_returns_list(): void
    {
        // Arrange
        $alice = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $bob = $this->createTestUser('bob', 'bob@example.com', 'Bob');

        // Act
        $response = $this->getJson('/api/users');

        // Assert
        $response->assertStatus(200)
            ->assertIsArray();

        $data = $response->json();
        $this->assertCount(2, $data);
    }

    public function test_list_users_pagination_default_limit(): void
    {
        // Arrange - Create 20 users
        for ($i = 0; $i < 20; $i++) {
            $this->createTestUser("user{$i}", "user{$i}@example.com");
        }

        // Act
        $response = $this->getJson('/api/users?page=0&size=10');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(10, $data);
    }

    public function test_list_users_custom_limit(): void
    {
        // Arrange
        for ($i = 0; $i < 15; $i++) {
            $this->createTestUser("user{$i}", "user{$i}@example.com");
        }

        // Act
        $response = $this->getJson('/api/users?page=0&size=5');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(5, $data);
    }

    public function test_list_users_pagination_second_page(): void
    {
        // Arrange
        for ($i = 0; $i < 20; $i++) {
            $this->createTestUser("user{$i}", "user{$i}@example.com");
        }

        // Act
        $response = $this->getJson('/api/users?page=1&size=10');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(10, $data);
    }

    public function test_get_user_by_id(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson([
                'id' => $user->id,
                'username' => 'alice',
                'fullName' => 'Alice',
            ]);
    }

    public function test_get_user_includes_optional_bio(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', 'Alice bio');

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson(['bio' => 'Alice bio']);
    }

    public function test_get_user_bio_null_when_not_provided(): void
    {
        // Arrange
        $user = $this->createTestUser('bob', 'bob@example.com', 'Bob');

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertNull($data['bio']);
    }

    // ========================================================================
    // GET /posts Tests
    // ========================================================================

    public function test_list_posts_returns_list(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post1 = $this->createTestPost($author->pk_user, 'Post 1', 'Content 1');
        $post2 = $this->createTestPost($author->pk_user, 'Post 2', 'Content 2');

        // Act
        $response = $this->getJson('/api/posts');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(2, $data);
    }

    public function test_list_posts_pagination(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        for ($i = 0; $i < 15; $i++) {
            $this->createTestPost($author->pk_user, "Post {$i}", "Content {$i}");
        }

        // Act
        $response = $this->getJson('/api/posts?page=0&size=10');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(10, $data);
    }

    public function test_list_posts_includes_author_id(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');

        // Act
        $response = $this->getJson('/api/posts');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertNotEmpty($data);
        $this->assertArrayHasKey('authorId', $data[0]);
    }

    public function test_get_post_by_id(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Test Content');

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJson([
                'id' => $post->id,
                'title' => 'Test Post',
                'content' => 'Test Content',
            ]);
    }

    public function test_get_post_includes_created_at(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertArrayHasKey('createdAt', $data);
        $this->assertNotNull($data['createdAt']);
    }

    public function test_get_post_by_author_returns_author_posts(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $other = $this->createTestUser('other', 'other@example.com', 'Other');

        $post1 = $this->createTestPost($author->pk_user, 'Author Post 1', 'Content 1');
        $post2 = $this->createTestPost($author->pk_user, 'Author Post 2', 'Content 2');
        $post3 = $this->createTestPost($other->pk_user, 'Other Post', 'Content 3');

        // Act
        $response = $this->getJson("/api/posts/by-author/{$author->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(2, $data);
    }

    public function test_get_posts_by_author_returns_empty_for_no_posts(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $other = $this->createTestUser('other', 'other@example.com', 'Other');

        $this->createTestPost($other->pk_user, 'Other Post', 'Content');

        // Act
        $response = $this->getJson("/api/posts/by-author/{$author->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(0, $data);
    }
}
