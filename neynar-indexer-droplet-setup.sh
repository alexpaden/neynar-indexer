#!/bin/bash

# Update and upgrade the system
apt-get update && apt-get upgrade -y

# Install prerequisites
apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce

# Install PostgreSQL
apt-get install -y postgresql postgresql-contrib

# Install Python 3.10
apt-get install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.10
apt install -y python3-pip
apt install python3-boto3
apt install python3-botocore
apt install python3-dotenv
apt install python3-pandas

# Install Node Version Manager (NVM)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Install specific Node version
nvm install 21

# Install Homebrew (Linuxbrew)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
test -d ~/.linuxbrew && eval "$(~/.linuxbrew/bin/brew shellenv)"
test -d /home/linuxbrew/.linuxbrew && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
test -r ~/.bash_profile && echo "eval \$($(brew --prefix)/bin/brew shellenv)" >>~/.bash_profile
echo "eval \$($(brew --prefix)/bin/brew shellenv)" >>~/.profile

# Install AWS CLI using APT
sudo apt-get update
sudo apt-get install -y awscli

# Install Parquet-tools
# Since parquet-tools is not available via apt, we use a Java-based tool from the Apache Parquet project.
sudo apt-get install -y default-jdk
wget https://repo1.maven.org/maven2/org/apache/parquet/parquet-tools/1.11.1/parquet-tools-1.11.1.jar -O /usr/local/bin/parquet-tools.jar
echo 'alias parquet-tools="java -jar /usr/local/bin/parquet-tools.jar"' >> ~/.bashrc
source ~/.bashrc


# Display completion message
echo "All installations are complete."
echo "=================================="
echo "=================================="

# Run Docker compose
docker compose up -d postgres

#configure s3 bucket for neynar information
aws configure --profile neynar_parquet_exports
