FROM node:24-slim AS build
RUN corepack enable && corepack prepare pnpm@9.14.2 --activate
WORKDIR /app
COPY . .
ARG NUXT_API_PROXY_TARGET=http://api:8000
ARG NUXT_MEDIA_PROXY_TARGET=http://s3:8333/nit-media
ENV NUXT_API_PROXY_TARGET=$NUXT_API_PROXY_TARGET \
    NUXT_MEDIA_PROXY_TARGET=$NUXT_MEDIA_PROXY_TARGET \
    NUXT_TELEMETRY_DISABLED=1
RUN pnpm install --frozen-lockfile && pnpm build

FROM node:24-slim
WORKDIR /app
COPY --from=build /app/.output ./.output
ENV NODE_ENV=production HOST=0.0.0.0 PORT=3000
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
