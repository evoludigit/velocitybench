using FraiseQL.Benchmark.Models;

namespace FraiseQL.Benchmark.Repositories;

public interface IPostRepository
{
    Task<Post?> GetByIdAsync(Guid id);
    Task<IEnumerable<Post>> GetAllAsync(int page = 0, int size = 10, bool? published = null);
    Task<IEnumerable<Post>> GetByAuthorIdAsync(Guid authorId, int page = 0, int size = 10);
}