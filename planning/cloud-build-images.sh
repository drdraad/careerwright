#!/usr/bin/env bash
# Cloud session only (planning/env-cloud.md): build the three local images through the session's
# HTTPS proxy. Containers can't reach the proxy or trust its CA, so each Dockerfile is copied to
# /tmp with the CA added as a build-time file and args (never ENV), built with --network host.
# The repository's Dockerfiles are unchanged. The stack starts with --no-build, so these images
# are what `make acceptance` runs. Rebuild after any code change before an acceptance run.
set -euo pipefail
cd "$(dirname "$0")/.."
P="${HTTPS_PROXY:?the session proxy is not set}"
mkdir -p /tmp/ccr-build
for spec in "backend/Dockerfile|backend|careerwright-l0/backend:local" \
            "apps/web/Dockerfile|apps/web|careerwright-l0/web:local" \
            "docker/auth/Dockerfile|docker/auth|careerwright-l0/auth-emulator:15.34.1"; do
  IFS='|' read -r df ctx tag <<<"$spec"
  out=/tmp/ccr-build/$(echo "$ctx" | tr / _).Dockerfile
  awk 'BEGIN{n=0} /^FROM /{print; n++; if (n==1) {print "COPY --from=ccr ca-bundle.crt /tmp/ccr-ca.crt"; print "ARG NODE_EXTRA_CA_CERTS=/tmp/ccr-ca.crt SSL_CERT_FILE=/tmp/ccr-ca.crt PIP_CERT=/tmp/ccr-ca.crt"}; next} {print}' "$df" > "$out"
  echo "== $tag"
  docker build -q --network host --build-context ccr=/root/.ccr \
    --build-arg HTTPS_PROXY="$P" --build-arg HTTP_PROXY="$P" \
    --build-arg https_proxy="$P" --build-arg http_proxy="$P" \
    -f "$out" -t "$tag" "$ctx"
done
