using FraiseQL.Benchmark.Repositories;
using AutoMapper;
using FraiseQL.Benchmark.DTOs;
using Microsoft.AspNetCore.Mvc;

namespace FraiseQL.Benchmark.Controllers;

[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IUserRepository _userRepository;
    private readonly IMapper _mapper;

    public UsersController(IUserRepository userRepository, IMapper mapper)
    {
        _userRepository = userRepository;
        _mapper = mapper;
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var user = await _userRepository.GetByIdAsync(id);
        if (user == null)
        {
            return NotFound(new { error = "User not found" });
        }

        var userDto = _mapper.Map<UserDto>(user);
        return Ok(userDto);
    }

    [HttpGet]
    public async Task<IActionResult> GetAll([FromQuery] int page = 0, [FromQuery] int size = 10)
    {
        var users = await _userRepository.GetAllAsync(page, size);
        var userDtos = _mapper.Map<IEnumerable<UserDto>>(users);
        return Ok(userDtos);
    }
}