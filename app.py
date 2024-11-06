from flask import Flask, request
from c2pa import *
from hashlib import sha256
import boto3
import json
import io


# Load environment variable from .env file
from dotenv import dotenv_values
app_config = dotenv_values(".env")
run_mode = app_config['RUN_MODE']


# Run Flask app
app = Flask(__name__)


# Load env vars with a given prefix into APP config
# By default, env vars with the `FLASK_`` prefix
app.config.from_prefixed_env()

# Load KMS key ID from local Flask app environment
# `create_kms_key` from the setup.py script created a key with key spec ECC_NIST_P256
kms_key_id = app.config["KMS_KEY_ID"]

# Load the certificate chain from local Flask app environment (chain.pem file)
cert_chain_path = app.config["CERT_CHAIN_PATH"]

cert_chain = open(cert_chain_path, "rb").read()


if run_mode == 'DEV':
    # Development setup (eg. with LocalStack)
    endpoint_url = app_config['AWS_ENDPOINT']
    print(f'Running example in dev mode with endpoint: {endpoint_url}')

    region = app_config['REGION']
    aws_access_key_id = app_config['AWS_ACCESS_KEY_ID']
    aws_secret_access_key = app_config['AWS_SECRET_ACCESS_KEY']

    # Use variables from .env file
    session = boto3.Session(region_name=region,
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
    kms = session.client('kms',
                        endpoint_url=endpoint_url,
                        region_name=region,
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key)
else:
    # Example setup for use with AWS credentials setup (no LocalStack use)
    session = boto3.Session()
    kms = session.client('kms')


print(f'Using KMS key: {kms_key_id}')
print(f'Using certificate chain from {cert_chain_path}')


@app.route("/attach", methods=["POST"])
def resize():
    request_data = request.get_data()

    manifest = json.dumps({
        "title": "image.jpg",
        "format": "image/jpeg",
        "claim_generator_info": [
            {
                "name": "c2pa test",
                "version": "0.0.1"
            }
        ],
        "assertions": [
            {
                "label": "c2pa.actions",
                "data": {
                    "actions": [
                        {
                            "action": "c2pa.edited",
                            "softwareAgent": {
                                "name": "C2PA Python Example",
                                "version": "0.1.0"
                            }
                        }
                    ]
                }
            }
        ]
    })

    builder = Builder(manifest)

    # The signer is created with a certificate chain
    signer = create_signer(sign, SigningAlg.ES256,
                           cert_chain, "http://timestamp.digicert.com")

    result = io.BytesIO(b"")
    # The result parameter is used to pass around the result of the builder.sign function
    builder.sign(signer, "image/jpeg", io.BytesIO(request_data), result)

    return result.getvalue()


def sign(data: bytes) -> bytes:
    hashed_data = sha256(data).digest()
    # Uses KMS to sign
    return kms.sign(KeyId=kms_key_id, Message=hashed_data, MessageType="DIGEST", SigningAlgorithm="ECDSA_SHA_256")["Signature"]
