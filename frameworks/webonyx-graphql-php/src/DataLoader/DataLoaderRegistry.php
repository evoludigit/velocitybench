<?php
declare(strict_types=1);

namespace VelocityBench\DataLoader;

use Overblog\DataLoader\DataLoader;
use Overblog\PromiseAdapter\Adapter\WebonyxGraphQLSyncPromiseAdapter;
use VelocityBench\Model\User;
use VelocityBench\Model\Post;
use VelocityBench\Model\Comment;

class DataLoaderRegistry
{
    private WebonyxGraphQLSyncPromiseAdapter $promiseAdapter;
    private ?DataLoader $userLoader = null;
    private ?DataLoader $postLoader = null;
    private ?DataLoader $postsByAuthorLoader = null;
    private ?DataLoader $commentsByPostLoader = null;

    public function __construct()
    {
        $this->promiseAdapter = new WebonyxGraphQLSyncPromiseAdapter();
    }

    public function getUserLoader(): DataLoader
    {
        if ($this->userLoader === null) {
            $adapter = $this->promiseAdapter;
            $this->userLoader = new DataLoader(
                function (array $keys) use ($adapter) {
                    $users = User::findByPks($keys);
                    $result = array_map(fn($key) => $users[$key] ?? null, $keys);
                    return $adapter->createFulfilled($result);
                },
                $adapter
            );
        }
        return $this->userLoader;
    }

    public function getPostLoader(): DataLoader
    {
        if ($this->postLoader === null) {
            $adapter = $this->promiseAdapter;
            $this->postLoader = new DataLoader(
                function (array $keys) use ($adapter) {
                    $posts = Post::findByPks($keys);
                    $result = array_map(fn($key) => $posts[$key] ?? null, $keys);
                    return $adapter->createFulfilled($result);
                },
                $adapter
            );
        }
        return $this->postLoader;
    }

    public function getPostsByAuthorLoader(int $limit = 50): DataLoader
    {
        if ($this->postsByAuthorLoader === null) {
            $adapter = $this->promiseAdapter;
            $this->postsByAuthorLoader = new DataLoader(
                function (array $keys) use ($adapter, $limit) {
                    $postsByAuthor = Post::findByAuthorPks($keys, $limit);
                    $result = array_map(fn($key) => $postsByAuthor[$key] ?? [], $keys);
                    return $adapter->createFulfilled($result);
                },
                $adapter
            );
        }
        return $this->postsByAuthorLoader;
    }

    public function getCommentsByPostLoader(int $limit = 50): DataLoader
    {
        if ($this->commentsByPostLoader === null) {
            $adapter = $this->promiseAdapter;
            $this->commentsByPostLoader = new DataLoader(
                function (array $keys) use ($adapter, $limit) {
                    $commentsByPost = Comment::findByPostPks($keys, $limit);
                    $result = array_map(fn($key) => $commentsByPost[$key] ?? [], $keys);
                    return $adapter->createFulfilled($result);
                },
                $adapter
            );
        }
        return $this->commentsByPostLoader;
    }
}
