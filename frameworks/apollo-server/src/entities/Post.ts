import { Entity, PrimaryColumn, Column } from 'typeorm';

@Entity({ schema: 'benchmark', name: 'tb_post' })
export class Post {
  @PrimaryColumn('uuid')
  id!: string;

  @Column('text')
  title!: string;

  @Column('text', { nullable: true })
  content!: string | null;

  @Column('uuid')
  author_id!: string;

  @Column('timestamp')
  updated_at!: Date;
}
