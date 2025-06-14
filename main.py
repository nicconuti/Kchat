from agents.context import AgentContext
from agents.orchestrator_agent import run as orchestrate

# ANSI terminal color codes
RED = "\x1b[31m"
GREEN = "\x1b[32m"
RESET = "\x1b[0m"

def main():
    print("💬 Kchat\n")

    context = AgentContext(session_id='qwerty', user_id="power_user", input="")

    while True:
        user_input = input(f"{RED}User:{RESET} ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break

        context.input = user_input
        context = orchestrate(context)
        print(f"{GREEN}Bot:{RESET} {context.response}\n")

if __name__ == "__main__":
    main()
