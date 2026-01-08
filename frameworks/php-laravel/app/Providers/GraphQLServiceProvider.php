<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use Nuwave\Lighthouse\Schema\TypeRegistry;
use Nuwave\Lighthouse\Schema\Source\SchemaSourceProvider;

class GraphQLServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        // Register custom field resolvers
        app('events')->listen('lighthouse.schema.build', function () {
            // Custom resolvers for complex queries
            app(TypeRegistry::class)->registerLazy('Query', function () {
                return [
                    'postsByUser' => function ($root, $args) {
                        return \App\Models\Post::where('author_id', $args['userId'])
                            ->orderBy('created_at', 'desc')
                            ->take(10)
                            ->get();
                    },
                    'commentsByPost' => function ($root, $args) {
                        return \App\Models\Comment::where('post_id', $args['postId'])
                            ->orderBy('created_at')
                            ->take(10)
                            ->get();
                    },
                ];
            });
        });
    }
}
