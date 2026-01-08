<?php

namespace Tests\Traits;

use App\Models\User;
use App\Models\Post;
use App\Models\Comment;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;

/**
 * DatabaseTrait - Provides factory methods for test data creation
 *
 * Follows the Trinity Identifier Pattern:
 * - pk_{entity}: Internal INTEGER primary key for database joins
 * - id: UUID for public API access
 * - identifier: TEXT slug for human-readable access (future)
 */
trait DatabaseTrait
{
    use RefreshDatabase, WithFaker;

    /**
     * Create a test user with flexible parameters.
     *
     * @param string $username Username (required)
     * @param string|null $email Email address (optional, defaults to username@example.com)
     * @param string|null $fullName Full name (optional, defaults to capitalized username)
     * @param string|null $bio Bio text (optional)
     * @return User Created user instance
     */
    protected function createTestUser(
        string $username,
        ?string $email = null,
        ?string $fullName = null,
        ?string $bio = null
    ): User {
        // Default values
        if ($email === null) {
            $email = $username . '@example.com';
        }
        if ($fullName === null) {
            $fullName = ucfirst($username);
        }

        return User::create([
            'username' => $username,
            'email' => $email,
            'full_name' => $fullName,
            'bio' => $bio,
        ]);
    }

    /**
     * Create a test post with flexible parameters.
     *
     * @param int $authorId Author's pk_user (internal primary key)
     * @param string $title Post title
     * @param string|null $content Post content (optional)
     * @return Post Created post instance
     */
    protected function createTestPost(
        int $authorId,
        string $title,
        ?string $content = null
    ): Post {
        if ($content === null) {
            $content = "Test content for {$title}";
        }

        return Post::create([
            'fk_author' => $authorId,
            'title' => $title,
            'content' => $content,
        ]);
    }

    /**
     * Create a test comment with flexible parameters.
     *
     * @param int $postId Post's pk_post (internal primary key)
     * @param int $authorId Author's pk_user (internal primary key)
     * @param string|null $content Comment content (optional)
     * @return Comment Created comment instance
     */
    protected function createTestComment(
        int $postId,
        int $authorId,
        ?string $content = null
    ): Comment {
        if ($content === null) {
            $content = "Test comment";
        }

        return Comment::create([
            'fk_post' => $postId,
            'fk_author' => $authorId,
            'content' => $content,
        ]);
    }
}
