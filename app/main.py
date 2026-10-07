import os
from dotenv import load_dotenv
from openai import OpenAI


# ---------------------------------------
# 1. Load environment variables
# ---------------------------------------

load_dotenv()


# ---------------------------------------
# 2. Create Groq client
# ---------------------------------------

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


# ---------------------------------------
# 3. Python tools
# ---------------------------------------

def get_project_name():
    return "MCP-Powered Developer Assistant"


def get_developer_name():
    return "AI Developer"


# ---------------------------------------
# 4. Tool definitions
# ---------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_project_name",
            "description": "Returns the name of the project.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_developer_name",
            "description": "Returns the name of the developer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# ---------------------------------------
# 5. Tool registry
# ---------------------------------------

available_tools = {
    "get_project_name": get_project_name,
    "get_developer_name": get_developer_name
}


# ---------------------------------------
# 6. Conversation state
# ---------------------------------------

conversation = []


# ---------------------------------------
# 7. Chat loop
# ---------------------------------------

while True:

    question = input("You: ")

    if question.lower().strip() == "exit":
        print("Goodbye!")
        break

    # Add user message
    conversation.append({
        "role": "user",
        "content": question
    })

    # ---------------------------------------
    # First LLM call
    # ---------------------------------------

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=conversation,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message

    # ---------------------------------------
    # Check if model requested tools
    # ---------------------------------------

    if assistant_message.tool_calls:

        # IMPORTANT:
        # Save the assistant's tool-call message
        conversation.append(assistant_message)

        # Execute every requested tool
        for tool_call in assistant_message.tool_calls:

            function_name = tool_call.function.name

            print("Tool requested:", function_name)

            if function_name not in available_tools:
                continue

            function = available_tools[function_name]

            result = function()

            print("Tool result:", result)

            # Add tool result to conversation
            conversation.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        # ---------------------------------------
        # Second LLM call
        # ---------------------------------------

        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=conversation,
            tools=tools,
            tool_choice="none"
        )

        final_message = final_response.choices[0].message

        print("Assistant:", final_message.content)

        # Save final assistant response
        conversation.append(final_message)

    else:

        # Model answered without using a tool
        print("Assistant:", assistant_message.content)

        conversation.append(assistant_message)