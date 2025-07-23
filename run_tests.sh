#!/bin/bash
# Run tests for mNAV webhook application

echo "🧪 Running mNAV Tests..."
echo "========================"

# Run unit tests
python -m pytest test_app.py -v --tb=short 2>/dev/null || python -m unittest test_app.py -v

echo ""
echo "📊 Test Summary Complete"