# Dev Dockerfile for Next.js with hot reload
FROM node:20-alpine

WORKDIR /app

# Avoid running as root in dev as well
RUN addgroup --system --gid 1001 nodejs \
 	&& adduser --system --uid 1001 nextjs

# Install OS deps that help with native modules if needed
RUN apk add --no-cache libc6-compat

# Copy only package manifests first for better caching
COPY --chown=nextjs:nodejs package.json package-lock.json ./

# Create directories with correct ownership upfront
RUN mkdir -p /app/node_modules /app/.next \
	&& chown nextjs:nodejs /app/node_modules /app/.next

# Switch to non-root user before npm install
USER nextjs

# Install all dependencies including devDependencies for tooling
RUN npm ci

# Copy the rest of the app with correct ownership
COPY --chown=nextjs:nodejs . .

ENV NODE_ENV=development
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

EXPOSE 3000

# Default command for dev compose; can be overridden
CMD ["npm", "run", "dev"]


