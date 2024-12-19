#!/bin/bash

if [[ -z $1 || -z $2 ]];
then
	echo "usage: create-cert.sh CERT_EMAIL PATH_TO_CSR"
	exit
fi

CERT_EMAIL=$1
PATH_TO_CSR=$2

if [[ -z $DIGICERT_API_KEY ]];
	then
		echo "var DIGICERT_API_KEY must be set"
		exit
fi

CSR_CONTENT=$(cat $PATH_TO_CSR | tr -d "\n")

echo "Creating a cert with email $CERT_EMAIL..........."

REQUEST_BODY="{
		\"certificate\": {
			\"csr\": \"${CSR_CONTENT}\",
 			\"emails\": [\"${CERT_EMAIL}\"],
			\"usage_designation\": {
				\"primary_usage\": \"signing\"
				}
		},
		\"order_validity\": {
			\"years\": \"1\"
			},
		\"payment_method\": \"profile\",
		\"skip_approval\": \"true\"
	}"

curl 'https://www.digicert.com/services/v2/order/certificate/secure_email_mailbox' \
  -H 'Content-Type: application/json' \
  -H "X-DC-DEVKEY: ${DIGICERT_API_KEY}" \
  --data-raw "$REQUEST_BODY"

