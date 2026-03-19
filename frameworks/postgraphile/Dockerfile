FROM node:20-alpine

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm ci --only=production=false

# Copy source and build
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# Remove dev dependencies after build
RUN npm prune --production

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD node -e "require('http').get('http://localhost:4000/health', r => { process.exit(r.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))"

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

EXPOSE 4000

CMD ["node", "dist/src/index.js"]
