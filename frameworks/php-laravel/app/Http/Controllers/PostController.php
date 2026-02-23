<?php

namespace App\Http\Controllers;

use App\Models\Post;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class PostController extends Controller
{
    public function show(string $id): JsonResponse
    {
        $post = Post::with("author")->find($id);

        if (!$post) {
            return response()->json(["error" => "Post not found"], 404);
        }

        return response()->json([
            "id" => $post->id,
            "title" => $post->title,
            "content" => $post->content,
            "authorId" => $post->author?->id ?? $post->fk_author,
            "createdAt" => $post->created_at->toISOString()
        ]);
    }

    public function index(Request $request): JsonResponse
    {
        $page = $request->get("page", 0);
        $limit = $request->get("limit", $request->get("size", 10));
        $includeAuthor = $request->has("include") && $request->get("include") === "author";

        $posts = Post::with("author")
            ->orderBy("created_at", "desc")
            ->skip($page * $limit)
            ->take($limit)
            ->get();

        $result = $posts->map(function ($post) use ($includeAuthor) {
            $item = [
                "id" => $post->id,
                "title" => $post->title,
                "content" => $post->content,
                "authorId" => $post->author?->id ?? $post->fk_author,
                "createdAt" => $post->created_at->toISOString()
            ];
            if ($includeAuthor && $post->author) {
                $item["author"] = [
                    "username" => $post->author->username,
                    "fullName" => $post->author->full_name,
                ];
            }
            return $item;
        });

        return response()->json($result);
    }

    public function getPostsByAuthor(string $authorId, Request $request): JsonResponse
    {
        $page = $request->get("page", 0);
        $size = $request->get("size", 10);

        // Find user by UUID first to get the integer primary key
        $user = User::where("id", $authorId)->first();
        if (!$user) {
            return response()->json(["error" => "User not found"], 404);
        }

        // Use the integer primary key for the relationship lookup
        $posts = Post::with("author")
            ->where("fk_author", $user->pk_user)
            ->orderBy("created_at", "desc")
            ->skip($page * $size)
            ->take($size)
            ->get();

        $result = $posts->map(function ($post) {
            return [
                "id" => $post->id,
                "title" => $post->title,
                "content" => $post->content,
                "authorId" => $post->author?->id ?? $post->fk_author,
                "createdAt" => $post->created_at->toISOString()
            ];
        });

        return response()->json($result);
    }
}
