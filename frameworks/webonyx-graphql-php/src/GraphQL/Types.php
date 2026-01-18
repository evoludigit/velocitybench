<?php
declare(strict_types=1);

namespace VelocityBench\GraphQL;

use GraphQL\Type\Definition\ObjectType;
use GraphQL\Type\Definition\Type;
use GraphQL\Type\Definition\InputObjectType;
use VelocityBench\Model\User;
use VelocityBench\Model\Post;

class Types
{
    private static ?ObjectType $userType = null;
    private static ?ObjectType $postType = null;
    private static ?ObjectType $commentType = null;
    private static ?InputObjectType $updateUserInput = null;
    private static ?InputObjectType $updatePostInput = null;

    public static function user(): ObjectType
    {
        if (self::$userType === null) {
            self::$userType = new ObjectType([
                'name' => 'User',
                'fields' => fn() => [
                    'id' => [
                        'type' => Type::nonNull(Type::id()),
                        'resolve' => fn(User $user) => $user->id
                    ],
                    'username' => [
                        'type' => Type::nonNull(Type::string()),
                        'resolve' => fn(User $user) => $user->username
                    ],
                    'fullName' => [
                        'type' => Type::string(),
                        'resolve' => fn(User $user) => $user->full_name
                    ],
                    'bio' => [
                        'type' => Type::string(),
                        'resolve' => fn(User $user) => $user->bio
                    ],
                    'createdAt' => [
                        'type' => Type::nonNull(Type::string()),
                        'resolve' => fn(User $user) => $user->created_at
                    ],
                    'posts' => [
                        'type' => Type::nonNull(Type::listOf(Type::nonNull(self::post()))),
                        'args' => [
                            'limit' => [
                                'type' => Type::int(),
                                'defaultValue' => 50
                            ]
                        ],
                        'resolve' => function (User $user, array $args, $context) {
                            $limit = min($args['limit'], 50);
                            return $context['loaders']->getPostsByAuthorLoader($limit)->load($user->pk_user);
                        }
                    ],
                    'followers' => [
                        'type' => Type::nonNull(Type::listOf(Type::nonNull(self::user()))),
                        'args' => [
                            'limit' => [
                                'type' => Type::int(),
                                'defaultValue' => 50
                            ]
                        ],
                        'resolve' => fn() => [] // Not implemented in benchmark schema
                    ],
                    'following' => [
                        'type' => Type::nonNull(Type::listOf(Type::nonNull(self::user()))),
                        'args' => [
                            'limit' => [
                                'type' => Type::int(),
                                'defaultValue' => 50
                            ]
                        ],
                        'resolve' => fn() => [] // Not implemented in benchmark schema
                    ]
                ]
            ]);
        }
        return self::$userType;
    }

    public static function post(): ObjectType
    {
        if (self::$postType === null) {
            self::$postType = new ObjectType([
                'name' => 'Post',
                'fields' => fn() => [
                    'id' => [
                        'type' => Type::nonNull(Type::id()),
                        'resolve' => fn(Post $post) => $post->id
                    ],
                    'title' => [
                        'type' => Type::nonNull(Type::string()),
                        'resolve' => fn(Post $post) => $post->title
                    ],
                    'content' => [
                        'type' => Type::string(),
                        'resolve' => fn(Post $post) => $post->content
                    ],
                    'createdAt' => [
                        'type' => Type::nonNull(Type::string()),
                        'resolve' => fn(Post $post) => $post->created_at
                    ],
                    'author' => [
                        'type' => Type::nonNull(self::user()),
                        'resolve' => function (Post $post, array $args, $context) {
                            return $context['loaders']->getUserLoader()->load($post->fk_author);
                        }
                    ],
                    'comments' => [
                        'type' => Type::nonNull(Type::listOf(Type::nonNull(self::comment()))),
                        'args' => [
                            'limit' => [
                                'type' => Type::int(),
                                'defaultValue' => 50
                            ]
                        ],
                        'resolve' => function (Post $post, array $args, $context) {
                            $limit = min($args['limit'], 50);
                            return $context['loaders']->getCommentsByPostLoader($limit)->load($post->pk_post);
                        }
                    ]
                ]
            ]);
        }
        return self::$postType;
    }

    public static function comment(): ObjectType
    {
        if (self::$commentType === null) {
            self::$commentType = new ObjectType([
                'name' => 'Comment',
                'fields' => fn() => [
                    'id' => [
                        'type' => Type::nonNull(Type::id()),
                        'resolve' => fn($comment) => $comment->id
                    ],
                    'content' => [
                        'type' => Type::nonNull(Type::string()),
                        'resolve' => fn($comment) => $comment->content
                    ],
                    'createdAt' => [
                        'type' => Type::nonNull(Type::string()),
                        'resolve' => fn($comment) => $comment->created_at
                    ],
                    'author' => [
                        'type' => self::user(),
                        'resolve' => function ($comment, array $args, $context) {
                            return $context['loaders']->getUserLoader()->load($comment->fk_author);
                        }
                    ],
                    'post' => [
                        'type' => self::post(),
                        'resolve' => function ($comment, array $args, $context) {
                            return $context['loaders']->getPostLoader()->load($comment->fk_post);
                        }
                    ]
                ]
            ]);
        }
        return self::$commentType;
    }

    public static function updateUserInput(): InputObjectType
    {
        if (self::$updateUserInput === null) {
            self::$updateUserInput = new InputObjectType([
                'name' => 'UpdateUserInput',
                'fields' => [
                    'fullName' => Type::string(),
                    'bio' => Type::string()
                ]
            ]);
        }
        return self::$updateUserInput;
    }

    public static function updatePostInput(): InputObjectType
    {
        if (self::$updatePostInput === null) {
            self::$updatePostInput = new InputObjectType([
                'name' => 'UpdatePostInput',
                'fields' => [
                    'title' => Type::string(),
                    'content' => Type::string()
                ]
            ]);
        }
        return self::$updatePostInput;
    }
}
