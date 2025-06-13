from pipeline import run_pipeline

if __name__ == "__main__":
    while True:
        user_input = input("Utente: ")
        if user_input.lower() in ["esci", "quit", "exit"]:
            break
        output = run_pipeline(user_input)
        print("Bot:", output)
