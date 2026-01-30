import { Entity, Column, PrimaryColumn, ManyToOne, OneToMany, JoinColumn, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity({ name: 'benchmark.tb_post', synchronize: false })
export class Post {
  @PrimaryColumn({ type: 'uuid' })
  id!: string;

  @Column({ type: 'integer' })
  pk_post!: number;

  @Column({ type: 'integer' })
  fk_author!: number;

  @Column({ type: 'varchar' })
  title!: string;

  @Column({ type: 'text' })
  content!: string;

  @Column({ type: 'boolean' })
  published!: boolean;

  @CreateDateColumn({ type: 'timestamp' })
  created_at!: Date;

  @UpdateDateColumn({ type: 'timestamp' })
  updated_at!: Date;

  // Relationships - using string references to avoid circular dependencies
  @ManyToOne('User', 'posts')
  @JoinColumn({ name: 'fk_author', referencedColumnName: 'pk_user' })
  author?: any;

  @OneToMany('Comment', 'post')
  comments?: any[];
}