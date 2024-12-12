#!/usr/bin/env python3

import arguably

import boto3

from pyasn1.codec.der import decoder, encoder
from pyasn1.type import univ
import pyasn1_modules.pem
import pyasn1_modules.rfc2986
import pyasn1_modules.rfc2314
import hashlib
import base64
import textwrap
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.x509 import Name, CertificateSigningRequestBuilder, NameAttribute, SignatureAlgorithmOID, ExtensionType, OID_TIME_STAMPING, OID_CODE_SIGNING, OID_KEY_USAGE, OID_EXTENDED_KEY_USAGE, OID_BASIC_CONSTRAINTS
from cryptography.hazmat.primitives.asymmetric import ec
from pathlib import Path
import json


# Load environment variable from .env file
from dotenv import dotenv_values, find_dotenv, set_key

# Set constants
start_marker = '-----BEGIN CERTIFICATE REQUEST-----'
end_marker = '-----END CERTIFICATE REQUEST-----'
hash_alg = 'ECDSA_SHA_256'
# This magic string corresponds to [SignatureAlgorithmOID.ECDSA_WITH_SHA256][^1].
#
# [^1]: https://cryptography.io/en/latest/x509/reference/#cryptography.x509.oid.SignatureAlgorithmOID.ECDSA_WITH_SHA256
sign_oid = '1.2.840.10045.4.3.2'
csr_file = 'kms-signing.csr'
json_config_filename = 'config.json'


def read_env_params(env_file_path=None):
  if env_file_path is not None:
      print(f'Loading environment variables from: {env_file_path}')
      app_config = dotenv_values(dotenv_path=env_file_path)
  else:
    print('No env file path received as param. Looking at other possible locations...')

    env_file_path = os.environ.get('ENV_FILE_PATH')
    if env_file_path is not None:
        print(f'Loading environment variables from {env_file_path} file defined in env vars')
        app_config = dotenv_values(env_file_path)
    else:
        print('Loading env variables values from default .env file')
        app_config = dotenv_values(".env")

  kms = None
  run_mode = app_config['RUN_MODE']

  if 'RUN_MODE' in app_config and run_mode == 'DEV':
      # Run in dev/local mode (eg. with LocalStack)
      endpoint_url = app_config['AWS_ENDPOINT_URL']
      print(f'Running example setup in dev mode with endpoint: {endpoint_url}')

      region = app_config['AWS_REGION']
      aws_access_key_id = app_config['AWS_ACCESS_KEY_ID']
      aws_secret_access_key = app_config['AWS_SECRET_ACCESS_KEY']

      # Use variables from .env file as parameter values
      try:
        kms = boto3.client('kms',
                            endpoint_url=endpoint_url,
                            region_name=region,
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
      except Exception as e:
        print('Error during KMS client setup in dev mode')
        print(e)
        raise Exception('KMS dev setup failed: Error during KMS client setup in dev mode')

  else:
      # Example setup for use with AWS credentials setup (no LocalStack use)
      kms = boto3.client('kms')

  return kms


def create_kms_key(env_file_path=None):
    kms = None
    if env_file_path is not None:
        print(f'Using env variables from {env_file_path} to build environment and KMS client')
        kms = read_env_params(env_file_path)
    else:
        print(f'Using default environment to build environment and KMS client')
        kms = read_env_params()


    try:
      if kms is not None:
        response = kms.create_key(
            Description='C2PA Python KMS Demo Key',
            KeyUsage='SIGN_VERIFY',
            KeySpec='ECC_NIST_P256',
        )
      else:
        print('Error during KMS client setup')
        raise Exception('No KMS key id generated (Error during KMS client setup)')
    except Exception as e:
      print(f'Error during KMS key creation: {e}')
      raise Exception('No KMS key id generated (Error during KMS key creation)')

    key_id = response['KeyMetadata']['KeyId']
    print(f'Created KMS key: {key_id}')
    print(f'Consider setting an environment variable: `export KMS_KEY_ID={key_id}`')

    # TODO-TMN: Put kms_key_id in local env file too
    open(json_config_filename, 'wt').write(json.dumps({'kms_key_id': key_id}))

    try:
      if env_file_path is not None:
        # Use defined env file path
        set_key(env_file_path, "KMS_KEY_ID", key_id)
        
      else:
        # Is there an env file location defined in the env vars?
        env_file_to_use = os.environ.get('ENV_FILE_PATH')
        print(f'KMS_KEY_ID value updated in .env file set as parameter: {env_file_to_use}')
        if env_file_to_use is None:
            # Env file defined in env vars, we'll place the key there
            env_file_to_use = find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=False)
            print(f'KMS_KEY_ID value updated in found default .env file: {env_file_to_use}')
        else:
            print(f'KMS_KEY_ID value updated in env file set in environment variables: {env_file_to_use}')
        # Update local env file with KMS_KEY_ID
        set_key(env_file_to_use, "KMS_KEY_ID", key_id)
    except:
      print("KMS_KEY_ID value update: Could not update env file to include KMS_KEY_ID of generated KMS key")

    return key_id

# Example call: python setup.py create-key-and-csr 'CN=John Smith,O=C2PA Python Demo' './my-env-file.env'
@arguably.command
def create_key_and_csr(subject, env_file_path=None):
    key_id = create_kms_key(env_file_path)

    if key_id is not None:
        print(f'Generating KMS key with subject: {subject}')
        generate_certificate_request(key_id, subject, env_file_path)
    else:
        print('Error during KMS key ID generation')
        raise Exception('No KMS key id generated')


@arguably.command
def generate_certificate_request(kms_key: str, subject: str, env_file_path=None):
    if env_file_path is not None:
        print(f'Using env variables from {env_file_path} to build environment and KMS client')
        kms = read_env_params(env_file_path)
    else:
        print(f'Using default environment to build environment and KMS client')
        kms = read_env_params()

    key_obj = kms.describe_key(KeyId=kms_key)
    # Show structure of key object
    # print(key_obj)

    # Get public key from KMS
    response = kms.get_public_key(KeyId=kms_key)

    pubkey_der = response['PublicKey']

    # Create temporary private key
    private_key = ec.generate_private_key(
        ec.SECP256R1()
    )

    # Setup CSR file Subject
    subject = Name.from_rfc4514_string(subject)
    csr_info = CertificateSigningRequestBuilder().subject_name(
        subject
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            x509.ExtendedKeyUsageOID.EMAIL_PROTECTION,
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256()).tbs_certrequest_bytes

    csr_info = decoder.decode(
        csr_info, asn1Spec=pyasn1_modules.rfc2986.CertificationRequestInfo())[0]

    pub = decoder.decode(
        pubkey_der, pyasn1_modules.rfc2314.SubjectPublicKeyInfo())[0]

    csr_info['subjectPKInfo'] = pub

    der_bytes = encoder.encode(csr_info)
    digest = hashlib.new('sha256')
    digest.update(der_bytes)
    digest = digest.digest()

    response = kms.sign(KeyId=kms_key, Message=digest,
                        MessageType='DIGEST', SigningAlgorithm=hash_alg)
    signature = response['Signature']

    sigAlgIdentifier = pyasn1_modules.rfc2314.SignatureAlgorithmIdentifier()
    sigAlgIdentifier.setComponentByName(
        'algorithm',
        univ.ObjectIdentifier(sign_oid)
    )

    csr_request = pyasn1_modules.rfc2986.CertificationRequest()

    csr_request.setComponentByName('certificationRequestInfo', csr_info)
    csr_request.setComponentByName(
        'signatureAlgorithm', sigAlgIdentifier)
    csr_request.setComponentByName(
        'signature', univ.BitString.fromOctetString(signature))
    build_output(csr_request)

    # TODO-TMN: Keep CSR request filepath at hand
    with open(csr_file, "w") as f:
        f.write(build_output(csr_request))


def build_output(csr):
    out = start_marker + '\n'
    b64 = base64.b64encode(encoder.encode(csr)).decode('ascii')
    for line in textwrap.wrap(b64, width=64):
        out += line+'\n'
    out += end_marker
    return out


if __name__ == "__main__":
    arguably.run()
