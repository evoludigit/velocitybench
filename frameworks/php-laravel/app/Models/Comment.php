<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Comment extends Model
{
    use HasFactory;

    protected $primaryKey = "pk_comment";
    protected $keyType = "int";
    public $incrementing = true;

    protected $fillable = [
        "id",
        "content",
        "fk_post",
        "fk_author",
        "created_at"
    ];

    protected $casts = [
        "id" => "string",
    ];

    protected $table = "benchmark.tb_comment";
    public $timestamps = false;

    public function post(): BelongsTo
    {
        return $this->belongsTo(Post::class, "fk_post", "pk_post");
    }

    public function author(): BelongsTo
    {
        return $this->belongsTo(User::class, "fk_author", "pk_user");
    }
}