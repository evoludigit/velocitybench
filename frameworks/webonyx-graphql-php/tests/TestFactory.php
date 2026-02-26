<?php

declare(strict_types=1);

namespace VelocityBench\Tests;

use DateTime;
use DateTimeImmutable;
use Ramsey\Uuid\Uuid;

/**
 * Test data structures
 */
class TestUser
{
    public string $id;
    public int $pkUser;
    public string $username;
    public string $email;
    public string $fullName;
    public ?string $bio;
    public DateTimeImmutable $createdAt;
    public DateTimeImmutable $updatedAt;

    public function __construct(
        string $id,
        int $pkUser,
        string $username,
        string $email,
        string $fullName,
        ?string $bio = null
    ) {
        $this->id = $id;
        $this->pkUser = $pkUser;
        $this->username = $username;
        $this->email = $email;
        $this->fullName = $fullName;
        $this->bio = $bio;
        $this->createdAt = new DateTimeImmutable();
        $this->updatedAt = new DateTimeImmutable();
    }
}

class TestPost
{
    public string $id;
    public int $pkPost;
    public int $fkAuthor;
    public string $authorId;
    public string $title;
    public string $content;
    public DateTimeImmutable $createdAt;
    public DateTimeImmutable $updatedAt;
    public ?TestUser $author;

    public function __construct(
        string $id,
        int $pkPost,
        int $fkAuthor,
        string $authorId,
        string $title,
        string $content,
        ?TestUser $author = null
    ) {
        $this->id = $id;
        $this->pkPost = $pkPost;
        $this->fkAuthor = $fkAuthor;
        $this->authorId = $authorId;
        $this->title = $title;
        $this->content = $content;
        $this->author = $author;
        $this->createdAt = new DateTimeImmutable();
        $this->updatedAt = new DateTimeImmutable();
    }
}

class TestComment
{
    public string $id;
    public int $pkComment;
    public int $fkPost;
    public int $fkAuthor;
    public string $postId;
    public string $authorId;
    public string $content;
    public DateTimeImmutable $createdAt;
    public ?TestUser $author;
    public ?TestPost $post;

    public function __construct(
        string $id,
        int $pkComment,
        int $fkPost,
        int $fkAuthor,
        string $postId,
        string $authorId,
        string $content,
        ?TestUser $author = null,
        ?TestPost $post = null
    ) {
        $this->id = $id;
        $this->pkComment = $pkComment;
        $this->fkPost = $fkPost;
        $this->fkAuthor = $fkAuthor;
        $this->postId = $postId;
        $this->authorId = $authorId;
        $this->content = $content;
        $this->author = $author;
        $this->post = $post;
        $this->createdAt = new DateTimeImmutable();
    }
}

/**
 * In-memory test factory for isolated tests
 */
class TestFactory
{
    /** @var array<string, TestUser> */
    private array $users = [];

    /** @var array<string, TestPost> */
    private array $posts = [];

    /** @var array<string, TestComment> */
    private array $comments = [];

    private int $userCounter = 0;
    private int $postCounter = 0;
    private int $commentCounter = 0;

    public function createUser(
        string $username,
        string $email,
        string $fullName = 'Test User',
        ?string $bio = null
    ): TestUser {
        if (empty($username)) {
            throw new \InvalidArgumentException('Username cannot be empty');
        }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new \InvalidArgumentException("Invalid email address: {$email}");
        }
        if (strlen($fullName) > 255) {
            throw new \InvalidArgumentException('Full name exceeds 255 character limit');
        }
        if ($bio !== null && strlen($bio) > 1000) {
            throw new \InvalidArgumentException('Bio exceeds 1000 character limit');
        }
        foreach ($this->users as $existing) {
            if ($existing->username === $username) {
                throw new \RuntimeException("Username already taken: {$username}");
            }
            if (isset($existing->email) && $existing->email === $email) {
                throw new \RuntimeException("Email already in use: {$email}");
            }
        }

        $this->userCounter++;
        $user = new TestUser(
            Uuid::uuid4()->toString(),
            $this->userCounter,
            $username,
            $email,
            $fullName,
            $bio
        );
        $this->users[$user->id] = $user;
        return $user;
    }

    public function createPost(
        string $authorId,
        string $title,
        string $content = 'Default content'
    ): TestPost {
        $author = $this->users[$authorId] ?? null;
        if ($author === null) {
            throw new \RuntimeException("Author not found: {$authorId}");
        }
        if (empty($title)) {
            throw new \InvalidArgumentException('Title cannot be empty');
        }
        if (strlen($title) > 255) {
            throw new \InvalidArgumentException('Title exceeds 255 character limit');
        }

        $this->postCounter++;
        $post = new TestPost(
            Uuid::uuid4()->toString(),
            $this->postCounter,
            $author->pkUser,
            $author->id,
            $title,
            $content,
            $author
        );
        $this->posts[$post->id] = $post;
        return $post;
    }

    public function createComment(
        string $postId,
        string $authorId,
        string $content
    ): TestComment {
        $author = $this->users[$authorId] ?? null;
        $post = $this->posts[$postId] ?? null;

        if ($author === null) {
            throw new \RuntimeException("Author not found");
        }
        if ($post === null) {
            throw new \RuntimeException("Post not found");
        }
        if (empty($content)) {
            throw new \InvalidArgumentException('Comment content cannot be empty');
        }

        $this->commentCounter++;
        $comment = new TestComment(
            Uuid::uuid4()->toString(),
            $this->commentCounter,
            $post->pkPost,
            $author->pkUser,
            $post->id,
            $author->id,
            $content,
            $author,
            $post
        );
        $this->comments[$comment->id] = $comment;
        return $comment;
    }

    public function getUser(string $id): ?TestUser
    {
        return $this->users[$id] ?? null;
    }

    public function getPost(string $id): ?TestPost
    {
        return $this->posts[$id] ?? null;
    }

    public function getComment(string $id): ?TestComment
    {
        return $this->comments[$id] ?? null;
    }

    /**
     * @return TestUser[]
     */
    public function getAllUsers(): array
    {
        return array_values($this->users);
    }

    /**
     * @return TestPost[]
     */
    public function getPostsByAuthor(int $authorPk): array
    {
        return array_values(array_filter(
            $this->posts,
            fn(TestPost $p) => $p->fkAuthor === $authorPk
        ));
    }

    /**
     * @return TestComment[]
     */
    public function getCommentsByPost(int $postPk): array
    {
        return array_values(array_filter(
            $this->comments,
            fn(TestComment $c) => $c->fkPost === $postPk
        ));
    }

    /**
     * @return TestPost[]
     */
    public function getAllPosts(): array
    {
        return array_values($this->posts);
    }

    public function updateUser(string $id, ?string $bio, string $fullName = 'Test User'): ?TestUser
    {
        if (!isset($this->users[$id])) {
            return null;
        }
        $this->users[$id]->bio = $bio;
        $this->users[$id]->fullName = $fullName;
        $this->users[$id]->updatedAt = new DateTimeImmutable();
        return $this->users[$id];
    }

    public function updatePost(string $id, string $title, string $content): ?TestPost
    {
        if (!isset($this->posts[$id])) {
            return null;
        }
        $this->posts[$id]->title = $title;
        $this->posts[$id]->content = $content;
        $this->posts[$id]->updatedAt = new DateTimeImmutable();
        return $this->posts[$id];
    }

    public function deleteUser(string $id): void
    {
        unset($this->users[$id]);
    }

    public function deletePost(string $id): void
    {
        unset($this->posts[$id]);
    }

    public function reset(): void
    {
        $this->users = [];
        $this->posts = [];
        $this->comments = [];
        $this->userCounter = 0;
        $this->postCounter = 0;
        $this->commentCounter = 0;
    }
}

class ValidationHelper
{
    private const UUID_REGEX = '/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i';

    public static function isValidUuid(string $value): bool
    {
        return preg_match(self::UUID_REGEX, $value) === 1;
    }
}

class DataGenerator
{
    public static function generateLongString(int $length): string
    {
        return str_repeat('x', $length);
    }

    public static function generateRandomUsername(): string
    {
        return 'user_' . bin2hex(random_bytes(4));
    }
}
