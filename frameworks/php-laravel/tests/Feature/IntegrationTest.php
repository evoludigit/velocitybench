<?php

namespace Tests\Feature;

use Tests\TestCase;
use Tests\Traits\DatabaseTrait;
use App\Models\User;
use App\Models\Post;

/**
 * IntegrationTest - Tests complex flows and deeply nested relationships
 *
 * Coverage includes:
 * - Multiple related entity queries
 * - Pagination with relationships
 * - Trinity pattern validation
 * - Data consistency across operations
 */
class IntegrationTest extends TestCase
{
    use DatabaseTrait;

    // ========================================================================
    // User-Post Relationship Tests
    // ========================================================================

    public function test_get_posts_by_specific_author(): void
    {
        // Arrange
        $author1 = $this->createTestUser('author1', 'author1@example.com', 'Author 1');
        $author2 = $this->createTestUser('author2', 'author2@example.com', 'Author 2');

        $post1 = $this->createTestPost($author1->pk_user, 'Post 1', 'Content 1');
        $post2 = $this->createTestPost($author1->pk_user, 'Post 2', 'Content 2');
        $post3 = $this->createTestPost($author2->pk_user, 'Post 3', 'Content 3');

        // Act
        $response = $this->getJson("/api/posts/by-author/{$author1->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(2, $data);
        $this->assertEquals('Post 1', $data[0]['title']);
        $this->assertEquals('Post 2', $data[1]['title']);
    }

    public function test_author_posts_pagination(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');

        for ($i = 0; $i < 15; $i++) {
            $this->createTestPost($author->pk_user, "Post {$i}", "Content {$i}");
        }

        // Act
        $response = $this->getJson("/api/posts/by-author/{$author->id}?page=0&size=10");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertCount(10, $data);
    }

    public function test_author_with_no_posts_returns_empty_list(): void
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

    // ========================================================================
    // Trinity Pattern Validation Tests
    // ========================================================================

    public function test_user_has_uuid_id(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();

        // Verify UUID format (8-4-4-4-12)
        $uuidParts = explode('-', $data['id']);
        $this->assertCount(5, $uuidParts);
    }

    public function test_post_has_uuid_id(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();

        // Verify UUID format
        $uuidParts = explode('-', $data['id']);
        $this->assertCount(5, $uuidParts);
    }

    public function test_post_author_id_is_user_uuid(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();

        // Author ID in post should match user's UUID
        $this->assertEquals($author->id, $data['authorId']);
    }

    // ========================================================================
    // Data Consistency Tests
    // ========================================================================

    public function test_list_users_returns_consistent_data(): void
    {
        // Arrange
        $user1 = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $user2 = $this->createTestUser('bob', 'bob@example.com', 'Bob');

        // Act
        $listResponse = $this->getJson('/api/users');
        $getResponse = $this->getJson("/api/users/{$user1->id}");

        // Assert
        $listData = $listResponse->json();
        $getData = $getResponse->json();

        // Data from list and detail should match
        $listUser = collect($listData)->firstWhere('id', $user1->id);
        $this->assertEquals($listUser['username'], $getData['username']);
        $this->assertEquals($listUser['fullName'], $getData['fullName']);
    }

    public function test_list_posts_returns_consistent_data(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Test Content');

        // Act
        $listResponse = $this->getJson('/api/posts');
        $getResponse = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $listData = $listResponse->json();
        $getData = $getResponse->json();

        $listPost = collect($listData)->firstWhere('id', $post->id);
        $this->assertEquals($listPost['title'], $getData['title']);
        $this->assertEquals($listPost['content'], $getData['content']);
    }

    public function test_post_author_relationship_integrity(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post1 = $this->createTestPost($author->pk_user, 'Post 1', 'Content 1');
        $post2 = $this->createTestPost($author->pk_user, 'Post 2', 'Content 2');

        // Act
        $postsResponse = $this->getJson('/api/posts');

        // Assert
        $posts = $postsResponse->json();

        $authorPosts = array_filter($posts, fn($p) => $p['authorId'] === $author->id);
        $this->assertCount(2, $authorPosts);
    }

    // ========================================================================
    // Response Structure Tests
    // ========================================================================

    public function test_users_list_response_structure(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', 'Alice bio');

        // Act
        $response = $this->getJson('/api/users');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertNotEmpty($data);

        $user = $data[0];
        $this->assertArrayHasKey('id', $user);
        $this->assertArrayHasKey('username', $user);
        $this->assertArrayHasKey('fullName', $user);
    }

    public function test_user_detail_response_structure(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice', 'Alice bio');

        // Act
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJsonStructure([
                'id',
                'username',
                'fullName',
                'bio',
            ]);
    }

    public function test_posts_list_response_structure(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Test Content');

        // Act
        $response = $this->getJson('/api/posts');

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertNotEmpty($data);

        $this->assertArrayHasKey('id', $data[0]);
        $this->assertArrayHasKey('title', $data[0]);
        $this->assertArrayHasKey('content', $data[0]);
        $this->assertArrayHasKey('authorId', $data[0]);
        $this->assertArrayHasKey('createdAt', $data[0]);
    }

    public function test_post_detail_response_structure(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Test Content');

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200)
            ->assertJsonStructure([
                'id',
                'title',
                'content',
                'authorId',
                'createdAt',
            ]);
    }

    // ========================================================================
    // Timestamp Tests
    // ========================================================================

    public function test_user_created_at_timestamp_set(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');

        // Act & Assert
        $this->assertNotNull($user->created_at);
    }

    public function test_post_created_at_timestamp_set(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');

        // Act & Assert
        $this->assertNotNull($post->created_at);
    }

    public function test_post_created_at_returned_in_response(): void
    {
        // Arrange
        $author = $this->createTestUser('author', 'author@example.com', 'Author');
        $post = $this->createTestPost($author->pk_user, 'Test Post', 'Content');

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $response->assertStatus(200);
        $data = $response->json();
        $this->assertNotNull($data['createdAt']);
    }
}
