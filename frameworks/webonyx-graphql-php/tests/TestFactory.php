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
    public string $fullName;
    public ?string $bio;
    public DateTimeImmutable $createdAt;
    public DateTimeImmutable $updatedAt;

    public function __construct(
        string $id,
        int $pkUser,
        string $username,
        string $fullName,
        ?string $bio = null
    ) {
        $this->id = $id;
        $this->pkUser = $pkUser;
        $this->username = $username;
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
    public string $title;
    public string $content;
    public DateTimeImmutable $createdAt;
    public DateTimeImmutable $updatedAt;
    public ?TestUser $author;

    public function __construct(
        string $id,
        int $pkPost,
        int $fkAuthor,
        string $title,
        string $content,
        ?TestUser $author = null
    ) {
        $this->id = $id;
        $this->pkPost = $pkPost;
        $this->fkAuthor = $fkAuthor;
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
    public string $content;
    public DateTimeImmutable $createdAt;
    public ?TestUser $author;
    public ?TestPost $post;

    public function __construct(
        string $id,
        int $pkComment,
        int $fkPost,
        int $fkAuthor,
        string $content,
        ?TestUser $author = null,
        ?TestPost $post = null
    ) {
        $this->id = $id;
        $this->pkComment = $pkComment;
        $this->fkPost = $fkPost;
        $this->fkAuthor = $fkAuthor;
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
        string $fullName,
        ?string $bio = null
    ): TestUser {
        $this->userCounter++;
        $user = new TestUser(
            Uuid::uuid4()->toString(),
            $this->userCounter,
            $username,
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

        $this->postCounter++;
        $post = new TestPost(
            Uuid::uuid4()->toString(),
            $this->postCounter,
            $author->pkUser,
            $title,
            $content,
            $author
        );
        $this->posts[$post->id] = $post;
        return $post;
    }

    public function createComment(
        string $authorId,
        string $postId,
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

        $this->commentCounter++;
        $comment = new TestComment(
            Uuid::uuid4()->toString(),
            $this->commentCounter,
            $post->pkPost,
            $author->pkUser,
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
