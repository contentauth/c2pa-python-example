# C2PA Python example

## Overview 

[This repository](https://github.com/contentauth/c2pa-python-example) is an example of a simple application that accepts an uploaded JPEG image file, attaches a C2PA manifest, and signs it using a certificate.  The app uses the CAI Python library and the [Flask Python framework](https://flask.palletsprojects.com/en/3.0.x/) to implement a back-end REST endpoint; it does not have an HTML front-end, so you have to use something like `curl` to access it.

The app uses [Amazon Key Management Service (KMS)](https://aws.amazon.com/kms/) to create and control cryptographic keys and the [AWS SDK for Python (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html) to call KMS.

### About CSRs

In addition to being an example of using the Python library, this app shows how to generate a certificate signing request (CSR), a message sent to a certificate authority (CA) to request the signing of a public key and associated information. 

A CSR comprises a public key, as well as a common name, organization, city, state, country, and e-mail address. Not all of these fields are required and will vary depending with the assurance level of your certificate. 

You sign the CSR with your private key; this proves to the CA that you have control of the private key that corresponds to the public key included in the CSR. Once the requested information in a CSR passes a vetting process and domain control is established, the CA may sign the public key to indicate that it can be publicly trusted. 

## Prerequisites

To build and run this app, you must install:

- Python 3.10.
- OpenSSL: See [OpenSSL](https://www.openssl.org/source/) for the source distribution or the [list of unofficial binary distributions](https://wiki.openssl.org/index.php/Binaries).  Make sure you have a recent version.

You must also have an AWS account and be able to get standard AWS access credentials so you can use KMS.

NOTE: This app was developed and tested on macOS. It should also work on other operating systems, but on Windows you may have to take additional steps.

## Install dependencies

Open a terminal window and follow these steps:

1. Set up [virtual environment](https://docs.python.org/3/library/venv.html) by entering these commands:
    ```
    python -m venv c2pa-env
    source c2pa-env/bin/activate
    ```
    In the first command, `c2pa-env` is the name of the virtual environment; you can use another name if you wish. These two commands do not produce any output in the terminal window, but your prompt will change to `(c2pa-env)` or whatever environment name you chose.  
1. Install dependencies:
    ```
    cd c2pa-python-example
    pip install -r requirements.txt
    ```
    You will see this output in the terminal:
    ```
    Collecting c2pa-python==0.5.0
    ...
    ```


 ## Set AWS credentials

Follow the AWS documentation to [Configure the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) and add AWS credentials to `$HOME/.aws/credentials` as follows (key and token values not shown):
```
[default]
region=us-east-1
aws_access_key_id=...
aws_secret_access_key=...
aws_session_token=...
```

## Get KMS key and CSR

### Use an existing KMS key

If you have an existing KMS key that you want to use for signing, follow these steps to generate a CSR:

1. Set the KMS_KEY_ID environment variable to the value of the KMS key; for example:
    ```
    export KMS_KEY_ID=abc12361-b6fa-4d95-b71f-8d6ae3abc123
    ```
1. Then run this command to generate a certificate request 
    ```shell
    python setup.py generate-certificate-request {KMS_KEY_ID} {CSR_SUBJECT}
    ```
    For example:
    ```
    python setup.py generate-certificate-request \
    arn:aws:kms:us-east-1:12312323:key/123-123-123-8b8b-123 \
    "C=US,ST=NY,L=NeW York,O=EXACT ORGANIZATION NAME,CN=EXACT ORGANIZATION NAME"
    ```

### Generate a KMS key and CSR

If you don't have an existing KMS key, follow these steps to generate a KMS key and CSR:

1. Enter this command to create a KMS key and generate a CSR:
    ```shell
    python setup.py create-key-and-csr {CSR_SUBJECT}
    ```
    Where `{CSR_SUBJECT}` is an [RFC 4514](https://datatracker.ietf.org/doc/html/rfc4514.html) string representation of a distinguished name (DN) identifying the applicant. 
    For example:
    ```
    python setup.py create-key-and-csr 'CN=John Smith,O=C2PA Python Demo'
    ```
    You'll see a response like this:
    ```
    Created KMS key: cdd59e61-b6fa-4d95-b71f-8d6ae3abc123
    Consider setting an environment variable: 
    `export KMS_KEY_ID=cdd59e61-b6fa-4d95-b71f-8d6ae3abc123`
    ```
1. Copy the command from the terminal to set the KMS_KEY_ID environment variable; for example:
    ```
    export KMS_KEY_ID=abc12361-b6fa-4d95-b71f-8d6ae3abc123
    ```

## Get certificate

When purchasing a certificate and key, you might be able to simply click a "Buy" button on the CA's website. Or your can make your own key, create an CSR, and send it to CA.  In either case what comes back is the signed certificate that you use to create a certificate chain.

If you use the CSR you generated in the previous step to purchase a certificate from a CA, the CSR is just an unsigned certificate that is the template for the final certificate.  The CA will take the CSR and create a new certificate with the same parameters and sign it with their root certificate, which makes it a "real" certificate.

The process is different for each CA (links below are to [Digicert](https://www.digicert.com), but there are [many other CAs](https://opensource.contentauthenticity.org/docs/getting-started#getting-a-security-certificate)).  Additionally, CAs offer a variety of different kinds of certificates and levels of vetting and validation:
- The simplest and least expensive option is an [S/MIME email certificate](https://www.digicert.com/tls-ssl/compare-secure-email-smime-certificates).  
- Other options, such as [document signing certificate](https://www.digicert.com/signing/compare-document-signing-certificates) require more rigor (like proving your identity) and cost more.

For testing and demonstration purposes, you can create a self-signed certificate for use as a root CA. The resulting manifests won't be trusted, but you can use it to run the application to see how it works before purchasing a real certificate from a CA.

Follow these steps:

1. Enter this OpenSSL command:
    ```
    openssl req -x509 \
    -days 1825 \
    -newkey rsa:2048 \
    -keyout rootCA.key \
    -out rootCA.crt
    ```
    This command creates a temporary test root CA key/certificate.  For a detailed explanation, [see below](#understanding-the-openssl-commands).
1. You'll be prompted to enter and confirm a PEM passphrase.  Then you'll see a message like this.  Respond to the prompts to provide the required information:
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
1. Enter this command to sign the CSR with the temporary test CA key:
    ```
    openssl x509 -req \
    -CA rootCA.crt \
    -CAkey rootCA.key \
    -in kms-signing.csr \
    -out kms-signing.crt \
    -days 365 \
    -copy_extensions copyall
    ```
    For a detailed explanation of the command, [see below](#understanding-the-openssl-commands).<br/>
    You'll be prompted for the passphrase you entered in the previous step.
    You'll see a response like this:
    ```
    Certificate request self-signature ok
    subject=O=C2PA Python Demo, CN=John Smith
    Enter pass phrase for rootCA.key:
    ```

### Understanding the OpenSSL commands

The [`openssl req -x509`](https://docs.openssl.org/master/man1/openssl-req/) command
creates a self-signed certificate for use as a root CA.  The other options in the command are:

| Option and value | Explanation |
|--------|-------------|
| -days 1825 | Specifies that the certificate is good for 1825 days (five years) from today. |
| -newkey rsa:2048 | Generate a new 2048-bit private key using RSA encryption. |
| -keyout rootCA.key | Save the private key to the `rootCA.key` file. |
| -out rootCA.crt | Save the root certificate to the `rootCA.crt` file. |

The [`openssl x509 -req`](https://docs.openssl.org/master/man1/openssl-x509/) command indicates to expect a self-signed PKCS#10 certificate request.

| Option | Explanation |
|--------|-------------|
| -CA rootCA.crt | Specifies the "CA" certificate to be used for signing. When present, this behaves like a "micro CA" as follows: The subject name of the "CA" certificate is placed as issuer name in the new certificate, which is then signed using the key specified by the `-CAkey` option. |
| -CAkey rootCA.key | Sets the CA private key to sign a certificate with. The private key must match the public key of the certificate specified by the `-CA` option.  |
| -in kms-signing.csr | Read the certificate request from `kms-signing.csr` file. |
| -out kms-signing.crt | Write output to `kms-signing.crt` file. |
| -days 365 | Specifies that the newly-generated certificate expires in 365 days. |
| -copy_extensions copyall | Copy all extensions, except that subject identifier and authority key identifier extensions. |

## Create certificate chain

Create certificate chain file PEM with certificate issued by CA and CA Root certificate. For example, with the self-signed certificate:

```
cat kms-signing.crt rootCA.crt > chain.pem
```

## Run the application 

1. Run the application by entering this command:
    ```
    FLASK_KMS_KEY_ID="$KMS_KEY_ID" FLASK_CERT_CHAIN_PATH="./chain.pem" flask run
    ```
    You'll see a response like this:
    ```
    Using KMS key: cdd59e61-b6fa-4d95-b71f-8d6ae3abc123
    Using certificate chain: ./chain.pem
    * Debug mode: off
    WARNING: This is a development server. Do not use it in a production deployment. 
    Use a production WSGI server instead.
    * Running on http://127.0.0.1:5000
    Press CTRL+C to quit
    ```
2. Upload and sign image: In another terminal window, use `curl` to upload an image file (the app works only with JPEGs) and have the app sign it by entering a command like this:
    ```
    curl -X POST -T "<PATH_TO_JPEG>" -o <SIGNED_FILE_NAME>.jpg 'http://localhost:5000/attach'
    ```
    For example:
    ```
    curl -X POST -T ~/Desktop/test.jpeg -o signed.jpeg 'http://localhost:5000/attach' 
    ```
    In this example, the image with signed Content Credentials is saved to `signed.jpeg`.

If you encounter any issues running the `curl` command, try using `127.0.0.1` instead of `localhost`.

Confirm that the app signed the output image by doing one of these:
- If you've installed C2PA Tool, run `c2patool <SIGNED_FILE_NAME>.jpg`.
- Upload the image to https://contentcredentials.org/verify. Note that Verify will display the message **This Content Credential was issued by an unknown source** because it was signed with a certificate not on the [known certificate list](https://opensource.contentauthenticity.org/docs/verify-known-cert-list).
