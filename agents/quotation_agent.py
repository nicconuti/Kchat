"""Generate a PDF quote with real implementation."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from agents.context import AgentContext
from utils.logger import get_logger

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = get_logger("quotation_log")


def extract_quote_items_from_documents(context: AgentContext) -> List[Dict[str, Any]]:
    """Extract quote items from retrieved documents."""
    quote_items = []
    
    for doc in context.documents:
        if hasattr(doc, 'metadata') and doc.metadata.get('category') == 'product_price':
            try:
                content = doc.content if hasattr(doc, 'content') else str(doc)
                
                # Try to parse structured product data
                if content.startswith('{') and content.endswith('}'):
                    import json
                    product_data = json.loads(content)
                    quote_items.append({
                        'description': product_data.get('description', 'Prodotto'),
                        'serial': product_data.get('serial', 'N/A'),
                        'price': product_data.get('price', 0.0),
                        'quantity': 1
                    })
                else:
                    # Fallback for unstructured content
                    quote_items.append({
                        'description': content[:100] + "..." if len(content) > 100 else content,
                        'serial': 'N/A',
                        'price': 0.0,
                        'quantity': 1
                    })
            except Exception as e:
                logger.warning(f"Error parsing document for quote: {e}")
                continue
    
    # If no items found, create a generic quote item
    if not quote_items:
        quote_items.append({
            'description': 'Servizio di consulenza personalizzato',
            'serial': 'CONS-001',
            'price': 150.0,
            'quantity': 1
        })
    
    return quote_items


def generate_pdf_quote(context: AgentContext, quote_items: List[Dict[str, Any]]) -> str:
    """Generate a PDF quote and return the file path."""
    if not REPORTLAB_AVAILABLE:
        logger.error("ReportLab not available, cannot generate PDF")
        return "Errore: libreria PDF non disponibile"
    
    # Create quotes directory if it doesn't exist
    quotes_dir = Path("quotes")
    quotes_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"preventivo_{context.user_id}_{timestamp}.pdf"
    filepath = quotes_dir / filename
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Build the story
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("PREVENTIVO", title_style))
        story.append(Spacer(1, 20))
        
        # Header information
        header_style = styles['Normal']
        story.append(Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}", header_style))
        story.append(Paragraph(f"<b>Cliente:</b> {context.user_id}", header_style))
        story.append(Paragraph(f"<b>Sessione:</b> {context.session_id}", header_style))
        story.append(Spacer(1, 20))
        
        # Quote items table
        table_data = [
            ['Descrizione', 'Codice/Serie', 'Quantità', 'Prezzo Unitario', 'Totale']
        ]
        
        total_amount = 0.0
        for item in quote_items:
            price = float(item.get('price', 0.0))
            quantity = int(item.get('quantity', 1))
            item_total = price * quantity
            total_amount += item_total
            
            table_data.append([
                item.get('description', 'N/A'),
                item.get('serial', 'N/A'),
                str(quantity),
                f"€ {price:.2f}",
                f"€ {item_total:.2f}"
            ])
        
        # Add total row
        table_data.append(['', '', '', '<b>TOTALE:</b>', f'<b>€ {total_amount:.2f}</b>'])
        
        # Create table
        table = Table(table_data, colWidths=[3*inch, 1.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        story.append(Paragraph("Preventivo valido 30 giorni dalla data di emissione.", footer_style))
        story.append(Paragraph("Per informazioni contattare il nostro ufficio commerciale.", footer_style))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF quote generated: {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error generating PDF quote: {e}")
        return f"Errore nella generazione del PDF: {str(e)}"


def run(context: AgentContext) -> AgentContext:
    """Generate a PDF quote based on the context and documents."""
    try:
        # Extract quote items from documents
        quote_items = extract_quote_items_from_documents(context)
        
        # Generate PDF
        pdf_path = generate_pdf_quote(context, quote_items)
        
        if pdf_path.startswith("Errore"):
            context.response = pdf_path
            context.source_reliability = 0.3
            context.error_flag = True
        else:
            context.response = f"Preventivo generato con successo. File salvato in: {pdf_path}"
            context.source_reliability = 0.95
        
        logger.info(
            "quote generation completed",
            extra={
                "confidence_score": context.confidence,
                "source_reliability": context.source_reliability,
                "clarification_attempted": context.clarification_attempted,
                "error_flag": context.error_flag,
                "pdf_path": pdf_path if not pdf_path.startswith("Errore") else None,
                "items_count": len(quote_items)
            },
        )
        
    except Exception as e:
        context.response = f"Errore durante la generazione del preventivo: {str(e)}"
        context.source_reliability = 0.1
        context.error_flag = True
        logger.error(f"Quote generation failed: {e}", exc_info=True)
    
    return context
