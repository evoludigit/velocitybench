module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    // Inherit the project tsconfig (node16 module resolution — required for
    // postgraphile v5's exports-map subpaths). tests/ is excluded from the
    // build tsconfig, so re-include it here.
    // Transpile-only: type checking happens in `npm run build` (tsc); ts-jest's
    // own checker mis-resolves grafserv's exports-map subpath re-exports.
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.json', diagnostics: false }],
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
  ],
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
  ],
  setupFilesAfterEnv: [],
  testTimeout: 15000,
  maxWorkers: 1,
  // The grafserv pg pool has no public handle to close from the smoke test.
  forceExit: true,
};
