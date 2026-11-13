FROM node:26-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN addgroup -S -g 10001 prism && adduser -S -u 10001 -G prism prism \
  && chown -R prism:prism /app
USER prism

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
