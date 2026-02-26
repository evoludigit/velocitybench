<?php
declare(strict_types=1);

namespace VelocityBench\Model;

use VelocityBench\Database\Connection;
use PDO;

class Post
{
    public int $pk_post;
    public string $id;
    public int $fk_author;
    public string $title;
    public ?string $content;
    public string $created_at;
    public ?string $updated_at;

    public static function fromRow(array $row): self
    {
        $post = new self();
        $post->pk_post = (int)$row['pk_post'];
        $post->id = $row['id'];
        $post->fk_author = (int)$row['fk_author'];
        $post->title = $row['title'];
        $post->content = $row['content'];
        $post->created_at = $row['created_at'];
        $post->updated_at = $row['updated_at'] ?? null;
        return $post;
    }

    public static function findById(string $id): ?self
    {
        $pdo = Connection::get();
        $stmt = $pdo->prepare('SELECT * FROM tb_post WHERE id = :id');
        $stmt->execute(['id' => $id]);
        $row = $stmt->fetch();
        return $row ? self::fromRow($row) : null;
    }

    public static function findByPk(int $pk): ?self
    {
        $pdo = Connection::get();
        $stmt = $pdo->prepare('SELECT * FROM tb_post WHERE pk_post = :pk');
        $stmt->execute(['pk' => $pk]);
        $row = $stmt->fetch();
        return $row ? self::fromRow($row) : null;
    }

    /**
     * @param int[] $pks
     * @return array<int, Post>
     */
    public static function findByPks(array $pks): array
    {
        if (empty($pks)) {
            return [];
        }

        $pdo = Connection::get();
        $placeholders = implode(',', array_fill(0, count($pks), '?'));
        $stmt = $pdo->prepare("SELECT * FROM tb_post WHERE pk_post IN ({$placeholders})");
        $stmt->execute($pks);

        $posts = [];
        while ($row = $stmt->fetch()) {
            $post = self::fromRow($row);
            $posts[$post->pk_post] = $post;
        }
        return $posts;
    }

    /**
     * @param int[] $authorPks
     * @param int $limit
     * @return array<int, Post[]>
     */
    public static function findByAuthorPks(array $authorPks, int $limit = 50): array
    {
        if (empty($authorPks)) {
            return [];
        }

        $pdo = Connection::get();
        $placeholders = implode(',', array_fill(0, count($authorPks), '?'));
        $sql = "
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY fk_author ORDER BY pk_post) as rn
                FROM tb_post
                WHERE fk_author IN ({$placeholders})
            ) t WHERE rn <= ?
            ORDER BY fk_author, pk_post
        ";
        $stmt = $pdo->prepare($sql);
        $stmt->execute([...$authorPks, $limit]);

        $postsByAuthor = array_fill_keys($authorPks, []);
        while ($row = $stmt->fetch()) {
            $post = self::fromRow($row);
            $postsByAuthor[$post->fk_author][] = $post;
        }
        return $postsByAuthor;
    }

    /**
     * @return Post[]
     */
    public static function all(int $limit = 10): array
    {
        $pdo = Connection::get();
        $stmt = $pdo->prepare('SELECT * FROM tb_post ORDER BY pk_post LIMIT :limit');
        $stmt->bindValue('limit', min($limit, 100), PDO::PARAM_INT);
        $stmt->execute();

        $posts = [];
        while ($row = $stmt->fetch()) {
            $posts[] = self::fromRow($row);
        }
        return $posts;
    }

    public static function update(string $id, array $data): ?self
    {
        $pdo = Connection::get();

        $sets = [];
        $params = ['id' => $id];

        if (isset($data['title'])) {
            $sets[] = 'title = :title';
            $params['title'] = $data['title'];
        }
        if (isset($data['content'])) {
            $sets[] = 'content = :content';
            $params['content'] = $data['content'];
        }

        if (empty($sets)) {
            return self::findById($id);
        }

        $sets[] = 'updated_at = NOW()';
        $sql = 'UPDATE tb_post SET ' . implode(', ', $sets) . ' WHERE id = :id';
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);

        return self::findById($id);
    }
}
