#!/bin/bash

# Define variables
REPO_URL="https://github.com/tfriberg/sensor.avanza_stock_gui"
BRANCH="test_branch"
COMPONENT_NAME="avanza_stock"
CONFIG_DIR="$HOME/.homeassistant"  # Change this if your config directory is different

# Create temporary directory
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

# Download the specific branch
echo "Downloading $BRANCH branch from $REPO_URL..."
curl -L "$REPO_URL/archive/refs/heads/$BRANCH.zip" -o repo.zip

# Unzip
echo "Extracting files..."
unzip repo.zip

# Create custom_components directory if it doesn't exist
mkdir -p "$CONFIG_DIR/custom_components"

# Remove existing component if it exists
if [ -d "$CONFIG_DIR/custom_components/$COMPONENT_NAME" ]; then
    echo "Removing existing component..."
    rm -rf "$CONFIG_DIR/custom_components/$COMPONENT_NAME"
fi

# Copy the new files
echo "Installing component..."
cp -r */custom_components/$COMPONENT_NAME "$CONFIG_DIR/custom_components/"

# Cleanup
cd
rm -rf "$TMP_DIR"

echo "Installation complete! Please restart Home Assistant to apply changes."
