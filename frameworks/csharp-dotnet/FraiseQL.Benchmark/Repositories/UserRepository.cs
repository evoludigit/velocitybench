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
}