namespace FraiseQL.Benchmark.DTOs;

public class UserDto
{
    public Guid Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string? FullName { get; set; }
    public string? Bio { get; set; }
}

public class CreateUserDto
{
    public string Email { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string? FullName { get; set; }
    public string? Bio { get; set; }
}

public class UpdateUserDto
{
    public string? FullName { get; set; }
    public string? Bio { get; set; }
}