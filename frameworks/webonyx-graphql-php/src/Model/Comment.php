<?php
declare(strict_types=1);

namespace VelocityBench\Model;

use VelocityBench\Database\Connection;
use PDO;

class Comment
{
    public int $pk_comment;
    public string $id;
    public int $fk_post;
    public int $fk_author;
    public string $content;
    public string $created_at;
    public ?string $updated_at;

    public static function fromRow(array $row): self
    {
        $comment = new self();
        $comment->pk_comment = (int)$row['pk_comment'];
        $comment->id = $row['id'];
        $comment->fk_post = (int)$row['fk_post'];
        $comment->fk_author = (int)$row['fk_author'];
        $comment->content = $row['content'];
        $comment->created_at = $row['created_at'];
        $comment->updated_at = $row['updated_at'] ?? null;
        return $comment;
    }

    /**
     * @param int[] $postPks
     * @param int $limit
     * @return array<int, Comment[]>
     */
    public static function findByPostPks(array $postPks, int $limit = 50): array
    {
        if (empty($postPks)) {
            return [];
        }

        $pdo = Connection::get();
        $placeholders = implode(',', array_fill(0, count($postPks), '?'));
        $sql = "
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY fk_post ORDER BY pk_comment) as rn
                FROM tb_comment
                WHERE fk_post IN ({$placeholders})
            ) t WHERE rn <= ?
            ORDER BY fk_post, pk_comment
        ";
        $stmt = $pdo->prepare($sql);
        $stmt->execute([...$postPks, $limit]);

        $commentsByPost = array_fill_keys($postPks, []);
        while ($row = $stmt->fetch()) {
            $comment = self::fromRow($row);
            $commentsByPost[$comment->fk_post][] = $comment;
        }
        return $commentsByPost;
    }
}
