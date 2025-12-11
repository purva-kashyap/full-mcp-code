#!/bin/bash

# Run the Zoom web app with Gunicorn

echo "🚀 Starting Zoom Web App with Gunicorn..."
echo "📍 Server will run on http://localhost:5002"
echo ""

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "❌ Gunicorn not found. Installing..."
    pip3 install gunicorn
fi

# Start Gunicorn
gunicorn --config gunicorn.conf.py app:app
