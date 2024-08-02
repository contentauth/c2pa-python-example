# c2pa-python-example

## 1. Setup AWS Credentials
https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html


## 2a. Create CSR request for KMS key

If you have an existing KMS key that you'll be using for signing, then execute:

```shell
python setup.py generate-certificate-request {KMS_KEY_ID} {CSR_SUBJECT}

ex. python setup.py generate-certificate-request arn:aws:kms:us-east-1:12312323:key/123-123-123-8b8b-123 "C=US,ST=NY,L=NeW York,O=EXACT ORGANIZATION NAME,CN=EXACT ORGANIZATION NAME"
```

## 2b. KMS Key and CSR request

If you'd like to create a KMS key and a CSR at the same time, then execute:

```shell
python setup.py create-key-and-csr {CSR_SUBJECT}
```

## 3a. Send CSR to CA to purchase Certificate

A document-signing certificate needs to be purchased from a CA. The process for
doing this will vary by CA.

## 3b. Use a self-signed certificate

For demonstration purposes, a self-signed certificate can be used. The resulting
manifests won't be trusted, but it'll get the application running.

```
# Create a fake root CA key/certificate
$ openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout rootCA.key -out rootCA.crt
# Sign the CSR with the fake CA key
$ openssl x509 -req -CA rootCA.crt -CAkey rootCA.key -in kms-signing.csr -out kms-signing.crt -days 365 -copy_extensions copyall
```

## 4. Create cert chain

Create cert chain file PEM with cert issued by CA and CA Root certificate. In
the self-signed certificate example, this might be:

```
$ cat kms-signing.crt rootCA.crt > chain.pem
```

## 5. Run Application

```shell
FLASK_KMS_KEY_ID={KMS_KEY} FLASK_CERT_CHAIN_PATH={CERT_CHAIN_PATH} flask run
```

Send a JPEG to `http://localhost:5000/attach` to have it signed.

```
$ curl -X POST -T "<path to your jpg>" -o attached.jpg 'http://localhost:5000/attach'
```
