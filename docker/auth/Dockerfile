# Firebase Auth emulator only (plan S1.1). The emulator is Node code inside firebase-tools; no
# Java runtime is installed or needed. It starts from the committed seed on every start, so
# the demo identities are deterministic and survive restarts. A `demo-` project needs no
# Google credentials and cannot reach real Firebase services.
FROM node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205

ENV PATH=/opt/emulator/node_modules/.bin:$PATH NO_UPDATE_NOTIFIER=1 FIREBASE_CLI_DISABLE_UPDATE_CHECK=true
RUN corepack enable \
    && corepack prepare pnpm@10.33.2 --activate \
    && useradd --create-home emulator

# firebase-tools and every transitive dependency come from the committed lockfile (GC2).
WORKDIR /opt/emulator
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod

USER emulator
WORKDIR /home/emulator
COPY --chown=emulator firebase.json .
COPY --chown=emulator seed ./seed
EXPOSE 9099
HEALTHCHECK --interval=2s --timeout=3s --retries=60 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:9099/').then(r => process.exit(r.ok ? 0 : 1), () => process.exit(1))"]
CMD ["firebase", "emulators:start", "--only", "auth", "--project", "demo-careerwright", "--import", "./seed"]
