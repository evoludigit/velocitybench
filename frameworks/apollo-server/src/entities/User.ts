import { Entity, PrimaryColumn, Column } from 'typeorm';

@Entity({ schema: 'benchmark', name: 'tb_user' })
export class User {
  @PrimaryColumn('uuid')
  id!: string;

  @Column('text')
  username!: string;

  @Column('text', { nullable: true })
  full_name!: string | null;

  @Column('text', { nullable: true })
  bio!: string | null;

  @Column('timestamp')
  updated_at!: Date;
}
