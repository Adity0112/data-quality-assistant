
from agent.graph import graph


def run_chatbot():

    print("\n========================================")
    print("       DATA QUALITY AI ASSISTANT")
    print("========================================")

    print("\nAsk me anything about your data quality.")
    print("Type 'exit' to close the assistant.")

    # Store conversation messages
    messages = []

    while True:

        # 1. Get user input
        user_input = input("\nYou: ").strip()

        # 2. Exit condition
        if user_input.lower() in ["exit", "quit"]:
            print("\nAssistant: Goodbye!")
            break

        if not user_input:
            continue

        try:

            # 3. Add user message
            messages.append(("user", user_input))

            # 4. Execute LangGraph
            response = graph.invoke({
                "messages": messages
            })

            # 5. Update conversation history
            messages = response["messages"]

            # 6. Display final response
            ai_response = messages[-1]

            print("\nAssistant:")
            print(ai_response.content)

        except Exception as e:

            print("\nError:", str(e))


if __name__ == "__main__":
    run_chatbot()
