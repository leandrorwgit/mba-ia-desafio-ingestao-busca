from search import search_prompt


def main():
    print("Faça sua pergunta: ('q' para sair)")
    try:
        while True:
            try:
                user_input = input("PERGUNTA: ").strip()
            except EOFError:
                print("\nFinalizando...")
                break

            if user_input.lower() in {"q", "quit", "exit", "sair"}:
                print("\nFinalizando...")
                break

            if not user_input:
                continue

            response = search_prompt(user_input)
            if response is None:
                continue

            print(f"RESPOSTA: {response}\n")
    except KeyboardInterrupt:
        print("\nFinalizando...")


if __name__ == "__main__":
    main()