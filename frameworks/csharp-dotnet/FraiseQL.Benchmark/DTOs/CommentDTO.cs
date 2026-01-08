namespace FraiseQL.Benchmark.DTOs;

public class CommentDto
{
    public Guid Id { get; set; }
    public string Content { get; set; } = string.Empty;
    public Guid AuthorId { get; set; }
    public Guid PostId { get; set; }
    public UserDto? Author { get; set; }
    public PostDto? Post { get; set; }
}

public class CreateCommentDto
{
    public string Content { get; set; } = string.Empty;
    public Guid PostId { get; set; }
}

public class UpdateCommentDto
{
    public string? Content { get; set; }
}