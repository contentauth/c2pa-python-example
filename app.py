# Copyright 2024 Adobe. All rights reserved.
# This file is licensed to you under the Apache License,
# Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
# or the MIT license (http://opensource.org/licenses/MIT),
# at your option.
# Unless required by applicable law or agreed to in writing,
# this software is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR REPRESENTATIONS OF ANY KIND, either express or
# implied. See the LICENSE-MIT and LICENSE-APACHE files for the
# specific language governing permissions and limitations under
# each license.

from flask import Flask, request
import logging
import json
import io
import boto3
import base64

from c2pa import *
from hashlib import sha256


# Load env conf values from .env file
from dotenv import dotenv_values
app_config = dotenv_values(".env")
run_mode = app_config['RUN_MODE']


# Configure logging
logging.basicConfig(level=logging.INFO)


# Run Flask app
app = Flask(__name__)


# Loads env vars with a given prefix into APP config
# By default, env vars with the `FLASK_`` prefix
app.config.from_prefixed_env()

# Load KMS key ID from local env
# `create_kms_key` from the setup.py script created a key
# with key spec ECC_NIST_P256
kms_key_id = app.config["KMS_KEY_ID"]
# Load the certificate chain from local env (chain.pem file)
cert_chain_path = app.config["CERT_CHAIN_PATH"]
# Open certificate chain path file
cert_chain = open(cert_chain_path, "rb").read()

if run_mode == 'DEV':
    endpoint_url = app_config['AWS_ENDPOINT']
    print(f'Running example in AWS dev mode with endpoint: {endpoint_url}')
    region = app_config['REGION']
    aws_access_key_id = app_config['AWS_ACCESS_KEY_ID']
    aws_secret_access_key = app_config['AWS_SECRET_ACCESS_KEY']
    session = boto3.Session(region_name=region,
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
    kms = session.client('kms',
                        endpoint_url=endpoint_url,
                        region_name=region,
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key)
else:
    session = boto3.Session()
    kms = session.client('kms')


print("Using KMS key with ID: " + kms_key_id)
print("Using certificate chain: " + cert_chain_path)

private_key = open("chain.pem","rb").read()
print("Private key loaded into memory")


def sign(data: bytes) -> bytes:
    print(f"Signing data using KMS key id {kms_key_id}")
    hashed_data = sha256(data).digest()

    result = kms.sign(KeyId=kms_key_id, Message=hashed_data, MessageType="DIGEST", SigningAlgorithm="ECDSA_SHA_256")
    # Response syntax
    # {
    # 'KeyId': 'string',
    #
    # The signature value is a DER-encoded object as defined by ANSI X9.62-2005 and RFC 3279 Section 2.2.3.
    # When you use the HTTP API (or the Amazon Web Services CLI), the signature value is Base64-encoded.
    # 'Signature': b'bytes',
    #
    # 'SigningAlgorithm': 'ECDSA_SHA_256'
    # }
    return result["Signature"]


# API Routes
@app.route("/attach", methods=["POST"])
def resize():
    request_data = request.get_data()

    manifest = json.dumps({
        "title": "image.jpg",
        "format": "image/jpeg",
        "claim_generator_info": [
            {
                "name": "c2pa python example test",
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

    # the signer here take the whole certificates chain
    signer = create_signer(sign,
                            SigningAlg.ES256,
                            cert_chain,
                            "http://timestamp.digicert.com")

    result = io.BytesIO(b"")
    builder.sign(signer, "image/jpeg", io.BytesIO(request_data), result)

    return result.getvalue()


@app.route("/signer_data", methods=["GET"])
def signer_data():
    logging.info("Getting signer data")
    try:
        data = json.dumps({
            "alg": "Ps256",
            "timestamp_url": "http://timestamp.digicert.com",
            "signing_url": "http://localhost:5000/sign",
            "cert_chain": base64.b64encode(cert_chain).decode('utf-8'),
        })
    except Exception as e:
        logging.error(e)
    return data


@app.route("/sign", methods=["POST"])
def signer():
    print("## Signer called")
    request_data = request.get_data()
    print("## Read request data")

    result = io.BytesIO(b"")
    try:
      print("Using KMS for signing")
      sign(io.BytesIO(request_data))
    except Exception as e:
        logging.error(e)

    return result
