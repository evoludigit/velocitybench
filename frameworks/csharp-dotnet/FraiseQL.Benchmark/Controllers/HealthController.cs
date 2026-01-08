using Microsoft.AspNetCore.Mvc;

namespace FraiseQL.Benchmark.Controllers;

[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    [HttpGet]
    public IActionResult Index()
    {
        return Ok(new
        {
            status = "UP",
            service = "csharp-dotnet-benchmark"
        });
    }
}