<?php
declare(strict_types=1);

namespace VelocityBench\GraphQL;

use GraphQL\Type\Definition\ObjectType;
use GraphQL\Type\Definition\Type;
use GraphQL\Type\Schema as GraphQLSchema;
use GraphQL\Type\SchemaConfig;
use VelocityBench\Model\User;
use VelocityBench\Model\Post;

class Schema
{
    public static function build(): GraphQLSchema
    {
        $queryType = new ObjectType([
            'name' => 'Query',
            'fields' => [
                'ping' => [
                    'type' => Type::nonNull(Type::string()),
                    'resolve' => fn() => 'pong'
                ],
                'user' => [
                    'type' => Types::user(),
                    'args' => [
                        'id' => Type::nonNull(Type::id())
                    ],
                    'resolve' => fn($root, array $args) => User::findById($args['id'])
                ],
                'users' => [
                    'type' => Type::nonNull(Type::listOf(Type::nonNull(Types::user()))),
                    'args' => [
                        'limit' => [
                            'type' => Type::int(),
                            'defaultValue' => 10
                        ]
                    ],
                    'resolve' => fn($root, array $args) => User::all(min($args['limit'], 100))
                ],
                'post' => [
                    'type' => Types::post(),
                    'args' => [
                        'id' => Type::nonNull(Type::id())
                    ],
                    'resolve' => fn($root, array $args) => Post::findById($args['id'])
                ],
                'posts' => [
                    'type' => Type::nonNull(Type::listOf(Type::nonNull(Types::post()))),
                    'args' => [
                        'limit' => [
                            'type' => Type::int(),
                            'defaultValue' => 10
                        ],
                        'published' => [
                            'type' => Type::boolean()
                        ]
                    ],
                    'resolve' => fn($root, array $args) => Post::all(
                        min($args['limit'], 100),
                        array_key_exists('published', $args) ? $args['published'] : null
                    )
                ]
            ]
        ]);

        $mutationType = new ObjectType([
            'name' => 'Mutation',
            'fields' => [
                'updateUser' => [
                    'type' => Types::user(),
                    'args' => [
                        'id' => Type::nonNull(Type::id()),
                        'input' => Type::nonNull(Types::updateUserInput())
                    ],
                    'resolve' => function ($root, array $args) {
                        $data = [];
                        if (isset($args['input']['fullName'])) {
                            $data['full_name'] = $args['input']['fullName'];
                        }
                        if (isset($args['input']['bio'])) {
                            $data['bio'] = $args['input']['bio'];
                        }
                        return User::update($args['id'], $data);
                    }
                ],
                'updatePost' => [
                    'type' => Types::post(),
                    'args' => [
                        'id' => Type::nonNull(Type::id()),
                        'input' => Type::nonNull(Types::updatePostInput())
                    ],
                    'resolve' => function ($root, array $args) {
                        $data = [];
                        if (isset($args['input']['title'])) {
                            $data['title'] = $args['input']['title'];
                        }
                        if (isset($args['input']['content'])) {
                            $data['content'] = $args['input']['content'];
                        }
                        return Post::update($args['id'], $data);
                    }
                ]
            ]
        ]);

        return new GraphQLSchema(
            SchemaConfig::create()
                ->setQuery($queryType)
                ->setMutation($mutationType)
        );
    }
}
