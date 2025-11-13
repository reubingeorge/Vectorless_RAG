# Development Dockerfile for Next.js with hot reload
FROM node:20-alpine

# Install dependencies for alpine
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev dependencies)
RUN npm install

# Copy the rest of the application
COPY . .

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

ENV PORT 3000

# Run development server with hot reload
CMD ["npm", "run", "dev"]