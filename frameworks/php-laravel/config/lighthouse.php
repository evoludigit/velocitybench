<?php

return [
    'route' => [
        'prefix' => 'graphql',
        'middleware' => ['web'],
    ],

    'schema' => [
        'register' => __DIR__.'/../graphql/schema.graphql',
    ],

    'cache' => [
        'enable' => false,
    ],

    'debug' => [
        'enable' => true,
    ],

    'pagination' => [
        'default_count' => 10,
        'max_count' => 100,
    ],
];
