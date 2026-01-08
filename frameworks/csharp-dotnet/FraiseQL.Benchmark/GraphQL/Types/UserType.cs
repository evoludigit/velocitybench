using FraiseQL.Benchmark.Models;
using HotChocolate.Types;

namespace FraiseQL.Benchmark.GraphQL.Types;

public class UserType : ObjectType<User>
{
    protected override void Configure(IObjectTypeDescriptor<User> descriptor)
    {
        descriptor.Field(u => u.Id);
        descriptor.Field(u => u.Username);
        descriptor.Field(u => u.FullName);
        descriptor.Field(u => u.Bio);
        descriptor.Field(u => u.Posts);
        descriptor.Field(u => u.Comments);
    }
}