/**
 * Example Jest tests for VelocityBench TypeScript frameworks.
 *
 * This template shows the standard pattern for testing:
 * 1. UNIT TESTS: Test functions/classes without external dependencies
 * 2. INTEGRATION TESTS: Test with database
 */

import { Pool } from 'pg';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';

// ============================================================================
// Database Helpers
// ============================================================================

class TestDatabase {
  private pool: Pool;

  constructor() {
    this.pool = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432'),
      user: process.env.DB_USER || 'velocitybench',
      password: process.env.DB_PASSWORD || 'password',
      database: process.env.DB_NAME || 'velocitybench_test',
    });
  }

  async connect(): Promise<void> {
    const client = await this.pool.connect();
    client.release();
  }

  async query(sql: string, params?: any[]): Promise<any[]> {
    const result = await this.pool.query(sql, params);
    return result.rows;
  }

  async close(): Promise<void> {
    await this.pool.end();
  }
}

// ============================================================================
// Test Factory
// ============================================================================

class TestFactory {
  constructor(private db: TestDatabase) {}

  async createUser(name: string, email: string): Promise<any> {
    const rows = await this.db.query(
      'INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email',
      [name, email]
    );
    return rows[0];
  }

  async createCompany(name: string): Promise<any> {
    const rows = await this.db.query(
      'INSERT INTO companies (name) VALUES ($1) RETURNING id, name',
      [name]
    );
    return rows[0];
  }

  async createProduct(name: string, price: number, companyId: number): Promise<any> {
    const rows = await this.db.query(
      'INSERT INTO products (name, price, company_id) VALUES ($1, $2, $3) ' +
      'RETURNING id, name, price, company_id',
      [name, price, companyId]
    );
    return rows[0];
  }
}

// ============================================================================
// Unit Tests (no database dependency)
// ============================================================================

describe('User Validation', () => {
  it('should validate correct email format', () => {
    const isValidEmail = (email: string): boolean => {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    };
    expect(isValidEmail('user@example.com')).toBe(true);
    expect(isValidEmail('invalid@')).toBe(false);
  });

  it('should normalize user names', () => {
    const normalizeName = (name: string): string => {
      return name.toLowerCase().trim();
    };
    expect(normalizeName('JOHN DOE')).toBe('john doe');
    expect(normalizeName('  alice  ')).toBe('alice');
  });

  it.each([
    ['valid@example.com', true],
    ['invalid@', false],
    ['no-at-sign.com', false],
  ])('should validate email %s as %s', (email, expected) => {
    const isValidEmail = (email: string): boolean => {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    };
    expect(isValidEmail(email)).toBe(expected);
  });
});

describe('Data Transformation', () => {
  it('should format prices correctly', () => {
    const formatPrice = (price: number): string => {
      return `$${price.toFixed(2)}`;
    };
    expect(formatPrice(19.99)).toBe('$19.99');
    expect(formatPrice(100.0)).toBe('$100.00');
  });

  it('should create user object from data', () => {
    interface User {
      id: number;
      name: string;
      email: string;
    }

    const userData = { id: 1, name: 'Alice', email: 'alice@example.com' };
    const user: User = userData;

    expect(user.id).toBe(1);
    expect(user.name).toBe('Alice');
    expect(user.email).toBe('alice@example.com');
  });
});

// ============================================================================
// Integration Tests (with database)
// ============================================================================

describe('User Queries', () => {
  let db: TestDatabase;
  let factory: TestFactory;

  beforeEach(async () => {
    db = new TestDatabase();
    await db.connect();
    factory = new TestFactory(db);

    // Clean up test tables
    await db.query('DELETE FROM orders');
    await db.query('DELETE FROM products');
    await db.query('DELETE FROM users');
    await db.query('DELETE FROM companies');
  });

  afterEach(async () => {
    await db.close();
  });

  it('should create a user', async () => {
    // Arrange
    const userData = { name: 'Alice', email: 'alice@example.com' };

    // Act
    const user = await factory.createUser(userData.name, userData.email);

    // Assert
    expect(user).toBeDefined();
    expect(user.name).toBe('Alice');
    expect(user.email).toBe('alice@example.com');
    expect(user.id).toBeDefined();
  });

  it('should retrieve user by id', async () => {
    // Arrange
    const created = await factory.createUser('Bob', 'bob@example.com');
    const userId = created.id;

    // Act
    const users = await db.query('SELECT id, name, email FROM users WHERE id = $1', [userId]);
    const user = users[0];

    // Assert
    expect(user).toBeDefined();
    expect(user.id).toBe(userId);
    expect(user.name).toBe('Bob');
    expect(user.email).toBe('bob@example.com');
  });

  it('should list all users', async () => {
    // Arrange
    await factory.createUser('Alice', 'alice@example.com');
    await factory.createUser('Bob', 'bob@example.com');
    await factory.createUser('Charlie', 'charlie@example.com');

    // Act
    const users = await db.query('SELECT id, name, email FROM users ORDER BY name');

    // Assert
    expect(users).toHaveLength(3);
    expect(users[0].name).toBe('Alice');
    expect(users[1].name).toBe('Bob');
    expect(users[2].name).toBe('Charlie');
  });

  it('should update a user', async () => {
    // Arrange
    const created = await factory.createUser('Alice', 'alice@example.com');
    const userId = created.id;

    // Act
    await db.query('UPDATE users SET email = $1 WHERE id = $2', [
      'alice.new@example.com',
      userId,
    ]);

    // Assert
    const users = await db.query('SELECT email FROM users WHERE id = $1', [userId]);
    expect(users[0].email).toBe('alice.new@example.com');
  });

  it('should delete a user', async () => {
    // Arrange
    const created = await factory.createUser('Alice', 'alice@example.com');
    const userId = created.id;

    // Act
    await db.query('DELETE FROM users WHERE id = $1', [userId]);

    // Assert
    const users = await db.query('SELECT id FROM users WHERE id = $1', [userId]);
    expect(users).toHaveLength(0);
  });
});

describe('Product Queries', () => {
  let db: TestDatabase;
  let factory: TestFactory;

  beforeEach(async () => {
    db = new TestDatabase();
    await db.connect();
    factory = new TestFactory(db);

    // Clean up test tables
    await db.query('DELETE FROM orders');
    await db.query('DELETE FROM products');
    await db.query('DELETE FROM users');
    await db.query('DELETE FROM companies');
  });

  afterEach(async () => {
    await db.close();
  });

  it('should create a product', async () => {
    // Arrange
    const company = await factory.createCompany('ACME Corp');

    // Act
    const product = await factory.createProduct('Widget', 19.99, company.id);

    // Assert
    expect(product).toBeDefined();
    expect(product.name).toBe('Widget');
    expect(product.price).toBe(19.99);
  });

  it('should list products by company', async () => {
    // Arrange
    const company1 = await factory.createCompany('ACME Corp');
    const company2 = await factory.createCompany('TechCorp');

    await factory.createProduct('Widget A', 10.0, company1.id);
    await factory.createProduct('Widget B', 20.0, company1.id);
    await factory.createProduct('Gadget', 30.0, company2.id);

    // Act
    const products = await db.query(
      'SELECT id, name, price FROM products WHERE company_id = $1 ORDER BY name',
      [company1.id]
    );

    // Assert
    expect(products).toHaveLength(2);
    expect(products[0].name).toBe('Widget A');
    expect(products[1].name).toBe('Widget B');
  });
});

// ============================================================================
// Complex Query Tests
// ============================================================================

describe('Complex Queries', () => {
  let db: TestDatabase;
  let factory: TestFactory;

  beforeEach(async () => {
    db = new TestDatabase();
    await db.connect();
    factory = new TestFactory(db);

    // Clean up test tables
    await db.query('DELETE FROM orders');
    await db.query('DELETE FROM products');
    await db.query('DELETE FROM users');
    await db.query('DELETE FROM companies');
  });

  afterEach(async () => {
    await db.close();
  });

  it('should aggregate user orders', async () => {
    // Arrange
    const user = await factory.createUser('Alice', 'alice@example.com');

    // Create some orders
    await db.query('INSERT INTO orders (user_id, total) VALUES ($1, $2)', [
      user.id,
      100.0,
    ]);

    // Act
    const results = await db.query(
      'SELECT u.id, u.name, COUNT(o.id) as order_count ' +
      'FROM users u ' +
      'LEFT JOIN orders o ON u.id = o.user_id ' +
      'WHERE u.id = $1 ' +
      'GROUP BY u.id',
      [user.id]
    );

    // Assert
    expect(results[0].order_count).toBe(1);
  });
});
