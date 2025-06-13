from pipeline import run_pipeline_stream

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

if __name__ == "__main__":
    while True:
        user_input = input(f"{RED}[User]{RESET}: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        stream = run_pipeline_stream(user_input)
        try:
            first = next(stream)
        except StopIteration:
            first = ""
        print(f"{GREEN}[Bot] ", end="", flush=True)
        if first:
            print(first, end="", flush=True)
        for token in stream:
            print(token, end="", flush=True)
        print(RESET)
