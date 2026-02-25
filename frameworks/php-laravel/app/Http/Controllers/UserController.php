<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class UserController extends Controller
{
    public function show(string $id): JsonResponse
    {
        $user = User::find($id);
        
        if (!$user) {
            return response()->json(["error" => "User not found"], 404);
        }
        
        return response()->json([
            "id" => $user->id,
            "username" => $user->username,
            "fullName" => $user->full_name,
            "bio" => $user->bio
        ]);
    }

    public function index(Request $request): JsonResponse
    {
        $limit = $request->get("limit", $request->get("size", 10));
        $offset = $request->get("offset", $request->get("page", 0) * $limit);

        $users = User::orderBy("username")
            ->offset($offset)
            ->limit($limit)
            ->get();
            
        $result = $users->map(function ($user) {
            return [
                "id" => $user->id,
                "username" => $user->username,
                "fullName" => $user->full_name,
                "bio" => $user->bio
            ];
        });
        
        return response()->json($result);
    }
}