#!/bin/sh
#
# Container command for the mock Gitea: starts Gitea, then seeds one org with
# one repo per fixture dir under ./seed (named <unit>_<version>), each pushed
# as a single commit on main plus a tag for the version.

set -eu

GITEA_URL="http://gitea:3000"
GITEA_USER="dsm"
GITEA_PASSWORD="dsm"
GITEA_EMAIL="dsm@standin.local"
ORG="dsm-src"
SEED_ROOT="/opt/dsm/seed"

log() { echo "[dsm-git-seed] $*"; }
api() { curl -sf -o /dev/null -u "$GITEA_USER:$GITEA_PASSWORD" -H 'content-type: application/json' -d "$2" "$GITEA_URL/api/v1/$1"; }

log "starting Gitea"
s6-svscan /etc/s6 &
until curl -sf "$GITEA_URL/api/healthz" >/dev/null; do sleep 2; done

log "admin user '$GITEA_USER'"
su-exec git gitea admin user create --admin --username "$GITEA_USER" --password "$GITEA_PASSWORD" --email "$GITEA_EMAIL" \
    || log "  already present"

log "organization '$ORG'"
api orgs "{\"username\":\"$ORG\"}" || log "  already present"

git config --global user.name "dsm seed"
git config --global user.email "$GITEA_EMAIL"

for dir in "$SEED_ROOT"/*/; do
    dir=${dir%/}
    name=$(basename "$dir")
    unit=${name%_*}
    version=${name##*_}

    log "repository '$ORG/$unit' at $version"
    api "orgs/$ORG/repos" "{\"name\":\"$unit\",\"private\":true}" || log "  already present"

    work=$(mktemp -d)
    cp -R "$dir/." "$work"
    git -C "$work" init -q -b main
    git -C "$work" add -A
    git -C "$work" commit -q -m "$unit $version"
    git -C "$work" tag "$version"
    git -C "$work" push -q --force "http://$GITEA_USER:$GITEA_PASSWORD@${GITEA_URL#http://}/$ORG/$unit.git" main "$version"
    rm -rf "$work"
done

log "done"
wait
