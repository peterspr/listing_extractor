#!/bin/bash
# Render.com build script

echo "Installing system dependencies..."
apt-get update
apt-get install -y default-jre

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build complete!"
