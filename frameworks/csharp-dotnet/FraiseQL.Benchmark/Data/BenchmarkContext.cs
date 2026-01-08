using FraiseQL.Benchmark.Models;
using Microsoft.EntityFrameworkCore;

namespace FraiseQL.Benchmark.Data;

public class BenchmarkContext : DbContext
{
    public BenchmarkContext(DbContextOptions<BenchmarkContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users { get; set; } = null!;
    public DbSet<Post> Posts { get; set; } = null!;
    public DbSet<Comment> Comments { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure schema
        modelBuilder.HasDefaultSchema("benchmark");

        // Configure relationships
        modelBuilder.Entity<Post>()
            .HasOne(p => p.Author)
            .WithMany(u => u.Posts)
            .HasForeignKey(p => p.FkAuthor)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<Comment>()
            .HasOne(c => c.Post)
            .WithMany(p => p.Comments)
            .HasForeignKey(c => c.FkPost)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<Comment>()
            .HasOne(c => c.Author)
            .WithMany(u => u.Comments)
            .HasForeignKey(c => c.FkAuthor)
            .OnDelete(DeleteBehavior.Cascade);

        // UUIDs don't need string length constraints since they're Guid type
    }
}