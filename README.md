# C2PA Python example

[This repository](https://github.com/contentauth/c2pa-python-example) is an example of a  simple app that accepts an uploaded JPEG image file, attaches a C2PA manifest, and signs it using a certificate.  The app uses the CAI Python library and the [Flask Python framework](https://flask.palletsprojects.com/en/3.0.x/).  The app implements only a backend REST endpoint; it does not have an HTML front-end, so you have to use something like `curl` to use it.

In addition to being an example of using the Python library, this app shows how to generate a certificate signing request (CSR), a message sent to a certificate authority to request the signing of a public key and associated information. 

Most commonly a CSR will be in a PKCS10 format. The contents of a CSR comprises a public key, as well as a common name, organization, city, state, country, and e-mail. Not all of these fields are required and will vary depending with the assurance level of your certificate. Together these fields make up the Certificate Signing Request (CSR). 

The CSR is signed by the applicant's private key; this proves to the CA that the applicant has control of the private key that corresponds to the public key included in the CSR. Once the requested information in a CSR passes a vetting process and domain control is established, the CA may sign the applicant's public key so that it can be publicly trusted. 

Before you can order an SSL Certificate, you will need to generate a CSR.

The app uses [Amazon Key Management Service (KMS)](https://aws.amazon.com/kms/) to create and control cryptographic keys. 

## Prerequisites

To build and run this app, you must install:

- Python 3.10.
- OpenSSL: See [OpenSSL](https://www.openssl.org/source/) for the source distribution or the [list of unofficial binary distributions](https://wiki.openssl.org/index.php/Binaries).

:::note:::
This app was developed and tested on macOS. It should also work on other operating systems, but on Windows you may have to take additional steps.
:::

## Process

### Step one: Install dependencies and get AWS credentials

Open a terminal window and follow these steps:

1. Set up [virtual environment](https://docs.python.org/3/library/venv.html) by entering these commands:
  ```
  python -m venv c2pa-env
  source c2pa-env/bin/activate
  ```
  These two commands do not produce any output.  
1. Install dependencies:
  ```
  pip install -r requirements.txt
  ```
  You will see this output in the terminal:
  ```
  Collecting c2pa-python==0.5.0
  ...
  ```
1. Follow the AWS documentation to [Configure the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) and add AWS credentials to `$HOME/.aws/credentials` as follows (key and token values not shown):
  ```
  [default]
  region=us-east-1
  aws_access_key_id=...
  aws_secret_access_key=...
  aws_session_token=...
  ```

### Step two: Generate CSR and get certificate

1. Enter this command to create a KMS key and generate a CSR:

```shell
python setup.py create-key-and-csr {CSR_SUBJECT}
```

For example:

```
python setup.py create-key-and-csr 'O=C2PA Python Demo'
```

TO DO: _Explain 'O=C2PA Python Demo' and what other identifiers could be used here_.

Response:
```
Created KMS key: cdd59e61-b6fa-4d95-b71f-8d6ae3f78e5e
```

1. Alternatively, if you have an existing KMS key that you that you want to use for signing, then execute this command:

```shell
python setup.py generate-certificate-request {KMS_KEY_ID} {CSR_SUBJECT}
```

For example:
```
python setup.py generate-certificate-request arn:aws:kms:us-east-1:12312323:key/123-123-123-8b8b-123 "C=US,ST=NY,L=NeW York,O=EXACT ORGANIZATION NAME,CN=EXACT ORGANIZATION NAME"
```
---

3. Create a self-signed certificate for use as a root CA:

```
$ openssl req -x509 -sha256 \
-days 1825 \
-newkey rsa:2048 \
-keyout rootCA.key \
-out rootCA.crt
```

You'll be prompted to enter and confirm a PEM passphrase.  Then you'll see this message:

```
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) [AU]: ...
State or Province Name (full name) [Some-State]: ...
Locality Name (eg, city) []: ...
Organization Name (eg, company) [Internet Widgits Pty Ltd]: ...
Organizational Unit Name (eg, section) []: ...
Common Name (e.g. server FQDN or YOUR name) []: ...
Email Address []: ...
```

4. Sign the CSR with the fake CA key Create certificate using fake CA cert

```
openssl x509 -req \
-CA rootCA.crt \
-CAkey rootCA.key \
-in kms-signing.csr \
-out kms-signing.crt \
-days 365 \
-copy_extensions copyall
```

Response:

```
Certificate request self-signature ok
subject=O=C2PA Python Demo
Enter pass phrase for rootCA.key:
```

1. Send CSR to CA to purchase Certificate

A document-signing certificate needs to be purchased from a CA. The process for
doing this will vary by CA.

### Step three: Create certificate chain

Create cert chain file PEM with cert issued by CA and CA Root certificate. For example, with the  self-signed certificate:

```
cat kms-signing.crt rootCA.crt > chain.pem
```

### Step four: Run the application 

1. Set the KMS_KEY_ID environment variable.

Edit `config.json` and get the value of `kms_key_id`. For example:

```
{"kms_key_id": "abc12361-b6fa-4d95-b71f-8d6ae3abc123"}
```

Set the environment variable like this (for example):

```
export KMS_KEY_ID=abc12361-b6fa-4d95-b71f-8d6ae3abc123
```

1. Run the application by entering this command:

```
FLASK_KMS_KEY_ID="$KMS_KEY_ID" FLASK_CERT_CHAIN_PATH="./chain.pem" flask run
```

Response:
```
Using KMS key: cdd59e61-b6fa-4d95-b71f-8d6ae3abc123
Using certificate chain: ./chain.pem
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

1. Upload and sign image: Use `curl` to upload an image file (the app works only with JPEGs) and have the app sign it by entering a command like this:

```
curl -X POST -T "<PATH_TO_JPEG>" -o <SIGNED_FILE_NAME>.jpg 'http://localhost:5000/attach'
```

For example:

```
curl -X POST -T ~/Desktop/test.jpeg -o signed.jpg 'http://localhost:5000/attach' 
```

In this example, the image with signed Content Credentials is saved to `signed.jpg`.
