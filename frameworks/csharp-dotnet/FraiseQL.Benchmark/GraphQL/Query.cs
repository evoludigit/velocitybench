using FraiseQL.Benchmark.Models;
using FraiseQL.Benchmark.Repositories;

namespace FraiseQL.Benchmark.GraphQL;

public class Query
{
    public async Task<User?> GetUser(
        Guid id,
        [Service] IUserRepository userRepository)
    {
        return await userRepository.GetByIdAsync(id);
    }

    public async Task<IEnumerable<User>> GetUsers(
        [Service] IUserRepository userRepository,
        int limit = 10)
    {
        return await userRepository.GetAllAsync(0, limit);
    }

    public async Task<Post?> GetPost(
        Guid id,
        [Service] IPostRepository postRepository)
    {
        return await postRepository.GetByIdAsync(id);
    }

    public async Task<IEnumerable<Post>> GetPosts(
        [Service] IPostRepository postRepository,
        int limit = 10)
    {
        return await postRepository.GetAllAsync(0, limit);
    }

    public async Task<IEnumerable<Post>> GetPostsByUser(
        Guid userId,
        [Service] IPostRepository postRepository,
        int first = 10)
    {
        return await postRepository.GetByAuthorIdAsync(userId, 0, first);
    }

    public async Task<IEnumerable<Comment>> GetCommentsByPost(
        Guid postId,
        [Service] ICommentRepository commentRepository,
        int first = 10)
    {
        return await commentRepository.GetByPostIdAsync(postId, 0, first);
    }
}