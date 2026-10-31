# Build stage: Hugo builds the site, Pagefind builds the search index.
FROM node:26.12.1-alpine3.24 AS build

ARG HUGO_VERSION=0.161.1
ARG TARGETARCH
RUN apk add --no-cache git make \
 && wget -qO- "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_${HUGO_VERSION}_linux-${TARGETARCH}.tar.gz" \
    | tar -xz -C /usr/local/bin hugo

WORKDIR /site
COPY . .
# .git is copied on purpose: "Updated" dates come from git history.
RUN git config --global --add safe.directory /site && make build

# Serve stage: nginx serves the static files.
FROM nginx:1.31.7-alpine3.24
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /site/public /usr/share/nginx/html
