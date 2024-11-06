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
import dotenv

from c2pa import *
from hashlib import sha256



# Load environment variable from .env file
from dotenv import dotenv_values
app_config = dotenv_values(".env")



# Configure logging
logging.basicConfig(level=logging.INFO)



# Run Flask app
app = Flask(__name__)


# Load env vars with a given prefix into APP config
# By default, env vars with the `FLASK_`` prefix
# app.config.from_prefixed_env()



if 'USE_LOCAL_KEYS' in app_config and app_config['USE_LOCAL_KEYS'] == 'True':
    # local test certs for development
    print("## Using local test certs")

    private_key = open("tests/certs/ps256.pem","rb").read()
    cert_chain = open("tests/certs/ps256.pub","rb").read()
else:
    print("## Using KMS")

    kms_key_id = app_config["KMS_KEY_ID"]
    cert_chain_path = app_config["CERT_CHAIN_PATH"]

    cert_chain = open(cert_chain_path, "rb").read()

    run_mode = app_config['RUN_MODE']

    if run_mode == 'DEV':
        # For use with Localstack
        endpoint_url = app_config['AWS_ENDPOINT']
        print(f'Running example in dev mode with endpoint: {endpoint_url}')
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


    print("Using KMS key: " + kms_key_id)
    print("Using certificate chain: " + cert_chain_path)


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

    try:
      builder = Builder(manifest)

      signer = create_signer(sign, SigningAlg.ES256,
                            cert_chain, "http://timestamp.digicert.com")

      result = io.BytesIO(b"")
      builder.sign(signer, "image/jpeg", io.BytesIO(request_data), result)

      return result.getvalue()
    except Exception as e:
        logging.error(e)
        return "Error"


def sign(data: bytes) -> bytes:
    hashed_data = sha256(data).digest()
    # Uses KMS to sign
    return kms.sign(KeyId=kms_key_id, Message=hashed_data, MessageType="DIGEST", SigningAlgorithm="ECDSA_SHA_256")["Signature"]


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
def signer(data: bytes):
    logging.info("Signing data")
    data = request.get_data()
    if private_key:
        return sign_ps256(data, private_key)
    else:
        sign(data)


if __name__ == '__main__':
    app.run(debug=True)
