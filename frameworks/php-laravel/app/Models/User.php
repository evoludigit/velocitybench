<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class User extends Model
{
    use HasFactory;

    protected $primaryKey = "pk_user";
    protected $keyType = "int";
    public $incrementing = true;

    protected $fillable = [
        "id",
        "username",
        "full_name",
        "bio"
    ];

    protected $casts = [
        "id" => "string",
    ];

    protected $table = "benchmark.tb_user";

    public function posts(): HasMany
    {
        return $this->hasMany(Post::class, "fk_author", "pk_user");
    }

    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class, "fk_author", "pk_user");
    }
}
