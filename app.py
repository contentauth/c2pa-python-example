from flask import Flask, request
from c2pa import *
import boto3
import json
import io


app = Flask(__name__)

app.config.from_prefixed_env()
kms_key_id = app.config["KMS_KEY_ID"]
cert_chain_path = app.config["CERT_CHAIN_PATH"]

cert_chain = open(cert_chain_path, "rb").read()

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

    builder = Builder(manifest)

    signer = create_signer(sign, SigningAlg.PS256,
                           cert_chain, "http://timestamp.digicert.com")

    result = io.BytesIO(b"")
    builder.sign(signer, "image/jpeg", io.BytesIO(request_data), result)

    return result.getvalue()


def sign(data: bytes) -> bytes:
    return kms.sign(KeyId=kms_key_id, Message=data, MessageType="RAW", SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256")["Signature"]
