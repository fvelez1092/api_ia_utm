#!/usr/bin/env sh
set -eu

key_directory="${1:-./secrets}"
mkdir -p "$key_directory"
umask 077

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out "$key_directory/jwt-private.pem"
openssl pkey -in "$key_directory/jwt-private.pem" -pubout -out "$key_directory/jwt-public.pem"

echo "Claves JWT creadas en $key_directory"
