using FraiseQL.Benchmark.Controllers;
using FraiseQL.Benchmark.Data;
using FraiseQL.Benchmark.GraphQL;
using FraiseQL.Benchmark.GraphQL.Types;
using FraiseQL.Benchmark.GraphQL.Resolvers;
using FraiseQL.Benchmark.Mapping;
using FraiseQL.Benchmark.Repositories;
using Microsoft.EntityFrameworkCore;
using HotChocolate;
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();

// Configure Entity Framework Core with PostgreSQL
builder.Services.AddDbContext<BenchmarkContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// Register repositories
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IPostRepository, PostRepository>();
builder.Services.AddScoped<ICommentRepository, CommentRepository>();

// Add AutoMapper
builder.Services.AddAutoMapper(typeof(MappingProfile));

// Add GraphQL support
builder.Services
    .AddGraphQLServer()
    .AddQueryType<Query>()
    .AddType<UserType>()
    .AddType<PostType>()
    .AddType<CommentType>()
    .AddType<PostResolvers>()
    .AddType<CommentResolvers>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}

app.UseAuthorization();

app.MapControllers();

app.MapGraphQL("/graphql");

// Health check endpoint
app.MapGet("/health", () => Results.Json(new { status = "UP", service = "csharp-dotnet-benchmark" }));

// Simple Prometheus metrics endpoint
app.MapGet("/metrics", () =>
{
    var metrics = new System.Text.StringBuilder();
    metrics.AppendLine("# HELP dotnet_gc_collections_total Number of garbage collections");
    metrics.AppendLine("# TYPE dotnet_gc_collections_total counter");
    metrics.AppendLine($"dotnet_gc_collections_total{{generation=\"gen0\"}} {GC.CollectionCount(0)}");
    metrics.AppendLine($"dotnet_gc_collections_total{{generation=\"gen1\"}} {GC.CollectionCount(1)}");
    metrics.AppendLine($"dotnet_gc_collections_total{{generation=\"gen2\"}} {GC.CollectionCount(2)}");
    metrics.AppendLine();
    metrics.AppendLine("# HELP dotnet_memory_heap_size_bytes Heap memory usage");
    metrics.AppendLine("# TYPE dotnet_memory_heap_size_bytes gauge");
    metrics.AppendLine($"dotnet_memory_heap_size_bytes {GC.GetTotalMemory(false)}");
    metrics.AppendLine();
    metrics.AppendLine("# HELP process_cpu_user_seconds_total Total user CPU time spent in seconds");
    metrics.AppendLine("# TYPE process_cpu_user_seconds_total counter");
    metrics.AppendLine($"process_cpu_user_seconds_total {System.Diagnostics.Process.GetCurrentProcess().TotalProcessorTime.TotalSeconds:F3}");
    metrics.AppendLine();
    metrics.AppendLine("# HELP dotnet_threads_count Number of active threads");
    metrics.AppendLine("# TYPE dotnet_threads_count gauge");
    metrics.AppendLine($"dotnet_threads_count {System.Threading.ThreadPool.ThreadCount}");

    return Results.Text(metrics.ToString(), "text/plain; version=0.0.4; charset=utf-8");
});

app.Run();
