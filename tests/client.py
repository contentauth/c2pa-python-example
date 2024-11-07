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

import argparse
import os
import requests
import json
import c2pa
from PIL import Image
import io
import base64

from dotenv import dotenv_values

def get_signer_data_uri():
    env_file_path = os.environ.get('CLIENT_ENV_FILE_PATH')
    uri = 'http://127.0.0.1:5000/signer_data'
    if env_file_path is not None:
        print(f'## Loading environment variables for client from {env_file_path} file defined in env vars')
        app_config = dotenv_values(env_file_path)

        host_port = app_config['CLIENT_HOST_PORT']
        if 'CLIENT_HOST_PORT' in host_port:
            host_port = app_config['CLIENT_HOST_PORT']
            uri = f'http://127.0.0.1:{host_port}/signer_data'

        print(f'Using default client URI {uri} (from env variables)')
    else:
        print(f'Using default client URI {uri}')

    return uri

# Generate a sign function from signer data returned by the url
def get_remote_signer(uri: str) -> c2pa.CallbackSigner:
    response = requests.get(uri)
    if response.status_code == 200:
        json_data = response.json()
        certs = json_data["cert_chain"]
        # Convert certs string to bytes using UTF-8 encoding
        certs = base64.b64decode(certs.encode("utf-8"))
        cert_chain = open("tests/certs/ps256.pub","rb").read()
        assert certs == cert_chain
        alg_str = json_data["alg"].upper()
        try:
            alg = getattr(c2pa.SigningAlg, alg_str)
        except AttributeError:
            raise ValueError(f"Unsupported signing algorithm: {alg_str}")
    else:
        raise ValueError(f"Failed to get signer data: {response.status_code} {response.text}")

    #sign = lambda data: requests.post(json_data["signing_url"], data=data).content
    def remote_sign(data):
        try:
            response = requests.post(json_data["signing_url"], data=data)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error during signing: {e}")
            print(f"Response: {response.text}")
            raise

    return c2pa.create_signer(remote_sign, alg, certs, json_data["timestamp_url"])

# Generate a thumbnail from a file
def make_thumbnail(file: str) -> io.BytesIO:
    with Image.open(file) as img:
        img.thumbnail((512, 512))
        buffer = io.BytesIO()
        img.save(buffer, "JPEG")
        buffer.seek(0)
        return buffer


manifest = json.dumps({
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

ingredient_json = {
    "relationship": "parentOf",
    "title": "",
    "thumbnail": {
        "format": "image/jpeg",
        "identifier": "thumbnail"
    }
}

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Sign files with C2PA.")
parser.add_argument("files", metavar="F", type=str, nargs="+", help="Files to be signed")
parser.add_argument("-o", "--output", type=str, required=True, help="Output directory")

args = parser.parse_args()

# Ensure the output directory exists
os.makedirs(args.output, exist_ok=True)

uri = get_signer_data_uri()
signer = get_remote_signer(uri)

# Sign each file and write to the output directory
for file in args.files:
    output_file = os.path.join(args.output, os.path.basename(file))
    builder = c2pa.Builder(manifest)
    ingredient_json["title"] = os.path.basename(file)
    builder.add_ingredient_file(ingredient_json, file)
    builder.add_resource("thumbnail", make_thumbnail(file))
    builder.sign_file(signer, file, output_file)
    print(f"Signed {file} and saved to {output_file}")
