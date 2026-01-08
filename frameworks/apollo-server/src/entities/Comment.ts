import { Entity, PrimaryColumn, Column } from 'typeorm';

@Entity({ schema: 'benchmark', name: 'tb_comment' })
export class Comment {
  @PrimaryColumn('uuid')
  id!: string;

  @Column('text')
  content!: string;

  @Column('uuid')
  post_id!: string;

  @Column('uuid')
  author_id!: string;

  @Column('timestamp')
  updated_at!: Date;
}
