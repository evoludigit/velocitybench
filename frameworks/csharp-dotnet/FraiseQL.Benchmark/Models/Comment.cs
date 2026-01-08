using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace FraiseQL.Benchmark.Models;

[Table("tb_comment", Schema = "benchmark")]
public class Comment
{
    [Key]
    [Column("pk_comment")]
    public int PkComment { get; set; }

    [Column("id")]
    public Guid Id { get; set; }

    [Column("content")]
    [Required]
    public string Content { get; set; } = string.Empty;

    [Column("fk_post")]
    [Required]
    public int FkPost { get; set; }

    [Column("fk_author")]
    [Required]
    public int FkAuthor { get; set; }

    [Column("created_at")]
    public DateTime CreatedAt { get; set; }

    // Navigation properties
    [ForeignKey("FkPost")]
    public virtual Post? Post { get; set; }

    [ForeignKey("FkAuthor")]
    public virtual User? Author { get; set; }
}