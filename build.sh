#!/bin/bash
# Build script for Hortus Cognitor on Render

set -e  # Exit on any error

echo "🔧 Installing requirements..."
pip install -r requirements.txt

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗄️ Running migrations..."
python manage.py migrate

echo "📊 Loading sample course data..."
python manage.py load_sample_data

echo "💰 Setting up pricing tiers..."
python manage.py setup_pricing

echo "✅ Build complete!"