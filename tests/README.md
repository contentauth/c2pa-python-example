# C2PA Client Documentation

This directory contains the client for signing JPEG images with content credentials. This client is designed to work with the C2PA Python Example server in development mode using demo certificates (included in this repository).

## Overview

The `client.py` file is a command-line test tool that signs JPEG image files. It connects to the signing server defined in `app.py`, to add Content Credentials to JPEG images.

## Prerequisites

1. **Python Dependencies**: Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

2. **Running signing Server**: The signing server (`app.py`) must be running using local certificates  and accessible to the client:

   ```bash
   python app.py
   ```

3. **Image Files**: JPEG images to be signed

## Usage

Only JPEG images are supported with this test client.

### Basic Command

```bash
python tests/client.py <image-file> -o <output-directory>
```

### Command Line Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `files` | string | Yes | One or more image files to be signed |
| `-o, --output` | string | Yes | Output directory where signed images will be saved |
| `-f, --envfile` | string | No | Path to environment configuration file |

### Examples

#### Sign a single image

```bash
python tests/client.py ./image-to-sign.jpeg -o signed-images
```

#### Use custom configuration

```bash
python tests/client.py ./image-to-sign.jpeg -o signed-images -f ./my-config.env
```

## Signing flow when using the client

1. **Server Connection**: Client connects to the signing server's `/signer_data` endpoint.
2. **Configuration Retrieval**: Gets signing algorithm, certificate chain, and signing URL.
3. **Signer Creation**: Creates a remote signer using the modern C2PA API (`Signer.from_callback`)/
4. **Manifest Creation**: Generates a default C2PA manifest.
5. **Image Processing**: Creates a thumbnail for the manifest and adds it as resource.
6. **Remote Signing**: Uses the `Builder.sign()` method with remote signing callback.
7. **Output**: Saves the signed image to the specified output directory.
