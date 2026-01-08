using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace FraiseQL.Benchmark.Models;

[Table("tb_user", Schema = "benchmark")]
public class User
{
    [Key]
    [Column("pk_user")]
    public int PkUser { get; set; }

    [Column("id")]
    public Guid Id { get; set; }

    [Column("username")]
    [Required]
    public string Username { get; set; } = string.Empty;

    [Column("full_name")]
    [Required]
    public string FullName { get; set; } = string.Empty;

    [Column("bio")]
    public string? Bio { get; set; }

    [Column("created_at")]
    public DateTime CreatedAt { get; set; }

    // Navigation properties
    public virtual ICollection<Post> Posts { get; set; } = new List<Post>();
    public virtual ICollection<Comment> Comments { get; set; } = new List<Comment>();
}