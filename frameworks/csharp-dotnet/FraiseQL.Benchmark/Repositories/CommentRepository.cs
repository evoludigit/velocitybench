using FraiseQL.Benchmark.Data;
using FraiseQL.Benchmark.Models;
using Microsoft.EntityFrameworkCore;

namespace FraiseQL.Benchmark.Repositories;

public class CommentRepository : ICommentRepository
{
    private readonly BenchmarkContext _context;

    public CommentRepository(BenchmarkContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<Comment>> GetByPostIdAsync(Guid postId, int page = 0, int size = 10)
    {
        return await _context.Comments
            .Include(c => c.Author)
            .Include(c => c.Post)
            .AsNoTracking()
            .Where(c => c.Post != null && c.Post.Id == postId)
            .OrderBy(c => c.CreatedAt)
            .Skip(page * size)
            .Take(size)
            .ToListAsync();
    }

    public async Task<IEnumerable<Comment>> GetByAuthorIdAsync(Guid authorId, int page = 0, int size = 10)
    {
        return await _context.Comments
            .Include(c => c.Author)
            .Include(c => c.Post)
            .AsNoTracking()
            .Where(c => c.Author != null && c.Author.Id == authorId)
            .OrderByDescending(c => c.CreatedAt)
            .Skip(page * size)
            .Take(size)
            .ToListAsync();
    }
}