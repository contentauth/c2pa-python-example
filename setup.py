#!/usr/bin/env python3

import arguably

import boto3
import yaml

from pyasn1.codec.der import decoder, encoder
from pyasn1.type import univ
import pyasn1_modules.pem
import pyasn1_modules.rfc2986
import pyasn1_modules.rfc2314
import hashlib
import base64
import textwrap
import sys
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.x509 import Name, CertificateSigningRequestBuilder, NameAttribute, SignatureAlgorithmOID, ExtensionType, OID_TIME_STAMPING, OID_CODE_SIGNING, OID_KEY_USAGE, OID_EXTENDED_KEY_USAGE, OID_BASIC_CONSTRAINTS
from cryptography.hazmat.primitives.asymmetric import ec
from pathlib import Path
import json


start_marker = '-----BEGIN CERTIFICATE REQUEST-----'
end_marker = '-----END CERTIFICATE REQUEST-----'
hash_alg = 'ECDSA_SHA_256'
# This magic string corresponds to [SignatureAlgorithmOID.ECDSA_WITH_SHA256][^1].
#
# [^1]: https://cryptography.io/en/latest/x509/reference/#cryptography.x509.oid.SignatureAlgorithmOID.ECDSA_WITH_SHA256
sign_oid = '1.2.840.10045.4.3.2'
csr_file = 'kms-signing.csr'
config_file = 'config.json'

kms = boto3.client('kms')

def create_kms_key():
    response = kms.create_key(
        Description='C2PA Python KMS Demo Key',
        KeyUsage='SIGN_VERIFY',
        KeySpec='ECC_NIST_P256',
    )

    key_id = response['KeyMetadata']['KeyId']
    print(f'Created KMS key: {key_id}')
    print(f'Consider setting an environment variable: `export KMS_KEY_ID={key_id}`')

    open('config.json', 'wt').write(json.dumps({'kms_key_id': key_id}))

    return key_id


@arguably.command
def create_key_and_csr(subject):
    key_id = create_kms_key()
    generate_certificate_request(key_id, subject)


@arguably.command
def generate_certificate_request(kms_key: str, subject: str):

    kms = boto3.client('kms')

    key_obj = kms.describe_key(KeyId=kms_key)

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

    f = open(csr_file, "w")
    f.write(build_output(csr_request))
    f.close()


def build_output(csr):
    out = start_marker + '\n'
    b64 = base64.b64encode(encoder.encode(csr)).decode('ascii')
    for line in textwrap.wrap(b64, width=64):
        out += line+'\n'
    out += end_marker
    return out


if __name__ == "__main__":
    arguably.run()
