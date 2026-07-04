import { PostGraphileAmberPreset } from 'postgraphile/presets/amber';
import { makePgService } from 'postgraphile/adaptors/pg';

const DB_USER = process.env.DB_USER || 'benchmark';
const DB_PASSWORD =
  process.env.DB_PASSWORD ??
  (() => {
    throw new Error('DB_PASSWORD env var is required');
  })();
const DB_HOST = process.env.DB_HOST || 'localhost';
const DB_PORT = process.env.DB_PORT || '5432';
const DB_NAME = process.env.DB_NAME || 'velocitybench_benchmark';

export const connectionString = `postgres://${DB_USER}:${encodeURIComponent(
  DB_PASSWORD
)}@${DB_HOST}:${DB_PORT}/${DB_NAME}`;

const preset: GraphileConfig.Preset = {
  // Stock amber preset — no custom plugins or inflection. Note: amber renames
  // the uuid `id` column to `rowId` (the `id` field is the Relay node ID), so
  // benchmark documents alias `id: rowId` to return the uuid like every other
  // framework does.
  extends: [PostGraphileAmberPreset],
  pgServices: [
    makePgService({
      connectionString,
      schemas: ['benchmark'],
      poolConfig: { max: 50 },
    }),
  ],
  grafserv: {
    graphqlPath: '/graphql',
    graphiql: false,
    watch: false,
  },
};

export default preset;
