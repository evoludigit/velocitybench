FROM node:20-alpine

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY tsconfig.json ./
COPY src ./src
RUN npm run build
RUN npm prune --production

# Install curl for health checks
RUN apk add --no-cache curl

EXPOSE 8007

CMD ["node", "dist/index.js"]
