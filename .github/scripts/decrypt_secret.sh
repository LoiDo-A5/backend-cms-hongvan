#!/bin/sh

# Decrypt the file
mkdir $HOME/secrets
# --batch to prevent interactive command
# --yes to assume "yes" for questions
cd .github/scripts/
gpg --quiet --batch --yes --decrypt --passphrase="$PASSWORD_DECRYPT_GPG_FILE" \
--output $HOME/secrets/3gfeo1hccuwnf1hh.kubeconfig 3gfeo1hccuwnf1hh.kubeconfig.gpg
pwd
