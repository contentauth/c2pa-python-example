#!/bin/bash -e

echo "Creating a test user in localstack"
awslocal --endpoint-url=http://localstack:4566 iam create-user --user-name test

echo "Creating test credentials in localstack and saving them to .env.local file"
awslocal --endpoint-url=http://localstack:4566 iam create-access-key --user-name test --output json | jq -r '.AccessKey | "AWS_ACCESS_KEY_ID=\(.AccessKeyId)\nAWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)"' >> .env.local

echo "Creating KMS key in localstack"
python setup.py create-key-and-csr 'CN=John Smith,O=C2PA Python Demo'

echo "Adding KMS_KEY_ID to .env.local"
cat config.json | jq -r '"KMS_KEY_ID=\(.kms_key_id)"' >> .env.local

# We should use some default values for the root CA certificate
echo "Creating root CA certificate"
openssl req -x509 \
    -days 1825 \
    -newkey rsa:2048 \
    -keyout rootCA.key \
    -passout pass:"" \
    -subj "/C=US/ST=CA/L=San Francisco/O=C2PA Python Demo/CN=John Smith" \
    -out rootCA.crt

echo "Signing the csr with the local cert"
openssl x509 -req \
    -CA rootCA.crt \
    -CAkey rootCA.key \
    -in kms-signing.csr \
    -out kms-signing.crt \
    -passin pass:"" \
    -days 365 \
    -copy_extensions copyall

echo "Copying kms-signing.crt to local_volume/kms-signing.crt"
cat kms-signing.crt rootCA.crt > chain.pem

echo "Copying chain.pem to local_volume/chain.pem"
cp chain.pem local_volume/chain.pem

echo "Adding CERT_CHAIN_PATH to .env.local"
echo "CERT_CHAIN_PATH=local_volume/chain.pem" >> .env.local

echo "Copying .env.local to local_volume/.env"
cp .env.local local_volume/.env
