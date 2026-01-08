import { Entity, Column, PrimaryColumn, OneToMany, ManyToMany, JoinTable, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity({ name: 'benchmark.tb_user', synchronize: false })
export class User {
  @PrimaryColumn({ type: 'varchar' })
  id!: string;

  @Column({ type: 'integer' })
  pk_user!: number;

  @Column({ type: 'varchar' })
  username!: string;

  @Column({ type: 'varchar', nullable: true })
  full_name?: string;

  @Column({ type: 'text', nullable: true })
  bio?: string;

  @CreateDateColumn({ type: 'timestamp' })
  created_at!: Date;

  @UpdateDateColumn({ type: 'timestamp' })
  updated_at!: Date;

  // Relationships - using string references to avoid circular dependencies
  @OneToMany('Post', 'author')
  posts?: any[];

  @OneToMany('Comment', 'author')
  comments?: any[];

  @ManyToMany('User', 'followers')
  @JoinTable({
    name: 'benchmark.tb_user_follows',
    joinColumn: { name: 'fk_following', referencedColumnName: 'pk_user' },
    inverseJoinColumn: { name: 'fk_follower', referencedColumnName: 'pk_user' }
  })
  followers?: any[];

  @ManyToMany('User', 'following')
  following?: any[];
}