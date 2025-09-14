# Stop script on first error
$ErrorActionPreference = "Stop"

# Execute the rpk command to create topics
docker exec -it redpanda rpk topic create esports.lol.schedule.upsert esports.lol.match.status esports.lol.result.upsert
