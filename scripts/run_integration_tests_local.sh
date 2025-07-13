# scripts/test-setup.sh
#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/.."

docker-compose -f docker-compose.test.yml up -d
poetry run pytest tests/integration/
docker-compose -f docker-compose.test.yml down

# remove the test result file if it exists
if [ -f "grobid_test_result.xml" ]; then
    rm grobid_test_result.xml
fi