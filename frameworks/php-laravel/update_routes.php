<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\UserController;
use App\Http\Controllers\PostController;
use App\Http\Controllers\HealthController;

Route::get('/user', function (Request $request) {
    return 'API';
});

// API Routes
Route::get('/users/{id}', [UserController::class, 'show']);
Route::get('/users', [UserController::class, 'index']);

Route::get('/posts/{id}', [PostController::class, 'show']);
Route::get('/posts', [PostController::class, 'index']);
Route::get('/posts/by-author/{authorId}', [PostController::class, 'getPostsByAuthor']);

Route::get('/health', [HealthController::class, 'index']);

echo "Routes updated successfully!\n";
