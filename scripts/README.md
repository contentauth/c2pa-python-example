# Script to purchase Digitcert signing certificate

Use the shell script in this directory to issue an API request to Digicert requesting a digital certificate.

## Prerequisites

You must set the enviornment variable DIGICERT_API_KEY to the value of your 
[Digicert API key](https://dev.digicert.com/en/certcentral-apis/authentication.html).

## Run the script

Enter this command to run the script:

```
./digicert-create-cert.sh <YOUR_EMAIL> <PATH_TO_CSR_FILE>
```

Where:
- `<YOUR_EMAIL>` is the email associated with your Digicert account.
- `<PATH_TO_CSR_FILE>` is the path to the certificate signing request (CSR) file that you're using for your request.
