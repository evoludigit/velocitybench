import { Entity, Column, PrimaryColumn, ManyToOne, JoinColumn, CreateDateColumn } from 'typeorm';

@Entity({ name: 'benchmark.tb_comment', synchronize: false })
export class Comment {
  @PrimaryColumn({ type: 'varchar' })
  id!: string;

  @Column({ type: 'integer' })
  pk_comment!: number;

  @Column({ type: 'integer' })
  fk_post!: number;

  @Column({ type: 'integer' })
  fk_author!: number;

  @Column({ type: 'text' })
  content!: string;

  @CreateDateColumn({ type: 'timestamp' })
  created_at!: Date;

  // Relationships - using string references to avoid circular dependencies
  @ManyToOne('Post', 'comments')
  @JoinColumn({ name: 'fk_post', referencedColumnName: 'pk_post' })
  post?: any;

  @ManyToOne('User', 'comments')
  @JoinColumn({ name: 'fk_author', referencedColumnName: 'pk_user' })
  author?: any;
}