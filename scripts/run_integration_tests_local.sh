# scripts/test-setup.sh
#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/.."

docker-compose -f docker-compose.test.yml up -d
echo "Waiting for services..."
sleep 5
poetry run pytest tests/integration/
docker-compose -f docker-compose.test.yml down