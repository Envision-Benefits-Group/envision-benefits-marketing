#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="envision-benefits-marketing"
OUTPUT_ZIP="/home/ubuntu/${PROJECT_NAME}.zip"

echo "Packaging ${PROJECT_NAME} for download..."

cd "$(dirname "$PROJECT_DIR")"

zip -r "$OUTPUT_ZIP" "$PROJECT_NAME" \
  --exclude "${PROJECT_NAME}/.git/*" \
  --exclude "${PROJECT_NAME}/node_modules/*" \
  --exclude "${PROJECT_NAME}/frontend/.next/*" \
  --exclude "${PROJECT_NAME}/frontend/node_modules/*" \
  --exclude "${PROJECT_NAME}/backend/__pycache__/*" \
  --exclude "${PROJECT_NAME}/backend/.venv/*" \
  --exclude "${PROJECT_NAME}/.env"

echo "Done. File saved to: ${OUTPUT_ZIP}"
echo ""
echo "Download it with SCP (run this on your local machine):"
echo "  scp -i YOUR-KEY.pem ubuntu@YOUR-EC2-PUBLIC-IP:${OUTPUT_ZIP} C:\\Users\\kristin\\Desktop\\"
