using FraiseQL.Benchmark.Models;

namespace FraiseQL.Benchmark.Repositories;

public interface ICommentRepository
{
    Task<IEnumerable<Comment>> GetByPostIdAsync(Guid postId, int page = 0, int size = 10);
    Task<IEnumerable<Comment>> GetByAuthorIdAsync(Guid authorId, int page = 0, int size = 10);
}