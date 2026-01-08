using FraiseQL.Benchmark.Models;
using FraiseQL.Benchmark.Repositories;

namespace FraiseQL.Benchmark.GraphQL.Resolvers;

public class CommentResolvers
{
    public Task<Post?> GetPost([Parent] Comment comment)
    {
        return Task.FromResult(comment.Post);
    }

    public Task<User?> GetAuthor([Parent] Comment comment)
    {
        return Task.FromResult(comment.Author);
    }
}