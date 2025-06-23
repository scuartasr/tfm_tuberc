#!/bin/bash
echo "📦 Actualizando pip..."
pip install --upgrade pip

echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "✅ Listo."
