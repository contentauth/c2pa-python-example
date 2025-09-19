# C2PA Client Documentation

This directory contains the C2PA (Coalition for Content Provenance and Authenticity) client for signing images with digital manifests. This client is designed to work with the C2PA Python Example server in development mode.

> **Note**: This client has been updated to use the modern C2PA Python API, matching the implementation in `app.py`.

## Overview

The `client.py` file is a command-line tool that signs image files with C2PA manifests. It connects to a signing server (the Flask app in `app.py`) to add digital signatures and content authenticity credentials to images.

## Prerequisites

1. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

2. **Running signing Server**: The Flask server (`app.py`) must be running and accessible
   ```bash
   python app.py
   ```

3. **Image Files**: JPEG images to be signed

## Usage

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

#### Sign multiple images
```bash
python tests/client.py ./image1.jpg ./image2.jpg -o signed-images
```

#### Use custom configuration
```bash
python tests/client.py ./image-to-sign.jpeg -o signed-images -f ./my-config.env
```

#### Using Docker
```bash
docker compose run --entrypoint "python tests/client.py ./tests/A.jpg -o client_volume/signed-images" client
```

## Configuration

The client can be configured in three ways:

### 1. Default Configuration
- **Server Endpoint**: `http://localhost:5000/signer_data`
- **Protocol**: HTTP
- **Host**: localhost
- **Port**: 5000

### 2. Environment File
Create a `.env` file with the following variables:

```env
CLIENT_HOST_PORT=5000
CLIENT_ENDPOINT=127.0.0.1
CLIENT_PROTOCOL=http
```

Then use it with:
```bash
python tests/client.py ./image.jpg -o output -f ./my-config.env
```

### 3. Environment Variable
Set the `CLIENT_ENV_FILE_PATH` environment variable:
```bash
export CLIENT_ENV_FILE_PATH=./my-config.env
python tests/client.py ./image.jpg -o output
```

## How It Works

1. **Server Connection**: Client connects to the signing server's `/signer_data` endpoint
2. **Configuration Retrieval**: Gets signing algorithm, certificate chain, and signing URL
3. **Signer Creation**: Creates a remote signer using the modern C2PA API (`Signer.from_callback`)
4. **Manifest Creation**: Generates a C2PA manifest with metadata:
   - Claim generator info
   - Action assertions (e.g., "c2pa.edited")
   - Software agent information
5. **Image Processing**: Creates thumbnail and processes the image
6. **Remote Signing**: Uses the modern `Builder.sign()` method with remote signing callback
7. **Output**: Saves the signed image to the specified output directory

## Generated Manifest

The client creates a standard C2PA manifest with the following structure:

```json
{
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
}
```

## Error Handling

The client handles various error scenarios:

- **Server Connection Issues**: Displays error if server is unreachable
- **Signing Failures**: Shows detailed error messages for signing problems
- **File Conflicts**: Prevents overwriting existing files
- **Invalid Configuration**: Validates configuration parameters

## Troubleshooting

### Common Issues

1. **"Failed to get signer data"**
   - Ensure the signing server is running (`python app.py`)
   - Check server endpoint configuration

2. **"Failed to sign [file]"**
   - Verify the server is accessible
   - Check certificate configuration on the server
   - Ensure output directory exists and is writable

3. **"Invalid configuration"**
   - Verify environment file format
   - Check that all required configuration variables are set

### Debug Mode

For additional debugging information, you can modify the client to include more verbose output or check the server logs.

