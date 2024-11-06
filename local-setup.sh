!#/bin/bash -e

echo "Creating a test user in localstack"
awslocal --endpoint-url=http://localstack:4566 iam create-user --user-name test

echo "Creating test credentials in localstack and saving them to .env.local file"
awslocal --endpoint-url=http://localstack:4566 iam create-access-key --user-name test \
    | jq -r '.AccessKey | "AWS_ACCESS_KEY_ID=\(.AccessKeyId)\nAWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)"' \
    >> .env.local
