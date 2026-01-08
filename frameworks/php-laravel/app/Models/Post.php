<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Post extends Model
{
    use HasFactory;

    protected $primaryKey = "pk_post";
    protected $keyType = "int";
    public $incrementing = true;

    protected $fillable = [
        "id",
        "title",
        "content",
        "fk_author",
        "created_at"
    ];

    protected $table = "benchmark.tb_post";

    public function author(): BelongsTo
    {
        return $this->belongsTo(User::class, "fk_author", "pk_user");
    }

    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class, "fk_post", "pk_post");
    }
}
