using FraiseQL.Benchmark.Models;
using FraiseQL.Benchmark.Repositories;
using HotChocolate;

namespace FraiseQL.Benchmark.GraphQL.Resolvers;

public class PostResolvers
{
    public Task<User?> GetAuthor([Parent] Post post)
    {
        return Task.FromResult(post.Author);
    }

    public async Task<IEnumerable<Comment>> GetComments(
        [Parent] Post post,
        [Service] ICommentRepository commentRepository,
        int first = 10)
    {
        return await commentRepository.GetByPostIdAsync(post.Id, 0, first);
    }
}