<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

Route::get('/graphql-playground', function () {
    return view('graphql-playground');
});
