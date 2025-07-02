#!/usr/bin/env python3
"""
Setup script per il sistema di estrazione avanzata K-Array.
Installa le dipendenze necessarie e configura l'ambiente.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_package(package):
    """Installa un pacchetto Python via pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installato: {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Errore installando: {package}")
        return False

def setup_extractor_dependencies():
    """Installa tutte le dipendenze per l'estrazione avanzata."""
    
    print("🔧 Setup del Sistema di Estrazione Avanzata K-Array")
    print("=" * 60)
    
    # Core dependencies
    core_packages = [
        "aiohttp>=3.8.0",
        "aiofiles>=0.8.0", 
        "beautifulsoup4>=4.11.0",
        "requests>=2.28.0"
    ]
    
    # Document processing
    document_packages = [
        "PyPDF2>=3.0.0",
        "pdfplumber>=0.7.0",
        "openpyxl>=3.0.0", 
        "python-docx>=0.8.11"
    ]
    
    # Optional advanced packages
    advanced_packages = [
        "pytesseract>=0.3.10",  # OCR for images in PDFs
        "Pillow>=9.0.0",        # Image processing
        "youtube-dl>=2021.12.17", # Video download (for YouTube videos)
        "speech-recognition>=3.8.1", # Audio transcription
        "pydub>=0.25.1"         # Audio processing
    ]
    
    print("📦 Installando dipendenze core...")
    for package in core_packages:
        install_package(package)
    
    print("\n📄 Installando processori documenti...")
    for package in document_packages:
        install_package(package)
    
    print("\n🎯 Installando funzionalità avanzate...")
    for package in advanced_packages:
        install_package(package)
    
    print("\n✅ Setup completato!")
    print("\nPer utilizzare OCR (opzionale), installa tesseract:")
    print("- macOS: brew install tesseract")
    print("- Ubuntu: sudo apt-get install tesseract-ocr")
    print("- Windows: scarica da https://github.com/UB-Mannheim/tesseract/wiki")

if __name__ == "__main__":
    setup_extractor_dependencies()