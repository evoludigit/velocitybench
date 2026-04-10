<?php

namespace App\Http\Controllers;

use App\Models\Comment;
use App\Models\Post;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class CommentController extends Controller
{
    public function byPost(string $postId, Request $request): JsonResponse
    {
        $post = Post::where('id', $postId)->first();

        if (!$post) {
            return response()->json([], 200);
        }

        $limit = min((int) $request->get('limit', 10), 100);

        $comments = Comment::with('author')
            ->where('fk_post', $post->pk_post)
            ->orderBy('created_at', 'desc')
            ->limit($limit)
            ->get()
            ->map(fn($c) => [
                'id'        => $c->id,
                'content'   => $c->content,
                'createdAt' => \Carbon\Carbon::parse($c->created_at)->toISOString(),
                'author'    => [
                    'id'       => $c->author?->id,
                    'username' => $c->author?->username,
                    'fullName' => $c->author?->full_name,
                ],
            ]);

        return response()->json($comments);
    }
}
