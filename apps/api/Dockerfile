FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN corepack enable && yarn install
COPY tsconfig.json ./
COPY src ./src
RUN yarn build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package.json ./
RUN corepack enable && yarn install --production
COPY --from=build /app/dist ./dist
EXPOSE 8000
CMD ["node", "dist/index.js"]
