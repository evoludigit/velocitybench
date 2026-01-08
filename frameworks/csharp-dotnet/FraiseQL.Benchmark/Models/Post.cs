using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace FraiseQL.Benchmark.Models;

[Table("tb_post", Schema = "benchmark")]
public class Post
{
    [Key]
    [Column("pk_post")]
    public int PkPost { get; set; }

    [Column("id")]
    public Guid Id { get; set; }

    [Column("title")]
    [Required]
    public string Title { get; set; } = string.Empty;

    [Column("content")]
    [Required]
    public string Content { get; set; } = string.Empty;

    [Column("fk_author")]
    [Required]
    public int FkAuthor { get; set; }

    [Column("created_at")]
    public DateTime CreatedAt { get; set; }

    // Navigation properties
    [ForeignKey("FkAuthor")]
    public virtual User? Author { get; set; }

    public virtual ICollection<Comment> Comments { get; set; } = new List<Comment>();
}