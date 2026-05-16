#!/bin/bash

# Define the name of the zip file
ZIP_FILE="project_sources.zip"

# Find and zip all relevant files, excluding node_modules and other unwanted files
zip -r $ZIP_FILE . -x \
    "*/node_modules/*" \
    "*/package-lock.json" \
    "*/yarn.lock" \
    "*/public/*" \
    "*/screenshots/*" \
    "*.lock"

echo "Zipped all relevant source files into $ZIP_FILE"

