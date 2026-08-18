#!/bin/sh
#
# Description: Seeds the stand-in Gitea server with one org per source repository.
# Created by: Mustafa Can Caliskan
# Date: 2026-08-01
#
# Each stand-in "server" (bitbucket-a, bitbucket-b, gitlab-main) becomes a Gitea
# organization, so the three configured sources keep three distinct connection
# addresses and the routing between them stays meaningful. Every software unit
# directory becomes a repository with its version pushed as a tag, which is what
# MSD clones by.
#
# Idempotent: re-running against a seeded server changes nothing.

set -eu

GITEA_URL="${GITEA_URL:-http://gitea:3000}"
GITEA_USER="${GITEA_ADMIN_USER:-saag}"
GITEA_PASSWORD="${GITEA_ADMIN_PASSWORD:-saag-standin-password}"
GITEA_EMAIL="${GITEA_ADMIN_EMAIL:-saag@standin.local}"
TOKEN_NAME="${GITEA_TOKEN_NAME:-msd}"
SOURCE_ROOT="${SOURCE_ROOT:-/standins/data/source_repository}"
TOKEN_FILE="${GITEA_TOKEN_FILE:-/standins/git/token}"
GITEA_CONFIG="${GITEA_CONFIG:-/data/gitea/conf/app.ini}"

log() { echo "[git-seed] $*"; }

# Start Gitea via s6 so the config and database are initialized.
log "starting Gitea"
chown -R git:git /etc/s6
/bin/s6-svscan /etc/s6 &
S6_PID=$!

log "waiting for ${GITEA_URL}"
until curl -sf "${GITEA_URL}/api/healthz" >/dev/null 2>&1; do sleep 2; done

# Create admin user now that Gitea config and DB exist.
log "creating admin user '${GITEA_USER}'"
su-exec git /usr/local/bin/gitea admin user create \
  --config "${GITEA_CONFIG}" \
  --username "${GITEA_USER}" \
  --password "${GITEA_PASSWORD}" \
  --email "${GITEA_EMAIL}" \
  --admin 2>/dev/null || log "  user already present"

log "issuing an access token"
TOKEN=$(curl -sf -X POST "${GITEA_URL}/api/v1/users/${GITEA_USER}/tokens" \
  -u "${GITEA_USER}:${GITEA_PASSWORD}" \
  -H 'content-type: application/json' \
  -d "{\"name\":\"${TOKEN_NAME}-$(date +%s)\",\"scopes\":[\"write:organization\",\"write:repository\",\"write:user\"]}" \
  | sed -n 's/.*"sha1":"\([^"]*\)".*/\1/p')

if [ -z "${TOKEN}" ]; then
  log "could not obtain a token"
  exit 1
fi
printf '%s' "${TOKEN}" > "${TOKEN_FILE}" 2>/dev/null || log "token file not writable, continuing"

git config --global user.email "${GITEA_EMAIL}"
git config --global user.name "SaaG stand-in seed"
git config --global init.defaultBranch main

for server_path in "${SOURCE_ROOT}"/*; do
  [ -d "${server_path}" ] || continue
  server=$(basename "${server_path}")

  log "organization '${server}'"
  curl -sf -o /dev/null -X POST "${GITEA_URL}/api/v1/orgs" \
    -H "Authorization: token ${TOKEN}" \
    -H 'content-type: application/json' \
    -d "{\"username\":\"${server}\"}" || log "  already present"

  for unit_path in "${server_path}"/*; do
    [ -d "${unit_path}" ] || continue
    versioned=$(basename "${unit_path}")
    unit=$(echo "${versioned}" | sed -E 's/_[0-9]+\.[0-9]+.*$//')
    version=$(echo "${versioned}" | sed -E "s/^${unit}_//")

    log "  repository '${server}/${unit}' at ${version}"
    curl -sf -o /dev/null -X POST "${GITEA_URL}/api/v1/orgs/${server}/repos" \
      -H "Authorization: token ${TOKEN}" \
      -H 'content-type: application/json' \
      -d "{\"name\":\"${unit}\",\"auto_init\":false}" || log "    already present"

    work=$(mktemp -d)
    cp -R "${unit_path}/." "${work}/"
    (
      cd "${work}"
      git init -q
      git add -A
      git commit -q -m "${unit} ${version}"
      git tag "${version}"
      git push -q --force "${GITEA_URL%//*}//${GITEA_USER}:${TOKEN}@${GITEA_URL#*//}/${server}/${unit}.git" \
        HEAD:refs/heads/main "refs/tags/${version}" 2>/dev/null \
        || log "    already pushed"
    )
    rm -rf "${work}"
  done
done

log "done"
wait $S6_PID
