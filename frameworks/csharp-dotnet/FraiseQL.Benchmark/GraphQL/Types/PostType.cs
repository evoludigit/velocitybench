using FraiseQL.Benchmark.GraphQL.Resolvers;
using FraiseQL.Benchmark.Models;

namespace FraiseQL.Benchmark.GraphQL.Types;

public class PostType : ObjectType<Post>
{
    protected override void Configure(IObjectTypeDescriptor<Post> descriptor)
    {
        descriptor.Field(p => p.Id);
        descriptor.Field(p => p.Title);
        descriptor.Field(p => p.Content);
        descriptor.Field(p => p.FkAuthor).Name("authorId");
        descriptor.Field(p => p.CreatedAt);
    }
}