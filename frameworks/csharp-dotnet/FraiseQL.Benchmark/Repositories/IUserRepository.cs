using FraiseQL.Benchmark.Models;

namespace FraiseQL.Benchmark.Repositories;

public interface IUserRepository
{
    Task<User?> GetByIdAsync(Guid id);
    Task<IEnumerable<User>> GetAllAsync(int page = 0, int size = 10);
}