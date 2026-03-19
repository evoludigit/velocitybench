using FraiseQL.Benchmark.Models;
using FraiseQL.Benchmark.Repositories;

namespace FraiseQL.Benchmark.GraphQL;

public class Mutation
{
    public async Task<User?> UpdateUser(
        Guid id,
        string? bio,
        [Service] IUserRepository userRepository)
    {
        return await userRepository.UpdateAsync(id, bio);
    }
}
