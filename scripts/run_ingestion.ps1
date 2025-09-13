# Stop script on first error
$ErrorActionPreference = "Stop"

# Set environment variables
$env:PYTHONUNBUFFERED = "1"

# Set DATA_DIR to 'data' if it's not already set
if (-not $env:DATA_DIR) {
    $env:DATA_DIR = "data"
}

# Commented out environment variables
# $env:PROM_PORT = "9108"
# $env:PANDASCORE_TOKEN = "..."

# Run the main Python module
uv run  main.py
