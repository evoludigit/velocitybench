using FraiseQL.Benchmark.Data;
using FraiseQL.Benchmark.Models;
using Microsoft.EntityFrameworkCore;

namespace FraiseQL.Benchmark.Repositories;

public class PostRepository : IPostRepository
{
    private readonly BenchmarkContext _context;

    public PostRepository(BenchmarkContext context)
    {
        _context = context;
    }

    public async Task<Post?> GetByIdAsync(Guid id)
    {
        return await _context.Posts
            .Include(p => p.Author)
            .AsNoTracking()
            .FirstOrDefaultAsync(p => p.Id == id);
    }

    public async Task<IEnumerable<Post>> GetAllAsync(int page = 0, int size = 10)
    {
        return await _context.Posts
            .Include(p => p.Author)
            .AsNoTracking()
            .OrderByDescending(p => p.CreatedAt)
            .Skip(page * size)
            .Take(size)
            .ToListAsync();
    }

    public async Task<IEnumerable<Post>> GetByAuthorIdAsync(Guid authorId, int page = 0, int size = 10)
    {
        return await _context.Posts
            .Include(p => p.Author)
            .AsNoTracking()
            .Where(p => p.Author != null && p.Author.Id == authorId)
            .OrderByDescending(p => p.CreatedAt)
            .Skip(page * size)
            .Take(size)
            .ToListAsync();
    }
}