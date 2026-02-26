import { v4 as uuidv4 } from 'uuid';

export interface TestUser {
  id: string;
  pk_user: number;
  username: string;
  full_name: string;
  bio: string | null;
  created_at: Date;
  updated_at: Date;
}

export interface TestPost {
  id: string;
  pk_post: number;
  fk_author: number;
  title: string;
  content: string;
  published: boolean;
  created_at: Date;
  updated_at: Date;
  author?: TestUser;
}

export interface TestComment {
  id: string;
  pk_comment: number;
  fk_post: number;
  fk_author: number;
  content: string;
  created_at: Date;
  author?: TestUser;
  post?: TestPost;
}

export class TestFactory {
  private users: Map<string, TestUser> = new Map();
  private posts: Map<string, TestPost> = new Map();
  private comments: Map<string, TestComment> = new Map();
  private userCounter: number = 1;
  private postCounter: number = 1;
  private commentCounter: number = 1;

  createTestUser(username: string, email: string, fullName: string, bio: string): TestUser {
    const user: TestUser = {
      id: uuidv4(),
      pk_user: this.userCounter++,
      username,
      full_name: fullName,
      bio: bio ? bio : null,
      created_at: new Date(),
      updated_at: new Date(),
    };

    this.users.set(user.id, user);
    return user;
  }

  createTestPost(authorId: string, title: string, content: string): TestPost {
    const author = this.users.get(authorId);
    if (!author) {
      throw new Error(`Author not found: ${authorId}`);
    }

    const post: TestPost = {
      id: uuidv4(),
      pk_post: this.postCounter++,
      fk_author: author.pk_user,
      title,
      content,
      published: true,
      created_at: new Date(),
      updated_at: new Date(),
      author,
    };

    this.posts.set(post.id, post);
    return post;
  }

  createTestComment(authorId: string, postId: string, content: string): TestComment {
    const author = this.users.get(authorId);
    const post = this.posts.get(postId);

    if (!author || !post) {
      throw new Error('Author or Post not found');
    }

    const comment: TestComment = {
      id: uuidv4(),
      pk_comment: this.commentCounter++,
      fk_post: post.pk_post,
      fk_author: author.pk_user,
      content,
      created_at: new Date(),
      author,
      post,
    };

    this.comments.set(comment.id, comment);
    return comment;
  }

  getUser(id: string): TestUser | undefined {
    return this.users.get(id);
  }

  getPost(id: string): TestPost | undefined {
    return this.posts.get(id);
  }

  getComment(id: string): TestComment | undefined {
    return this.comments.get(id);
  }

  getAllUsers(): TestUser[] {
    return Array.from(this.users.values());
  }

  getAllPosts(): TestPost[] {
    return Array.from(this.posts.values());
  }

  getAllComments(): TestComment[] {
    return Array.from(this.comments.values());
  }

  getPostsByAuthor(authorPk: number): TestPost[] {
    return Array.from(this.posts.values()).filter(p => p.fk_author === authorPk);
  }

  getCommentsByPost(postPk: number): TestComment[] {
    return Array.from(this.comments.values()).filter(c => c.fk_post === postPk);
  }

  getUserCount(): number {
    return this.users.size;
  }

  getPostCount(): number {
    return this.posts.size;
  }

  getCommentCount(): number {
    return this.comments.size;
  }

  reset(): void {
    this.users.clear();
    this.posts.clear();
    this.comments.clear();
    this.userCounter = 1;
    this.postCounter = 1;
    this.commentCounter = 1;
  }
}

export class ValidationHelper {
  static isValidUUID(value: string): boolean {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(value);
  }

  static assertUUID(value: string): void {
    if (!this.isValidUUID(value)) {
      throw new Error(`Invalid UUID: ${value}`);
    }
  }

  static assertNotEmpty(value: string, name: string): void {
    if (!value || value.trim() === '') {
      throw new Error(`${name} should not be empty`);
    }
  }
}

export class DataGenerator {
  static generateLongString(length: number): string {
    let result = '';
    for (let i = 0; i < length; i++) {
      result += String(i % 10);
    }
    return result;
  }

  static generateUniqueStrings(count: number): string[] {
    return Array.from({ length: count }, () => uuidv4());
  }
}
