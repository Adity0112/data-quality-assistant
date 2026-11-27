
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage


# ------------------------------------------------
# 1. PAGE CONFIGURATION
# ------------------------------------------------

st.set_page_config(
    page_title="Data Quality AI Assistant",
    page_icon="🤖",
    layout="wide"
)


# ------------------------------------------------
# 2. APPLICATION HEADER
# ------------------------------------------------

st.title("🤖 Data Quality AI Assistant")

st.caption(
    "Your AI assistant for Databricks data quality analysis."
)

st.divider()


# ------------------------------------------------
# 3. INITIALIZE CHAT HISTORY
# ------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------
# 4. DISPLAY PREVIOUS CHAT MESSAGES
# ------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ------------------------------------------------
# 5. USER INPUT
# ------------------------------------------------

user_input = st.chat_input(
    "Ask something about your data quality..."
)


# ------------------------------------------------
# 6. PROCESS USER QUESTION
# ------------------------------------------------

if user_input:

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    try:

        with st.chat_message("assistant"):

            with st.spinner("Analyzing your request..."):

                # Import graph only when required
                from agent.graph import graph

                # Convert chat history into LangChain messages
                messages = []

                for message in st.session_state.messages:

                    if message["role"] == "user":

                        messages.append(
                            HumanMessage(
                                content=message["content"]
                            )
                        )

                    elif message["role"] == "assistant":

                        messages.append(
                            AIMessage(
                                content=message["content"]
                            )
                        )

                # Execute LangGraph
                response = graph.invoke({
                    "messages": messages
                })

                # Get AI response
                ai_message = response["messages"][-1]

                ai_response = ai_message.content

                if not ai_response:
                    ai_response = "The agent returned an empty response."

                # Display AI response
                st.markdown(ai_response)

                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_response
                })

    except Exception as e:

        st.error(
            f"Something went wrong: {str(e)}"
        )

        print("\n========== LANGGRAPH ERROR ==========")
        print(str(e))


# ------------------------------------------------
# 7. SIDEBAR
# ------------------------------------------------

with st.sidebar:

    st.title("⚙️ Settings")

    st.write("Data Quality AI Assistant")

    st.divider()

    if st.button("Clear Chat", use_container_width=True):

        st.session_state.messages = []

        st.rerun()
