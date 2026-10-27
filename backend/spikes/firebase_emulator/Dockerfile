# Firebase Auth emulator only, for the Sprint 0 arm64 check (S0.1). The Auth emulator is
# implemented in Node inside firebase-tools; no Java runtime is installed or needed.
#
# firebase.json binds 0.0.0.0 *inside* the container so a published port can reach it. Publish
# it on the host loopback only (Global Constraint 9), as the Sprint 0 check did:
#   docker run --rm -p 127.0.0.1:59099:9099 nessa-spike/firebase-auth-emulator:15.34.1
FROM node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205

ENV PNPM_HOME=/opt/pnpm PATH=/opt/pnpm:$PATH
RUN corepack enable \
    && corepack prepare pnpm@10.33.2 --activate \
    && pnpm add --global firebase-tools@15.34.1 \
    && useradd --create-home emulator

USER emulator
WORKDIR /home/emulator
COPY --chown=emulator firebase.json .
EXPOSE 9099
# A `demo-` project ID needs no Google credentials and cannot reach real Firebase services.
CMD ["firebase", "emulators:start", "--only", "auth", "--project", "demo-nessa"]
