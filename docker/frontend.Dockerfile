# Build context is the repo root (see docker-compose.yml), same reasoning
# as backend.Dockerfile even though frontend/ has no cross-package deps —
# keeps both services' `context:` consistent and simple.
FROM node:20-alpine

WORKDIR /app

# Installed from the lockfile before the rest of the source is copied so
# this layer only invalidates when dependencies actually change.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .

# Next.js inlines NEXT_PUBLIC_* env vars into the client bundle at build
# time, not at container start — must be set before `next build` runs.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
