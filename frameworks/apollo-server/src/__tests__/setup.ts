// Test setup file for Apollo Server tests
import { Pool } from 'pg';

// Mock database pool for tests
const mockPool = {
  query: jest.fn(),
  connect: jest.fn(),
  end: jest.fn(),
} as unknown as Pool;

jest.mock('../db', () => ({
  pool: mockPool,
}));

// Disable console logs during tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
};
