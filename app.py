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

from flask import Flask, request, abort
from waitress import serve
import logging
import json
import io
import os
import boto3
import base64
from flask_cors import CORS
from c2pa import *
from hashlib import sha256


# Load environment variable from .env file
from dotenv import dotenv_values

env_file_path = os.environ.get('ENV_FILE_PATH')
if env_file_path is not None:
    app_config = dotenv_values(env_file_path)
else:
    app_config = dotenv_values('.env')


# Configure logging
logging.basicConfig(level=logging.INFO)


# Run Flask app
app = Flask(__name__)
CORS(app)

# Load env vars with a given prefix into APP config
# By default, env vars with the `FLASK_`` prefix
# app.config.from_prefixed_env()

if 'USE_LOCAL_KEYS' in app_config and app_config['USE_LOCAL_KEYS'] == 'True':
    # local test certs for development
    print('Using local test certs for signing')

    private_key = open('tests/certs/ps256.pem', 'rb').read()
    cert_chain = open('tests/certs/ps256.pub', 'rb').read()
    encoded_cert_chain = base64.b64encode(cert_chain).decode('utf-8')
    signing_alg_str = 'PS256'
else:
    print('Using KMS for signing')

    kms_key_id = app_config['KMS_KEY_ID']
    cert_chain_path = app_config['CERT_CHAIN_PATH']

    cert_chain = open(cert_chain_path, 'rb').read()
    encoded_cert_chain = base64.b64encode(cert_chain).decode('utf-8')
    signing_alg_str = 'ES256'

    if 'RUN_MODE' in app_config and app_config['RUN_MODE'] == 'DEV':
        # For use with Localstack
        endpoint_url = app_config['AWS_ENDPOINT_URL']
        print(f'Running example in dev mode with endpoint: {endpoint_url}')
        region = app_config['AWS_REGION']
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


    print('Using KMS key: ' + kms_key_id)
    print('Using certificate chain: ' + cert_chain_path)

# Allow configuration of the timestamp URL
if 'TIMESTAMP_URL' in app_config and app_config['TIMESTAMP_URL']:
    timestamp_url = app_config['TIMESTAMP_URL']
else:
    timestamp_url = 'http://timestamp.digicert.com' # Default timestamp URL (change to None later?)

# todo: Get signing_alg_str from env when we support more algorithms
try:
    signing_alg = getattr(SigningAlg, signing_alg_str)
except AttributeError:
    raise ValueError(f"Unsupported signing algorithm: {signing_alg_str}")

@app.route("/attach", methods=["POST"])
def resize():
    request_data = request.get_data()
    content_type = request.headers.get('Content-Type', 'image/jpeg')  # Default to 'image/jpeg' if not provided

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

      signer = create_signer(kms_sign, signing_alg,
                            cert_chain, timestamp_url)

      result = io.BytesIO(b"")
      builder.sign(signer, content_type, io.BytesIO(request_data), result)

      return result.getvalue()
    except Exception as e:
        logging.error(e)
        abort(500, description=e)


# Uses KMS to sign
def kms_sign(data: bytes) -> bytes:
    hashed_data = sha256(data).digest()
    return kms.sign(KeyId=kms_key_id, Message=hashed_data, MessageType="DIGEST", SigningAlgorithm="ECDSA_SHA_256")["Signature"]


@app.route("/health", methods=["GET"])
def hello_world():
    return "<p>Healthy!</p>"


@app.route("/signer_data", methods=["GET"])
def signer_data():
    logging.info('Getting signer data')
    try:
        data = json.dumps({
            "alg": signing_alg_str,
            "timestamp_url": timestamp_url,
            "signing_url": f"{request.host_url}sign",
            "cert_chain": encoded_cert_chain
        })
    except Exception as e:
        logging.error(e)
        abort(500, description=e)
    return data


@app.route("/sign", methods=["POST"])
def sign():
    logging.info('Signing data')
    try:
        data = request.get_data()
        if private_key:
            return sign_ps256(data, private_key)
        else:
            return kms_sign(data)
    except Exception as e:
        logging.error(e)
        abort(500, description=e)

if __name__ == '__main__':
    app_config = None
    env_file_path = os.environ.get('ENV_FILE_PATH')
    if env_file_path is not None:
        print(f'Loading environment variables for server from {env_file_path} file defined in env vars')
        app_config = dotenv_values(env_file_path)

    port = 5000
    host = 'localhost'
    if app_config is not None:
        if 'APP_HOST_PORT' in app_config:
            port = app_config['APP_HOST_PORT']
        if 'APP_ENDPOINT' in app_config:
            host = app_config['APP_ENDPOINT']

    #app.run(debug=True)
    serve(app, host=host, port=port)
