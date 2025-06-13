#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Run Streamlit
streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true 