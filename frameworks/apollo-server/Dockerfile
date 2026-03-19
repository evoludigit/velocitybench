FROM node:20-alpine

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY tsconfig.json ./
COPY src ./src
RUN npm run build && test -f dist/index.js || (echo "TypeScript build failed: dist/index.js missing" && exit 1)
RUN npm prune --production

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

EXPOSE 4002

CMD ["node", "dist/index.js"]
