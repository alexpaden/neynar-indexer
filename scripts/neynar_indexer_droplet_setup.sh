#!/bin/bash

# Update and upgrade the system and automatically handle restarts
apt-get update && apt-get full-upgrade -y
apt-get install -y needrestart
needrestart -r a

# Install prerequisites for AWS CLI, Docker, Node.js, Python, and utilities
apt-get install -y apt-transport-https ca-certificates curl software-properties-common unzip
apt-get install -y postgresql postgresql-contrib default-jdk

# Docker installation and setup
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce

# Node.js and PM2 setup
apt install -y nodejs npm
npm install pm2@latest -g

# Python installation and setup
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.10 python3-pip
apt-get install -y python3-boto3 python3-botocore python3-dotenv python3-pandas python3-filelock psycopg2
pip install pyarrow boto3 python-dotenv --break-system-packages
pip install sqlalchemy --break-system-packages

# AWS CLI installation
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm awscliv2.zip

# Add AWS CLI path explicitly if not automatically configured
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
source ~/.bashrc

# Node Version Manager (NVM) setup
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 21

# Homebrew (Linuxbrew) installation
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
test -d /home/linuxbrew/.linuxbrew && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
echo "eval \$($(brew --prefix)/bin/brew shellenv)" >>~/.profile

# Parquet-tools installation
wget https://repo1.maven.org/maven2/org/apache/parquet/parquet-tools/1.11.1/parquet-tools-1.11.1.jar -O /usr/local/bin/parquet-tools.jar
echo 'alias parquet-tools="java -jar /usr/local/bin/parquet-tools.jar"' >> ~/.bashrc
source ~/.bashrc

# Configure AWS CLI for specific profile
aws configure --profile neynar_parquet_exports

chmod +x ./scripts/download_files.sh ./scripts/insert_update_sql.sh
