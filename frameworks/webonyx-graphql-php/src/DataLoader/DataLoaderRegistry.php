<?php
declare(strict_types=1);

namespace VelocityBench\DataLoader;

use Overblog\DataLoader\DataLoader;
use Overblog\DataLoader\Option\CacheMap;
use VelocityBench\Model\User;
use VelocityBench\Model\Post;
use VelocityBench\Model\Comment;
use React\Promise\Promise;

class DataLoaderRegistry
{
    private ?DataLoader $userLoader = null;
    private ?DataLoader $postLoader = null;
    private ?DataLoader $postsByAuthorLoader = null;
    private ?DataLoader $commentsByPostLoader = null;

    public function getUserLoader(): DataLoader
    {
        if ($this->userLoader === null) {
            $this->userLoader = new DataLoader(
                function (array $keys) {
                    return new Promise(function ($resolve) use ($keys) {
                        $users = User::findByPks($keys);
                        $result = array_map(fn($key) => $users[$key] ?? null, $keys);
                        $resolve($result);
                    });
                },
                null,
                new CacheMap()
            );
        }
        return $this->userLoader;
    }

    public function getPostLoader(): DataLoader
    {
        if ($this->postLoader === null) {
            $this->postLoader = new DataLoader(
                function (array $keys) {
                    return new Promise(function ($resolve) use ($keys) {
                        $posts = Post::findByPks($keys);
                        $result = array_map(fn($key) => $posts[$key] ?? null, $keys);
                        $resolve($result);
                    });
                },
                null,
                new CacheMap()
            );
        }
        return $this->postLoader;
    }

    public function getPostsByAuthorLoader(int $limit = 50): DataLoader
    {
        // Note: In a production system, you'd want different loaders for different limits
        // For simplicity, we create one loader per request
        if ($this->postsByAuthorLoader === null) {
            $this->postsByAuthorLoader = new DataLoader(
                function (array $keys) use ($limit) {
                    return new Promise(function ($resolve) use ($keys, $limit) {
                        $postsByAuthor = Post::findByAuthorPks($keys, $limit);
                        $result = array_map(fn($key) => $postsByAuthor[$key] ?? [], $keys);
                        $resolve($result);
                    });
                },
                null,
                new CacheMap()
            );
        }
        return $this->postsByAuthorLoader;
    }

    public function getCommentsByPostLoader(int $limit = 50): DataLoader
    {
        if ($this->commentsByPostLoader === null) {
            $this->commentsByPostLoader = new DataLoader(
                function (array $keys) use ($limit) {
                    return new Promise(function ($resolve) use ($keys, $limit) {
                        $commentsByPost = Comment::findByPostPks($keys, $limit);
                        $result = array_map(fn($key) => $commentsByPost[$key] ?? [], $keys);
                        $resolve($result);
                    });
                },
                null,
                new CacheMap()
            );
        }
        return $this->commentsByPostLoader;
    }
}
