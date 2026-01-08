using FraiseQL.Benchmark.Repositories;
using Microsoft.AspNetCore.Mvc;

namespace FraiseQL.Benchmark.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PostsController : ControllerBase
{
    private readonly IPostRepository _postRepository;

    public PostsController(IPostRepository postRepository)
    {
        _postRepository = postRepository;
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var post = await _postRepository.GetByIdAsync(id);
        if (post == null)
        {
            return NotFound(new { error = "Post not found" });
        }

        return Ok(new
        {
            id = post.Id,
            title = post.Title,
            content = post.Content,
            authorId = post.Author?.Id,
            createdAt = post.CreatedAt.ToString("O") // ISO 8601 format
        });
    }

    [HttpGet]
    public async Task<IActionResult> GetAll([FromQuery] int page = 0, [FromQuery] int size = 10)
    {
        var posts = await _postRepository.GetAllAsync(page, size);
        var result = posts.Select(post => new
        {
            id = post.Id,
            title = post.Title,
            content = post.Content,
            authorId = post.Author?.Id,
            createdAt = post.CreatedAt.ToString("O")
        });

        return Ok(result);
    }

    [HttpGet("by-author/{authorId}")]
    public async Task<IActionResult> GetByAuthor(Guid authorId, [FromQuery] int page = 0, [FromQuery] int size = 10)
    {
        var posts = await _postRepository.GetByAuthorIdAsync(authorId, page, size);
        var result = posts.Select(post => new
        {
            id = post.Id,
            title = post.Title,
            content = post.Content,
            authorId = post.Author?.Id,
            createdAt = post.CreatedAt.ToString("O")
        });

        return Ok(result);
    }
}