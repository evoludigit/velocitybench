using FraiseQL.Benchmark.Data;
using FraiseQL.Benchmark.Models;
using Microsoft.EntityFrameworkCore;

namespace FraiseQL.Benchmark.Repositories;

public class UserRepository : IUserRepository
{
    private readonly BenchmarkContext _context;

    public UserRepository(BenchmarkContext context)
    {
        _context = context;
    }

    public async Task<User?> GetByIdAsync(Guid id)
    {
        return await _context.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Id == id);
    }

    public async Task<IEnumerable<User>> GetAllAsync(int page = 0, int size = 10)
    {
        return await _context.Users
            .AsNoTracking()
            .OrderBy(u => u.Username)
            .Skip(page * size)
            .Take(size)
            .ToListAsync();
    }

    public async Task<User?> UpdateAsync(Guid id, string? bio)
    {
        if (bio is null)
            return await GetByIdAsync(id);

        var affected = await _context.Users
            .Where(u => u.Id == id)
            .ExecuteUpdateAsync(s => s.SetProperty(u => u.Bio, bio));

        return affected > 0 ? await GetByIdAsync(id) : null;
    }
}