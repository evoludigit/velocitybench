import { Sequelize, DataTypes, Model } from 'sequelize';

export const sequelize = new Sequelize({
  dialect: 'postgres',
  host: process.env.DB_HOST || 'postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'fraiseql_benchmark',
  username: process.env.DB_USER || 'benchmark',
  password: process.env.DB_PASSWORD || 'benchmark123',
  pool: {
    min: 10,
    max: 50,
    idle: 30000,
    acquire: 5000,
  },
  logging: false,
});

// Define models
export class User extends Model {
  declare id: string;
  declare pk_user: number;
  declare username: string;
  declare full_name: string;
  declare bio: string;
  declare created_at: Date;
  declare updated_at: Date;

  // Relationships
  declare posts?: Post[];
  declare followers?: User[];
  declare following?: User[];
}

export class Post extends Model {
  declare id: string;
  declare pk_post: number;
  declare fk_author: number;
  declare title: string;
  declare content: string;
  declare published: boolean;
  declare created_at: Date;
  declare updated_at: Date;

  // Relationships
  declare author?: User;
  declare comments?: Comment[];
}

export class Comment extends Model {
  declare id: string;
  declare pk_comment: number;
  declare fk_post: number;
  declare fk_author: number;
  declare content: string;
  declare created_at: Date;

  // Relationships
  declare author?: User;
  declare post?: Post;
}

// Initialize models
User.init({
  id: {
    type: DataTypes.STRING,
    primaryKey: true,
  },
  pk_user: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  username: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  full_name: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  bio: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
  created_at: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  updated_at: {
    type: DataTypes.DATE,
    allowNull: false,
  },
}, {
  sequelize,
  tableName: 'tb_user',
  schema: 'benchmark',
  timestamps: false,
});

Post.init({
  id: {
    type: DataTypes.STRING,
    primaryKey: true,
  },
  pk_post: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  fk_author: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  title: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  content: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  published: {
    type: DataTypes.BOOLEAN,
    allowNull: false,
  },
  created_at: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  updated_at: {
    type: DataTypes.DATE,
    allowNull: false,
  },
}, {
  sequelize,
  tableName: 'tb_post',
  schema: 'benchmark',
  timestamps: false,
});

Comment.init({
  id: {
    type: DataTypes.STRING,
    primaryKey: true,
  },
  pk_comment: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  fk_post: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  fk_author: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  content: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  created_at: {
    type: DataTypes.DATE,
    allowNull: false,
  },
}, {
  sequelize,
  tableName: 'tb_comment',
  schema: 'benchmark',
  timestamps: false,
});

// Define relationships
User.hasMany(Post, { foreignKey: 'fk_author', sourceKey: 'pk_user', as: 'posts' });
Post.belongsTo(User, { foreignKey: 'fk_author', targetKey: 'pk_user', as: 'author' });

Post.hasMany(Comment, { foreignKey: 'fk_post', sourceKey: 'pk_post', as: 'comments' });
Comment.belongsTo(Post, { foreignKey: 'fk_post', targetKey: 'pk_post', as: 'post' });

Comment.belongsTo(User, { foreignKey: 'fk_author', targetKey: 'pk_user', as: 'author' });

// Many-to-many relationships for followers
User.belongsToMany(User, {
  through: 'tb_user_follows',
  as: 'followers',
  foreignKey: 'fk_following',
  otherKey: 'fk_follower',
});

User.belongsToMany(User, {
  through: 'tb_user_follows',
  as: 'following',
  foreignKey: 'fk_follower',
  otherKey: 'fk_following',
});

// Initialize database connection
export async function initDatabase() {
  try {
    await sequelize.authenticate();
    console.log('Database connection established successfully.');
  } catch (error) {
    console.error('Unable to connect to the database:', error);
    throw error;
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, closing database connection...');
  await sequelize.close();
  process.exit(0);
});