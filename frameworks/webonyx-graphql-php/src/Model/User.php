<?php
declare(strict_types=1);

namespace VelocityBench\Model;

use VelocityBench\Database\Connection;
use PDO;

class User
{
    public int $pk_user;
    public string $id;
    public string $username;
    public ?string $full_name;
    public ?string $bio;
    public string $created_at;
    public ?string $updated_at;

    public static function fromRow(array $row): self
    {
        $user = new self();
        $user->pk_user = (int)$row['pk_user'];
        $user->id = $row['id'];
        $user->username = $row['username'];
        $user->full_name = $row['full_name'];
        $user->bio = $row['bio'];
        $user->created_at = $row['created_at'];
        $user->updated_at = $row['updated_at'] ?? null;
        return $user;
    }

    public static function findById(string $id): ?self
    {
        $pdo = Connection::get();
        $stmt = $pdo->prepare('SELECT * FROM tb_user WHERE id = :id');
        $stmt->execute(['id' => $id]);
        $row = $stmt->fetch();
        return $row ? self::fromRow($row) : null;
    }

    public static function findByPk(int $pk): ?self
    {
        $pdo = Connection::get();
        $stmt = $pdo->prepare('SELECT * FROM tb_user WHERE pk_user = :pk');
        $stmt->execute(['pk' => $pk]);
        $row = $stmt->fetch();
        return $row ? self::fromRow($row) : null;
    }

    /**
     * @param int[] $pks
     * @return array<int, User>
     */
    public static function findByPks(array $pks): array
    {
        if (empty($pks)) {
            return [];
        }

        $pdo = Connection::get();
        $placeholders = implode(',', array_fill(0, count($pks), '?'));
        $stmt = $pdo->prepare("SELECT * FROM tb_user WHERE pk_user IN ({$placeholders})");
        $stmt->execute($pks);

        $users = [];
        while ($row = $stmt->fetch()) {
            $user = self::fromRow($row);
            $users[$user->pk_user] = $user;
        }
        return $users;
    }

    /**
     * @return User[]
     */
    public static function all(int $limit = 10): array
    {
        $pdo = Connection::get();
        $stmt = $pdo->prepare('SELECT * FROM tb_user ORDER BY pk_user LIMIT :limit');
        $stmt->bindValue('limit', min($limit, 100), PDO::PARAM_INT);
        $stmt->execute();

        $users = [];
        while ($row = $stmt->fetch()) {
            $users[] = self::fromRow($row);
        }
        return $users;
    }

    public static function update(string $id, array $data): ?self
    {
        $pdo = Connection::get();

        $sets = [];
        $params = ['id' => $id];

        if (isset($data['full_name'])) {
            $sets[] = 'full_name = :full_name';
            $params['full_name'] = $data['full_name'];
        }
        if (isset($data['bio'])) {
            $sets[] = 'bio = :bio';
            $params['bio'] = $data['bio'];
        }

        if (empty($sets)) {
            return self::findById($id);
        }

        $sets[] = 'updated_at = NOW()';
        $sql = 'UPDATE tb_user SET ' . implode(', ', $sets) . ' WHERE id = :id';
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);

        return self::findById($id);
    }
}
