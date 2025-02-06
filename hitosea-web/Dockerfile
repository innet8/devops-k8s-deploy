FROM node:18-slim 

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN npm install -g pnpm@8.4.0

# COPY pnpm-lock.yaml /app/
WORKDIR /app
# RUN pnpm fetch --prod

COPY . /app/
RUN pnpm install --reporter append-only
RUN pnpm install -g cross-env
RUN pnpm run build

EXPOSE 3000
CMD [ "pnpm", "run", "start" ]