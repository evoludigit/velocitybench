import request from 'supertest';
import { Pool } from 'pg';
import { startServer } from '../src/index';
import { TestFactory } from './test-factory';

describe('Smoke Test', () => {
  let server: any;
  let pool: Pool;
  let factory: TestFactory;

  beforeAll(async () => {
    server = await startServer();
    pool = new Pool({
      user: process.env.DB_USER || 'velocitybench',
      password: process.env.DB_PASSWORD || 'password',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME || 'velocitybench_test',
    });
    factory = new TestFactory(pool);
  });

  afterAll(async () => {
    await pool.end();
    server.close();
  }, 15000);

  afterEach(async () => {
    await factory.cleanup();
  });

  test('health endpoint should return healthy', async () => {
    const response = await request(server)
      .get('/health');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('healthy');
    expect(response.body.timestamp).toBeDefined();
  });

  test('ready endpoint should return ready', async () => {
    const response = await request(server)
      .get('/ready');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('ready');
  });

  test('graphql introspection should work', async () => {
    const response = await request(server)
      .post('/graphql')
      .send({
        query: '{ __typename }',
      });

    expect(response.status).toBe(200);
    expect(response.body.data.__typename).toBe('Query');
  });
});
