using FraiseQL.Benchmark.Models;

namespace FraiseQL.Benchmark.GraphQL.Types;

public class CommentType : ObjectType<Comment>
{
    protected override void Configure(IObjectTypeDescriptor<Comment> descriptor)
    {
        descriptor.Field(c => c.Id);
        descriptor.Field(c => c.Content);
        descriptor.Field(c => c.FkPost).Name("postId");
        descriptor.Field(c => c.FkAuthor).Name("authorId");
        descriptor.Field(c => c.CreatedAt);
    }
}