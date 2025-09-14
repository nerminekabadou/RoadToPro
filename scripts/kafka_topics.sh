set -euo pipefail
# requires the redpanda container name from compose
docker exec -it docker-redpanda-1 \
  rpk topic create \
    esports.lol.schedule.upsert \
    esports.lol.match.status \
    esports.lol.result.upsert \