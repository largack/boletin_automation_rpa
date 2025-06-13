#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Debug: Show environment variables
echo "PORT environment variable: $PORT"
echo "All environment variables:"
env | grep -E "(PORT|HOST)"

# Set default port if not provided
if [ -z "$PORT" ]; then
    PORT=8501
    echo "No PORT set, using default: $PORT"
else
    echo "Using PORT from environment: $PORT"
fi

# Run Streamlit with proper port binding
echo "Starting Streamlit on 0.0.0.0:$PORT"
streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false 