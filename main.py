import uuid
import time
from agents.context import AgentContext
from agents.orchestrator_agent import run as orchestrate
from utils.input_validator import validate_user_input, ValidationError

# ANSI terminal color codes
RED = "\x1b[31m"
GREEN = "\x1b[32m"
RESET = "\x1b[0m"

def generate_session_id() -> str:
    """Generate a unique session ID for security."""
    timestamp = str(int(time.time()))
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{unique_id}"

def generate_user_id() -> str:
    """Generate a unique user ID for this session."""
    return f"user_{str(uuid.uuid4())[:12]}"

def main():
    print("💬 Kchat\n")
    
    # Generate unique IDs for security
    session_id = generate_session_id()
    user_id = generate_user_id()
    
    print(f"Session ID: {session_id[:20]}...")
    print(f"User ID: {user_id[:15]}...\n")

    context = AgentContext(session_id=session_id, user_id=user_id, input="")

    while True:
        try:
            user_input = input(f"{RED}User:{RESET} ")
            
            # Check for exit commands before validation
            if user_input.strip().lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break
            
            # Validate and sanitize user input
            try:
                validated_input = validate_user_input(user_input, allow_empty=False)
            except ValidationError as e:
                print(f"{RED}⚠️ Input validation error: {e}{RESET}")
                print("Please try again with different input.\n")
                continue
            
            context.input = validated_input
            context = orchestrate(context)
            print(f"{GREEN}Bot:{RESET} {context.response}\n")
            
        except KeyboardInterrupt:
            print(f"\n{RED}Interrupted by user{RESET}")
            break
        except Exception as e:
            print(f"{RED}❌ Unexpected error: {e}{RESET}")
            print("Please try again.\n")

if __name__ == "__main__":
    main()
