#!/bin/bash

# Update and upgrade the system and automatically handle restarts
apt-get update && apt-get full-upgrade -y
apt-get install -y needrestart
needrestart -r a

#aws on aws ubuntu
apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "../awscliv2.zip"
unzip ../awscliv2.zip
sudo ../aws/install

# Install prerequisites and Docker
apt-get install -y apt-transport-https ca-certificates curl software-properties-common \
                   postgresql postgresql-contrib default-jdk awscli

# Docker installation and setup
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update && apt-get install -y docker-ce

apt install nodejs npm -y
npm install pm2@latest -g

# Python installation and setup
add-apt-repository -y ppa:deadsnakes/ppa
pt-get update
apt-get install -y python3.10
apt install -y python3-pip
apt install -y python3-boto3
apt install -y python3-botocore
apt install -y python3-dotenv
apt install -y python3-pandas
apt install -y python3-filelock

# Node Version Manager (NVM) and Node setup
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
nvm install 21

# Homebrew (Linuxbrew) installation
echo | /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
test -d ~/.linuxbrew && eval "$(~/.linuxbrew/bin/brew shellenv)"
test -d /home/linuxbrew/.linuxbrew && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
test -r ~/.bash_profile && echo "eval \$($(brew --prefix)/bin/brew shellenv)" >>~/.bash_profile
echo "eval \$($(brew --prefix)/bin/brew shellenv)" >>~/.profile

# Parquet-tools installation
wget https://repo1.maven.org/maven2/org/apache/parquet/parquet-tools/1.11.1/parquet-tools-1.11.1.jar -O /usr/local/bin/parquet-tools.jar
echo 'alias parquet-tools="java -jar /usr/local/bin/parquet-tools.jar"' >> ~/.bashrc
source ~/.bashrc

# Run Docker compose
# running the command below will start the postgres db in docker in your current vps
# docker compose up -d postgres

# Configure s3 bucket for neynar information (assuming credentials are set)
aws configure --profile neynar_parquet_exports

chmod +x download_files.sh insert_update_sql.sh