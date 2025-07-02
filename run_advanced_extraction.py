#!/usr/bin/env python3
"""
Script di lancio rapido per l'estrazione avanzata K-Array.
Estrae tutti i contenuti da k-array.com con focus su keywords per retrieval ottimale.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add knowledge_pipeline to path
sys.path.append(str(Path(__file__).parent / "knowledge_pipeline"))

from extraction_manager import ExtractionManager

async def main():
    parser = argparse.ArgumentParser(description="Sistema di Estrazione Avanzata K-Array")
    parser.add_argument("--full", action="store_true", help="Estrazione completa (sostituisce tutto)")
    parser.add_argument("--test", type=str, help="Testa keyword extraction su testo")
    parser.add_argument("--validate", action="store_true", help="Valida qualità knowledge base")
    parser.add_argument("--quick", action="store_true", help="Estrazione rapida (solo pagine principali)")
    
    args = parser.parse_args()
    
    manager = ExtractionManager()
    
    print("🚀 Sistema di Estrazione Avanzata K-Array")
    print("=" * 50)
    
    if args.test:
        print(f"🧪 Test keyword extraction su: '{args.test}'")
        result = await manager.test_keyword_extraction(args.test)
        print("\n📊 Risultati:")
        print(f"Keywords: {result['keywords']}")
        print(f"Prodotti: {result['products']}")
        print(f"Categoria: {result['category']}")
        
    elif args.validate:
        print("🔍 Validazione qualità knowledge base...")
        result = await manager.validate_extraction_quality()
        print("\n📊 Risultati validazione:")
        print(f"Documenti totali: {result['total_documents']}")
        print(f"Alta qualità: {result['high_quality_percentage']:.1f}%")
        print(f"Keywords medie per doc: {result['average_keywords_per_doc']:.1f}")
        print(f"Prodotti coperti: {result['unique_products_covered']}")
        print(f"Lista prodotti: {', '.join(result['products_list'][:10])}")
        
    else:
        incremental = not args.full
        mode = "incrementale" if incremental else "completa (sostituzione)"
        
        print(f"📥 Avvio estrazione {mode}...")
        print("⚠️  ATTENZIONE: Questo processo può richiedere diversi minuti")
        print("💡 Il sistema estrarrà:")
        print("   • Tutte le pagine web di k-array.com")
        print("   • PDF tecnici e manuali")
        print("   • File Excel con specifiche")
        print("   • Documenti Word")
        print("   • Keywords ottimizzate per retrieval")
        
        # Conferma dall'utente
        if not args.quick:
            confirm = input("\n🤔 Continuare? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Estrazione annullata")
                return
        
        # Esegui estrazione
        print("\n🔄 Avvio estrazione...")
        result = await manager.run_full_extraction(incremental=incremental)
        
        if result['success']:
            print("\n✅ ESTRAZIONE COMPLETATA CON SUCCESSO!")
            print(f"📄 Documenti estratti: {result['documents_extracted']}")
            print(f"⏱️  Tempo: {result['statistics']['extraction_time']:.1f} secondi")
            print(f"📊 Categorie: {len(result['statistics']['categories'])}")
            print(f"🏷️  Prodotti: {len(result['statistics']['product_coverage'])}")
            print(f"⭐ Qualità media: {result['statistics']['quality_scores']['avg_confidence']:.2f}")
            
            print("\n📋 TOP CATEGORIE:")
            for cat, count in sorted(result['statistics']['categories'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {cat}: {count} documenti")
            
            print("\n🏷️  TOP PRODOTTI:")
            for prod, count in sorted(result['statistics']['product_coverage'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   • {prod}: {count} documenti")
            
            print(f"\n💾 Knowledge base aggiornata: karray_rag/data/karray_knowledge.jsonl")
            print("🔧 Per utilizzare la nuova knowledge base, riavvia il sistema RAG")
            
        else:
            print(f"\n❌ ERRORE DURANTE L'ESTRAZIONE: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())