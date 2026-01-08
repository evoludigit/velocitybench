namespace FraiseQL.Benchmark.DTOs;

public class PostDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Content { get; set; }
    public Guid AuthorId { get; set; }
    public UserDto? Author { get; set; }
    public List<CommentDto>? Comments { get; set; }
}

public class CreatePostDto
{
    public string Title { get; set; } = string.Empty;
    public string? Content { get; set; }
}

public class UpdatePostDto
{
    public string? Title { get; set; }
    public string? Content { get; set; }
}