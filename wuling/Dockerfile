FROM node:20-slim 

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN npm i -g corepack@latest && corepack enable

COPY pnpm-lock.yaml /app/
WORKDIR /app
RUN pnpm fetch --prod

COPY . /app/
RUN pnpm i
RUN pnpm build
WORKDIR /app/server
RUN pnpm i

EXPOSE 4000
CMD [ "pnpm", "dev" ]