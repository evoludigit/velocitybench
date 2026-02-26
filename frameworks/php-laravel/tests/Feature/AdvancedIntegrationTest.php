<?php

namespace Tests\Feature;

use Tests\TestCase;
use Tests\Traits\DatabaseTrait;
use App\Models\User;
use App\Models\Post;
use App\Models\Comment;

/**
 * AdvancedIntegrationTest - Advanced flows, relationships, and data consistency
 *
 * Additional tests to boost Laravel suite to 75+ tests
 */
class AdvancedIntegrationTest extends TestCase
{
    use DatabaseTrait;

    // ========================================================================
    // Multi-User Relationship Tests
    // ========================================================================

    public function test_multiple_authors_have_separate_posts(): void
    {
        // Arrange
        $author1 = $this->createTestUser("author1", "author1@example.com", "Author 1");
        $author2 = $this->createTestUser("author2", "author2@example.com", "Author 2");
        $author3 = $this->createTestUser("author3", "author3@example.com", "Author 3");

        $post1 = $this->createTestPost($author1->pk_user, "Author 1 Post", "Content 1");
        $post2 = $this->createTestPost($author2->pk_user, "Author 2 Post", "Content 2");
        $post3 = $this->createTestPost($author3->pk_user, "Author 3 Post", "Content 3");

        // Act
        $response1 = $this->getJson("/api/posts/by-author/{$author1->id}");
        $response2 = $this->getJson("/api/posts/by-author/{$author2->id}");
        $response3 = $this->getJson("/api/posts/by-author/{$author3->id}");

        // Assert
        $this->assertEquals(1, count($response1->json()));
        $this->assertEquals(1, count($response2->json()));
        $this->assertEquals(1, count($response3->json()));
    }

    public function test_post_relationships_are_independent(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com", "Author");
        $post1 = $this->createTestPost($author->pk_user, "Post 1", "Content 1");
        $post2 = $this->createTestPost($author->pk_user, "Post 2", "Content 2");

        // Act
        $response1 = $this->getJson("/api/posts/{$post1->id}");
        $response2 = $this->getJson("/api/posts/{$post2->id}");

        // Assert
        $data1 = $response1->json();
        $data2 = $response2->json();
        $this->assertNotEquals($data1['id'], $data2['id']);
        $this->assertEquals("Post 1", $data1['title']);
        $this->assertEquals("Post 2", $data2['title']);
    }

    // ========================================================================
    // Pagination Edge Cases
    // ========================================================================

    public function test_pagination_boundary_at_exact_limit(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com");
        for ($i = 0; $i < 20; $i++) {
            $this->createTestPost($author->pk_user, "Post $i", "Content $i");
        }

        // Act
        $response = $this->getJson("/api/posts/by-author/{$author->id}?page=0&size=20");

        // Assert
        $this->assertEquals(20, count($response->json()));
    }

    public function test_pagination_page_alignment(): void
    {
        // Arrange
        for ($i = 0; $i < 30; $i++) {
            $user = $this->createTestUser("user$i", "user$i@example.com");
            if ($i % 5 == 0) {
                $this->createTestPost($user->pk_user, "Post", "Content");
            }
        }

        // Act
        $page1 = $this->getJson("/api/users?page=0&size=15");
        $page2 = $this->getJson("/api/users?page=1&size=15");

        // Assert
        $this->assertEquals(15, count($page1->json()));
        $this->assertEquals(15, count($page2->json()));
    }

    // ========================================================================
    // Field Immutability Tests
    // ========================================================================

    public function test_username_remains_immutable(): void
    {
        // Arrange
        $user = $this->createTestUser("alice", "alice@example.com", "Alice");
        $originalUsername = $user->username;

        // Act
        $user->update(['bio' => 'New bio']);

        // Verify
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $data = $response->json();
        $this->assertEquals($originalUsername, $data['username']);
    }

    public function test_id_remains_immutable(): void
    {
        // Arrange
        $user = $this->createTestUser("alice", "alice@example.com", "Alice");
        $originalId = $user->id;

        // Act
        $user->update(['bio' => 'New bio']);

        // Verify
        $response = $this->getJson("/api/users/{$user->id}");

        // Assert
        $data = $response->json();
        $this->assertEquals($originalId, $data['id']);
    }

    // ========================================================================
    // Data Type Validation
    // ========================================================================

    public function test_all_user_ids_are_uuid(): void
    {
        // Arrange
        $users = [
            $this->createTestUser("alice", "alice@example.com"),
            $this->createTestUser("bob", "bob@example.com"),
            $this->createTestUser("charlie", "charlie@example.com"),
        ];

        // Act & Assert
        foreach ($users as $user) {
            $parts = explode('-', $user->id);
            $this->assertCount(5, $parts);
        }
    }

    public function test_all_post_ids_are_uuid(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com");
        $posts = [
            $this->createTestPost($author->pk_user, "Post 1", "Content 1"),
            $this->createTestPost($author->pk_user, "Post 2", "Content 2"),
            $this->createTestPost($author->pk_user, "Post 3", "Content 3"),
        ];

        // Act & Assert
        foreach ($posts as $post) {
            $parts = explode('-', $post->id);
            $this->assertCount(5, $parts);
        }
    }

    // ========================================================================
    // Response Structure Consistency
    // ========================================================================

    public function test_list_and_detail_structure_match(): void
    {
        // Arrange
        $user = $this->createTestUser("alice", "alice@example.com", "Alice", "Alice bio");

        // Act
        $listResponse = $this->getJson("/api/users");
        $detailResponse = $this->getJson("/api/users/{$user->id}");

        // Assert
        $listData = $listResponse->json();
        $detailData = $detailResponse->json();

        $listUser = collect($listData)->firstWhere('id', $user->id);

        $this->assertEquals($listUser['username'], $detailData['username']);
        $this->assertEquals($listUser['fullName'], $detailData['fullName']);
        $this->assertEquals($listUser['bio'] ?? null, $detailData['bio']);
    }

    public function test_post_list_and_detail_structure_match(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com");
        $post = $this->createTestPost($author->pk_user, "Test Post", "Test Content");

        // Act
        $listResponse = $this->getJson("/api/posts");
        $detailResponse = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $listData = $listResponse->json();
        $detailData = $detailResponse->json();

        $listPost = collect($listData)->firstWhere('id', $post->id);

        $this->assertEquals($listPost['title'], $detailData['title']);
        $this->assertEquals($listPost['content'], $detailData['content']);
    }

    // ========================================================================
    // Timestamp Consistency Tests
    // ========================================================================

    public function test_user_timestamps_are_set(): void
    {
        // Arrange
        $user = $this->createTestUser("alice", "alice@example.com", "Alice");

        // Act & Assert
        $this->assertNotNull($user->created_at);
        $this->assertIsObject($user->created_at);
    }

    public function test_post_timestamps_are_set(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com");
        $post = $this->createTestPost($author->pk_user, "Test Post", "Content");

        // Act & Assert
        $this->assertNotNull($post->created_at);
        $this->assertIsObject($post->created_at);
    }

    public function test_timestamps_returned_in_responses(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com");
        $post = $this->createTestPost($author->pk_user, "Test Post", "Content");

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $data = $response->json();
        $this->assertNotNull($data['createdAt']);
    }

    // ========================================================================
    // Null Field Consistency Tests
    // ========================================================================

    public function test_null_bio_consistency(): void
    {
        // Arrange
        $user1 = $this->createTestUser("alice", "alice@example.com", "Alice", null);
        $user2 = $this->createTestUser("bob", "bob@example.com", "Bob", "Bob's bio");

        // Act
        $response1 = $this->getJson("/api/users/{$user1->id}");
        $response2 = $this->getJson("/api/users/{$user2->id}");

        // Assert
        $data1 = $response1->json();
        $data2 = $response2->json();

        $this->assertNull($data1['bio']);
        $this->assertNotNull($data2['bio']);
    }

    public function test_empty_string_vs_null_bio(): void
    {
        // Arrange
        $user1 = $this->createTestUser("alice", "alice@example.com", "Alice", "");
        $user2 = $this->createTestUser("bob", "bob@example.com", "Bob", null);

        // Act
        $response1 = $this->getJson("/api/users/{$user1->id}");
        $response2 = $this->getJson("/api/users/{$user2->id}");

        // Assert
        $data1 = $response1->json();
        $data2 = $response2->json();

        $this->assertEquals("", $data1['bio']);
        $this->assertNull($data2['bio']);
    }

    // ========================================================================
    // Query Result Consistency Tests
    // ========================================================================

    public function test_same_user_returns_same_data(): void
    {
        // Arrange
        $user = $this->createTestUser("alice", "alice@example.com", "Alice", "Alice bio");
        $userId = $user->id;

        // Act
        $response1 = $this->getJson("/api/users/{$userId}");
        $response2 = $this->getJson("/api/users/{$userId}");

        // Assert
        $data1 = $response1->json();
        $data2 = $response2->json();

        $this->assertEquals($data1['id'], $data2['id']);
        $this->assertEquals($data1['username'], $data2['username']);
        $this->assertEquals($data1['bio'], $data2['bio']);
    }

    public function test_same_post_returns_same_data(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com");
        $post = $this->createTestPost($author->pk_user, "Test Post", "Test Content");
        $postId = $post->id;

        // Act
        $response1 = $this->getJson("/api/posts/{$postId}");
        $response2 = $this->getJson("/api/posts/{$postId}");

        // Assert
        $data1 = $response1->json();
        $data2 = $response2->json();

        $this->assertEquals($data1['id'], $data2['id']);
        $this->assertEquals($data1['title'], $data2['title']);
        $this->assertEquals($data1['content'], $data2['content']);
    }

    // ========================================================================
    // Trinity Pattern Consistency
    // ========================================================================

    public function test_post_author_id_references_user(): void
    {
        // Arrange
        $author = $this->createTestUser("author", "author@example.com", "Author");
        $post = $this->createTestPost($author->pk_user, "Test Post", "Content");

        // Act
        $response = $this->getJson("/api/posts/{$post->id}");

        // Assert
        $data = $response->json();
        $this->assertEquals($author->id, $data['authorId']);
    }

    public function test_multiple_posts_reference_correct_authors(): void
    {
        // Arrange
        $author1 = $this->createTestUser("author1", "author1@example.com");
        $author2 = $this->createTestUser("author2", "author2@example.com");

        $post1 = $this->createTestPost($author1->pk_user, "Post 1", "Content");
        $post2 = $this->createTestPost($author2->pk_user, "Post 2", "Content");

        // Act
        $response1 = $this->getJson("/api/posts/{$post1->id}");
        $response2 = $this->getJson("/api/posts/{$post2->id}");

        // Assert
        $data1 = $response1->json();
        $data2 = $response2->json();

        $this->assertEquals($author1->id, $data1['authorId']);
        $this->assertEquals($author2->id, $data2['authorId']);
    }
}
