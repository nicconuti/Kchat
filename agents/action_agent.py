"""Perform backend actions based on detected intents."""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from agents.context import AgentContext
from utils.logger import get_logger

logger = get_logger("action_log")

# Storage directory for backend data
BACKEND_DATA_DIR = Path("backend_data")
BACKEND_DATA_DIR.mkdir(exist_ok=True)

# Storage files
TICKETS_FILE = BACKEND_DATA_DIR / "tickets.json"
APPOINTMENTS_FILE = BACKEND_DATA_DIR / "appointments.json"
COMPLAINTS_FILE = BACKEND_DATA_DIR / "complaints.json"
REQUESTS_FILE = BACKEND_DATA_DIR / "requests.json"


def load_json_data(filepath: Path) -> Dict[str, Any]:
    """Load JSON data from file, create empty dict if file doesn't exist."""
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return {}


def save_json_data(filepath: Path, data: Dict[str, Any]) -> bool:
    """Save JSON data to file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")
        return False


def create_ticket(context: AgentContext) -> Dict[str, Any]:
    """Create a technical support ticket."""
    ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
    
    ticket = {
        'id': ticket_id,
        'user_id': context.user_id,
        'session_id': context.session_id,
        'type': 'technical_support',
        'status': 'open',
        'priority': 'medium',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'description': context.input,
        'language': context.language,
        'assigned_to': None,
        'resolution': None,
        'notes': []
    }
    
    # Load existing tickets
    tickets = load_json_data(TICKETS_FILE)
    tickets[ticket_id] = ticket
    
    # Save updated tickets
    if save_json_data(TICKETS_FILE, tickets):
        logger.info(f"Ticket created: {ticket_id}")
        return {
            'success': True,
            'ticket_id': ticket_id,
            'message': f"Ticket di supporto tecnico creato con ID: {ticket_id}. Il nostro team vi contatterà entro 24 ore."
        }
    else:
        return {
            'success': False,
            'message': "Errore nella creazione del ticket. Riprovare più tardi."
        }


def schedule_appointment(context: AgentContext) -> Dict[str, Any]:
    """Schedule an appointment or demo."""
    appointment_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    
    # Generate next available appointment slot (next business day at 10:00)
    next_day = datetime.now() + timedelta(days=1)
    while next_day.weekday() >= 5:  # Skip weekends
        next_day += timedelta(days=1)
    
    appointment_time = next_day.replace(hour=10, minute=0, second=0, microsecond=0)
    
    appointment = {
        'id': appointment_id,
        'user_id': context.user_id,
        'session_id': context.session_id,
        'type': 'consultation',
        'status': 'scheduled',
        'created_at': datetime.now().isoformat(),
        'scheduled_at': appointment_time.isoformat(),
        'duration_minutes': 60,
        'description': context.input,
        'language': context.language,
        'consultant_assigned': 'Auto-assigned',
        'meeting_link': f"https://meet.company.com/room/{appointment_id.lower()}",
        'notes': []
    }
    
    # Load existing appointments
    appointments = load_json_data(APPOINTMENTS_FILE)
    appointments[appointment_id] = appointment
    
    # Save updated appointments
    if save_json_data(APPOINTMENTS_FILE, appointments):
        logger.info(f"Appointment scheduled: {appointment_id}")
        return {
            'success': True,
            'appointment_id': appointment_id,
            'scheduled_time': appointment_time.strftime('%d/%m/%Y alle %H:%M'),
            'message': f"Appuntamento programmato per {appointment_time.strftime('%d/%m/%Y alle %H:%M')}. ID: {appointment_id}. Riceverete un link di conferma via email."
        }
    else:
        return {
            'success': False,
            'message': "Errore nella programmazione dell'appuntamento. Riprovare più tardi."
        }


def file_complaint(context: AgentContext) -> Dict[str, Any]:
    """File a formal complaint."""
    complaint_id = f"COMP-{uuid.uuid4().hex[:8].upper()}"
    
    complaint = {
        'id': complaint_id,
        'user_id': context.user_id,
        'session_id': context.session_id,
        'status': 'open',
        'priority': 'high',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'description': context.input,
        'language': context.language,
        'category': 'general',
        'assigned_to': 'Customer Service Manager',
        'resolution': None,
        'compensation_offered': None,
        'follow_up_date': (datetime.now() + timedelta(days=2)).isoformat(),
        'notes': []
    }
    
    # Load existing complaints
    complaints = load_json_data(COMPLAINTS_FILE)
    complaints[complaint_id] = complaint
    
    # Save updated complaints
    if save_json_data(COMPLAINTS_FILE, complaints):
        logger.info(f"Complaint filed: {complaint_id}")
        return {
            'success': True,
            'complaint_id': complaint_id,
            'message': f"Reclamo registrato con ID: {complaint_id}. Il nostro responsabile customer service vi contatterà entro 48 ore per risolvere la questione."
        }
    else:
        return {
            'success': False,
            'message': "Errore nella registrazione del reclamo. Riprovare più tardi."
        }


def handle_document_request(context: AgentContext) -> Dict[str, Any]:
    """Handle document requests."""
    request_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    
    request = {
        'id': request_id,
        'user_id': context.user_id,
        'session_id': context.session_id,
        'type': 'document_request',
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'description': context.input,
        'language': context.language,
        'requested_documents': [],
        'delivery_method': 'email',
        'estimated_delivery': (datetime.now() + timedelta(hours=2)).isoformat(),
        'notes': []
    }
    
    # Load existing requests
    requests = load_json_data(REQUESTS_FILE)
    requests[request_id] = request
    
    # Save updated requests
    if save_json_data(REQUESTS_FILE, requests):
        logger.info(f"Document request created: {request_id}")
        return {
            'success': True,
            'request_id': request_id,
            'message': f"Richiesta documenti registrata con ID: {request_id}. I documenti richiesti saranno inviati via email entro 2 ore."
        }
    else:
        return {
            'success': False,
            'message': "Errore nella registrazione della richiesta documenti. Riprovare più tardi."
        }


def handle_product_information(context: AgentContext) -> Dict[str, Any]:
    """Handle product information requests - log for analytics."""
    request_id = f"INFO-{uuid.uuid4().hex[:8].upper()}"
    
    request = {
        'id': request_id,
        'user_id': context.user_id,
        'session_id': context.session_id,
        'type': 'product_information',
        'created_at': datetime.now().isoformat(),
        'query': context.input,
        'language': context.language,
        'documents_provided': len(context.documents) if context.documents else 0,
        'satisfaction_rating': None
    }
    
    # Load existing requests
    requests = load_json_data(REQUESTS_FILE)
    requests[request_id] = request
    
    # Save updated requests
    if save_json_data(REQUESTS_FILE, requests):
        logger.info(f"Product information request logged: {request_id}")
        return {
            'success': True,
            'request_id': request_id,
            'message': "Richiesta informazioni prodotto elaborata e documentata."
        }
    else:
        return {
            'success': False,
            'message': "Errore nel logging della richiesta."
        }


def run(context: AgentContext) -> AgentContext:
    """Execute backend actions based on the detected intent."""
    try:
        action_result = None
        
        if context.intent == "technical_support_request":
            action_result = create_ticket(context)
            
        elif context.intent == "open_ticket":
            action_result = create_ticket(context)
            
        elif context.intent == "booking_or_schedule":
            action_result = schedule_appointment(context)
            
        elif context.intent == "complaint":
            action_result = file_complaint(context)
            
        elif context.intent == "document_request":
            action_result = handle_document_request(context)
            
        elif context.intent == "product_information_request":
            action_result = handle_product_information(context)
            
        elif context.intent == "cost_estimation":
            # Cost estimation is handled by quotation_agent, just log the request
            action_result = {
                'success': True,
                'message': "Richiesta preventivo elaborata dal sistema di quotazione."
            }
            
        elif context.intent == "generic_smalltalk":
            # No backend action needed for small talk
            action_result = {
                'success': True,
                'message': "Conversazione generale - nessuna azione backend richiesta."
            }
            
        else:
            # Unknown intent
            action_result = {
                'success': False,
                'message': f"Intent non riconosciuto: {context.intent}"
            }
        
        # Update context based on action result
        if action_result and action_result.get('success'):
            context.source_reliability = 0.9
            # Store action result in context for potential use by other agents
            if not hasattr(context, 'action_results'):
                context.action_results = []
            context.action_results.append(action_result)
        else:
            context.source_reliability = 0.3
            context.error_flag = True
            
        logger.info(
            f"backend action completed for intent {context.intent}",
            extra={
                "confidence_score": context.confidence,
                "source_reliability": context.source_reliability,
                "clarification_attempted": context.clarification_attempted,
                "error_flag": context.error_flag,
                "intent": context.intent,
                "action_success": action_result.get('success') if action_result else False,
                "action_id": action_result.get('ticket_id') or action_result.get('appointment_id') or 
                           action_result.get('complaint_id') or action_result.get('request_id', 'N/A') if action_result else 'N/A'
            },
        )
        
    except Exception as e:
        context.source_reliability = 0.1
        context.error_flag = True
        logger.error(f"Backend action failed for intent {context.intent}: {e}", exc_info=True)
    
    return context
