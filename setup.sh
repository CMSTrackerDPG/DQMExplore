#!/bin/bash

SSO_CLIENT_ID_INPUT=$1
SSO_CLIENT_SECRET_INPUT=$2

# Prompt for them if not provided
if [ -z "$SSO_CLIENT_ID_INPUT" ]; then
  read -p "Enter SSO_CLIENT_ID: " SSO_CLIENT_ID_INPUT
fi
if [ -z "$SSO_CLIENT_SECRET_INPUT" ]; then
  read -p "Enter SSO_CLIENT_SECRET: " SSO_CLIENT_SECRET_INPUT
fi

# Create and enter working directory
mkdir -p DQME
cd DQME

# Create virtual environment & install dependencies
python3.11 -m venv venv
source venv/bin/activate
git clone https://github.com/CMSTrackerDPG/DQMExplore
cd DQMExplore
pip3 install .

# Write the .env file
cat > .env <<EOF
SSO_CLIENT_ID=${SSO_CLIENT_ID_INPUT}
SSO_CLIENT_SECRET=${SSO_CLIENT_SECRET_INPUT}

# Variable which sets which URL to use, and how to access it.
# The value can be "local", "development" or "production".
ENVIRONMENT=production
EOF

echo ".env file created with SSO credentials and production environment."
