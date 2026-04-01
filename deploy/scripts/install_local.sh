#!/bin/bash

# install aws
pip install -U awscli

# kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
chmod +x ./kubectl
mv ./kubectl /usr/local/bin/kubectl

# terraform
curl -LO https://releases.hashicorp.com/terraform/0.12.29/terraform_0.12.29_linux_amd64.zip
unzip terraform_0.12.23_linux_amd64.zip -d /usr/local/bin/
rm terraform_0.12.23_linux_amd64.zip

# terraform providers
mkdir -p ~/.terraform.d/plugins
curl -LO https://github.com/jianyuan/terraform-provider-sentry/releases/download/v0.5.5/terraform-provider-sentry_0.5.5_linux_amd64.zip
unzip terraform-provider-sentry_0.5.5_linux_amd64.zip
chmod +x ./terraform-provider-sentry_v0.5.5 && mv ./terraform-provider-sentry_v0.5.5 ~/.terraform.d/plugins/
rm terraform-provider-sentry_0.5.5_linux_amd64.zip

# helm
curl -LO https://get.helm.sh/helm-v3.1.1-linux-amd64.tar.gz
tar -zxvf helm-v3.1.1-linux-amd64.tar.gz
mv linux-amd64/helm /usr/local/bin/
rm -rf helm-v3.1.1-linux-amd64.tar.gz ./linux-amd64/
