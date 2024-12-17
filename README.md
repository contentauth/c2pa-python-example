# C2PA Python example

## Overview

[This repository](https://github.com/contentauth/c2pa-python-example) is an example of a simple application that accepts an uploaded JPEG image file, attaches a C2PA manifest, and signs it using a certificate.  The app uses the CAI Python library and the [Flask Python framework](https://flask.palletsprojects.com/en/3.0.x/) to implement a back-end REST endpoint; it does not have an HTML front-end, so you have to use something like `curl` to access it.

The app uses [Amazon Key Management Service (KMS)](https://aws.amazon.com/kms/) to create and control cryptographic keys and the [AWS SDK for Python (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html) to call KMS.
During development and testing, you can also use [LocalStack](https://www.localstack.cloud/) to run a localized environment that simulates interactions with AWS.

### About CSRs

In addition to being an example of using the Python library, this app shows how to generate a certificate signing request (CSR), a message sent to a certificate authority (CA) to request the signing of a public key and associated information.

A CSR comprises a public key, as well as a common name, organization, city, state, country, and e-mail address. Not all of these fields are required and will vary depending with the assurance level of your certificate.

You sign the CSR with your private key; this proves to the CA that you have control of the private key that corresponds to the public key included in the CSR. Once the requested information in a CSR passes a vetting process and domain control is established, the CA may sign the public key to indicate that it can be publicly trusted.

## Prerequisites

To build and run this app, you must install:

- Python 3.10 or Python 3.12.
- OpenSSL: See [OpenSSL](https://www.openssl.org/source/) for the source distribution or the [list of unofficial binary distributions](https://wiki.openssl.org/index.php/Binaries).  Make sure you have a recent version.

If you wish to run this example with AWS, you must also have an AWS account and be able to get standard AWS access credentials so you can use KMS. To run this example entirely locally for development and testing, follow the steps in [Using LocalStack](README.md#using-localstack) to setup and run a mock AWS environment runing locally.

NOTE: This app was developed and tested on macOS. It should also work on other operating systems, but on Windows you may have to take additional steps.

## Install dependencies

Open a terminal window and follow these steps:

1. Set up [virtual environment](https://docs.python.org/3/library/venv.html) by entering these commands:

    ```shell
    python -m venv c2pa-env
    source c2pa-env/bin/activate
    ```

    In the first command, `c2pa-env` is the name of the virtual environment; you can use another name if you wish. These two commands do not produce any output in the terminal window, but your prompt will change to `(c2pa-env)` or whatever environment name you chose.
1. Install dependencies:

    ```shell
    cd c2pa-python-example
    pip install -r requirements.txt
    ```

    You will see this output in the terminal:

    ```shell
    Collecting c2pa-python==0.5.0
    ...
    ```

## Setup to use Docker

The example code from this repository can run in Docker containers with default  configurations. The Docker containers use LocalStack to run a localized environment that simulates interactions with AWS. This is the quickest way to spin up a working development environment (without doing additional configuration.) 

NOTE: This is a development setup and should not be deployed as-is to a production environment.

### Prerequisites

You must have Docker Desktop version 4.34.3 (170107) or later.

### Run the local setup

Build and run the Docker containers by entering this command:

```shell
make local
```

The command will first build and then run the containers using the [docker-compose file](docker-compose.yaml), which does the following:

1. Uses LocalStack to run a mock AWS infrastructure in a container called `localstack-main`.
2. The setup scripts will run (using the code from [setup.py](setup.py) and [local-setup.sh](local-setup.sh)) from a container called `local-setup` and configure the example, automating previous manual steps to have the supporting infrastructure (for example, creating mocked AWS users in LocalStack and certificate infrastructure). The container exits once the setup is done. The files created during setup are copied for reference to the `config_volume` directory in the root of this repository. Note that changing the values of the configurations in this directory does not affect the running Docker setup, nor after restarting it.
3. The signing server starts with default configuration in the `local-signer` container.
4. Once the signing server is ready, the example runs a self-check using the Python client and verifies that a default image placed in `client_volume/signed-images` can be signed using a `local-client` container. You can then also see the signed test file in a directory created at the root of this repo, `client_volume/signed_images`.

When the `make local` command finishes, it displays something like this:

```shell
(...Docker images build details...)

--- Running containers.........

docker compose up -d
[+] Running 5/5
 ✔ Network c2pa-python-example_default  Created                                                              0.0s
 ✔ Container localstack-main            Started                                                              0.3s
 ✔ Container local-setup                Exited                                                               0.8s
 ✔ Container local-signer               Healthy                                                              6.4s
 ✔ Container local-client               Started
```

### Re-run the Python client container

To re-run the Python client, enter the following command from the root of this repository:

```shell
docker compose run --entrypoint "Python tests/client.py ./tests/A.jpg -o client_volume/signed-images" client
```

Replace `./tests/A.jpg` with the path to the image you want to sign.

### Clean up the local setup

After trying out the example, be sure to stop and remove the containers by running this command at the root of this repository:

```shell
make clean
```

Once the cleanup is done, you'll see messages similar to this:

```shell

--- Cleaning up.................

docker compose down --volumes --remove-orphans
[+] Running 6/6
 ✔ Container local-client                 Removed                                                            0.0s 
 ✔ Container local-signer                 Removed                                                           10.1s 
 ✔ Container localstack-main              Removed                                                            1.1s 
 ✔ Container local-setup                  Removed                                                            0.0s 
 ✔ Volume c2pa-Python-example_local-data  Removed                                                            0.0s 
 ✔ Network c2pa-Python-example_default    Removed
```

## Setting up to run the example locally

These steps show and explain the details of running the signer example locally directly on your machine (not in a Docker container). This is a development setup and should not be deployed as-is to a production environment.

### Set up with AWS credentials

You must have an AWS account and be able to get standard AWS access credentials so you can use KMS.

Follow the AWS documentation to [Configure the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) and add AWS credentials to `$HOME/.aws/credentials` as follows (key and token values not shown):

```
[default]
region=us-east-1
aws_access_key_id=...
aws_secret_access_key=...
aws_session_token=...
```

### Using LocalStack

Instead of calling AWS services, you can use [LocalStack](https://www.localstack.cloud/) to run the example entirely on your local machine, simulating interactions with AWS. 

NOTE: This setup is suitable for development only.

#### Set up the LocalStack environment

Install LocalStack followin the [installation instructions](https://docs.localstack.cloud/getting-started/installation/) for your configuration.

#### Run LocalStack

Once LocalStack is installed, open a shell window and start the LocalStack stack in detached mode:

```shell
localstack start -d
```

Make sure to keep LocalStack running while you work through this example.
Warning: Anything configured in LocalStack is transient, and will be lost on restart/reboot of the LocalStack container.

#### Install awslocal CLI

To interact with LocalStack, install the CLI tool `awslocal` that substitutes for the `aws` CLI while LocalStack is running. For more information, see the [LocalStack documentation](https://docs.localstack.cloud/user-guide/integrations/aws-cli/).

Follow these steps:

1. Ensure that you have activated your Python virtual environment.
2. Since `awslocal` is a wrapper around the `aws` CLI, you need to install the `awscli` package first by entering this command:
   ```shell
    pip install awscli
    ```
3. Install `awslocal` into your local virtual environment by entering this command:
    ```shell
    pip install awscli-local
    ```

#### Create an environment file

The app uses environment variables to get credentials and the LocalStack endpoint to access. Therefore, you need to set up a `.env` file in the root of the repository following the format of the [example-env.env file](example-env.env) file. The setup script and the Flask app will then get the values from the `.env` file.

The environment file contains these values:

- `RUN_MODE` will be `DEV` for development mode. This is the only mode that LocalStack supports.
- `AWS_ENDPOINT` is to the AWS endpoint to use. With LocalStack, this is the endpoint on which the tool listens to intercept AWS interactions.
- `REGION` is the default AWS region to use. This must be a valid region name.
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are AWS user credentials.

#### Create test user account

For our example, you will create a test user and use that account's credentials for signing.

1. Ensure that LocalStack is running.
2. Create a user named `test` by entering this command:
    ```shell
    awslocal iam create-user --user-name test
    ```
3. Recover the credentials for that user by entering this command:
    ```shell
    awslocal iam create-access-key --user-name test
    ```

The command displays the following output to the terminal:

```json
{
    "AccessKey": {
        "UserName": "test",
        "AccessKeyId": "LK_AWS_ACCESS_KEY_ID",
        "Status": "Active",
        "SecretAccessKey": "AWS_SECRET_ACCESS_KEY",
        "CreateDate": "2024-11-06T00:20:30Z"
    }
}
```

Confirm that:
- The value of `AccessKeyId` shown is that of the environment variable `AWS_ACCESS_KEY_ID` in the `.env` file that you set previously.
- The value of `SecretAccessKey` is that of the environment variable `AWS_SECRET_ACCESS_KEY` in the `.env` file that you set previously.

For more information on identity and access management with LocalStack, see the [LocalStack documentation](https://docs.localstack.cloud/user-guide/aws/iam/).

### Get KMS key and CSR

NOTE: Amazon KMS uses Distinguished Encoding Rules (DER) encoding for cryptographic keys. The C2PA specification does not provide for DER support, but the CAI open-source SDK automatically converts it to a supported format.

#### Use an existing KMS key

If you have an existing KMS key that you want to use for signing, follow these steps to generate a CSR:

1. Set the KMS_KEY_ID environment variable to the value of the KMS key; for example:

    ```shell
    export KMS_KEY_ID=abc12361-b6fa-4d95-b71f-8d6ae3abc123
    ```

1. Then run this command to generate a certificate request

    ```shell
    python setup.py generate-certificate-request {KMS_KEY_ID} {CSR_SUBJECT}
    ```

    For example:

    ```shell
    python setup.py generate-certificate-request \
    arn:aws:kms:us-east-1:12312323:key/123-123-123-8b8b-123 \
    "C=US,ST=NY,L=NeW York,O=EXACT ORGANIZATION NAME,CN=EXACT ORGANIZATION NAME"
    ```

#### Generate a KMS key and CSR

If you don't have an existing KMS key, follow these steps to generate a KMS key and CSR:

1. Enter this command to create a KMS key and generate a CSR:

    ```shell
    python setup.py create-key-and-csr {CSR_SUBJECT}
    ```

    Where `{CSR_SUBJECT}` is an [RFC 4514](https://datatracker.ietf.org/doc/html/rfc4514.html) string representation of a distinguished name (DN) identifying the applicant.
    For example:

    ```shell
    python setup.py create-key-and-csr 'CN=John Smith,O=C2PA Python Demo'
    ```

    You'll see a response like this:

    ```shell
    Created KMS key: cdd59e61-b6fa-4d95-b71f-8d6ae3abc123
    ```

    By default, when the setup.py script command is run from the root of this repository, this will create a file name `kms-signing.csr` at the root of the repository. The setup.py script will also add add the value of the generated key id to a local `.env` file under the key `KMS_KEY_ID`.

### Get a certificate for signing

When purchasing a certificate and key, you might be able to simply click a "Buy" button on the CA's website. Or your can make your own key, create an CSR, and send it to CA.  In either case what comes back is the signed certificate that you use to create a certificate chain.

If you use the CSR you generated in the previous step to purchase a certificate from a CA, the CSR is just an unsigned certificate that is the template for the final certificate.  The CA will take the CSR and create a new certificate with the same parameters and sign it with their root certificate, which makes it a "real" certificate.

The process is different for each CA (links below are to [Digicert](https://www.digicert.com), but there are [many other CAs](https://opensource.contentauthenticity.org/docs/getting-started#getting-a-security-certificate)).  Additionally, CAs offer a variety of different kinds of certificates and levels of vetting and validation:

- The simplest and least expensive option is an [S/MIME email certificate](https://www.digicert.com/tls-ssl/compare-secure-email-smime-certificates).
- Other options, such as [document signing certificate](https://www.digicert.com/signing/compare-document-signing-certificates) require more rigor (like proving your identity) and cost more.

### For development: Using self-signed certificates

For testing and demonstration purposes, you can create a self-signed certificate for use as a root CA. The resulting manifests won't be trusted, but you can use it to run the application to see how it works before purchasing a real certificate from a CA.

Follow these steps:

1. Enter this OpenSSL command:

    ```shell
    openssl req -x509 \
    -days 1825 \
    -newkey rsa:2048 \
    -keyout rootCA.key \
    -out rootCA.crt
    ```

    This command creates a set of temporary test root CA key and certificate. By default, when this command is run from the root of this repository, you will see two files appear in the repository root: `rootCA.crt` and `rootCA.key`). For a detailed explanation of the command, [see below](#understanding-the-openssl-commands).

1. You'll be prompted to enter and confirm a PEM passphrase.  Then you'll see a message like this.  Respond to the prompts to provide the required information:

    ```shell
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

    ```shell
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

    ```shell
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

### Create certificate chain

Create certificate chain file PEM with certificate issued by CA and CA Root certificate. For example, with the self-signed certificate:

```shell
cat kms-signing.crt rootCA.crt > chain.pem
```

By default, when this command is run from the root of this repository, this will place the certificate chain in the root of this repository (file named `chain.pem`). As a reminder, this `chain.pem` file is a chain of certificates (and not a signing key).

### Run the application

1. Run the application by entering this command:

    ```shell
    python3 app.py
    ```

    You'll see a response like this:``

    ```shell
    Using KMS for signing
    Running example in dev mode with AWS endpoint: http://localhost.localstack.cloud:4566/
    Using KMS key: cdd59e61-b6fa-4d95-b71f-8d6ae3abc123
    Using certificate chain: chain.pem
    Press CTRL+C to stop the server
    INFO:waitress:Serving on http://0.0.0.0:5000
    ```

2. Upload and sign image: In another terminal window, use `curl` to upload an image file (the app works only with JPEGs) and have the app sign it by entering a command like this:

    ```shell
    curl -X POST -T "<PATH_TO_JPEG>" -o <SIGNED_FILE_NAME>.jpg 'http://localhost:5000/attach'
    ```

    For example:

    ```shell
    curl -X POST -T ~/Desktop/test.jpeg -o signed.jpeg 'http://localhost:5000/attach'
    ```

    In this example, the image with signed Content Credentials is saved to `signed.jpeg`.

If you encounter any issues running the `curl` command, try using `127.0.0.1` instead of `localhost`.

Confirm that the app signed the output image by doing one of these:

- If you've installed [C2PA Tool](https://github.com/contentauth/c2patool), run `c2patool <SIGNED_FILE_NAME>.jpg`.
- Upload the image to https://contentcredentials.org/verify. Note that Verify will display the message **This Content Credential was issued by an unknown source** because it was signed with a certificate not on the [known certificate list](https://opensource.contentauthenticity.org/docs/verify-known-cert-list).
