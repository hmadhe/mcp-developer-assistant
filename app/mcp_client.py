
import asyncio
import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from mcp import Client, StdioServerParameters


# -----------------------------
# Load environment variables
# -----------------------------

load_dotenv()


# -----------------------------
# Groq client
# -----------------------------

llm = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


# -----------------------------
# MCP server configuration
# -----------------------------

server = StdioServerParameters(
    command="python",
    args=["app/mcp_server.py"],
)


# -----------------------------
# Main
# -----------------------------

async def main():

    async with Client(server) as client:

        # 1. Discover MCP tools
        mcp_tools_result = await client.list_tools()

        print("Available MCP tools:")

        for tool in mcp_tools_result.tools:
            print("-", tool.name)

        # 2. Convert MCP tools into Groq tool format
        tools = []

        for tool in mcp_tools_result.tools:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
            )

        print("\nTools sent to LLM:")

        for tool in tools:
            print("-", tool["function"]["name"])

        # 3. Conversation history
        messages = [
            {
               "role": "system",
        "content": (
            "You are a developer assistant. "
            "Use the available tools when useful. "
            "The list_files tool takes no arguments and must be called with {}. "
            "The read_file tool requires the argument file_path."
        ),  
            }
        ]

        # 4. Start chat loop
        while True:

            question = input("You: ")

            if question.lower().strip() == "exit":
                print("Goodbye!")
                break

            messages.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

            # -----------------------------------------
            # LLM ↔ MCP tool loop
            # -----------------------------------------

            max_iterations = 10
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                response = llm.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )

                assistant_message = response.choices[0].message

                # -------------------------------------
                # No tool requested → final answer
                # -------------------------------------

                if not assistant_message.tool_calls:
                    print("\nAssistant:")
                    print(assistant_message.content)

                    messages.append(assistant_message)

                    break

                # -------------------------------------
                # Tool(s) requested
                # -------------------------------------

                print("\nLLM requested tool:")

                # Save assistant's tool-call message
                messages.append(assistant_message)

                for tool_call in assistant_message.tool_calls:

                    tool_name = tool_call.function.name

                    print("-", tool_name)

                    # Convert JSON string → Python dictionary
                    try:
                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                    except json.JSONDecodeError:
                        print(
                            "Invalid JSON in tool arguments:",
                            tool_call.function.arguments,
                        )
                        continue

                    # Handle common argument-name mismatch
                    if (
    tool_name == "read_file"
    and "path" in arguments
    and "file_path" not in arguments
                     ):
                        arguments["file_path"] = arguments.pop("path")

                    # Execute MCP tool
                    result = await client.call_tool(
                        tool_name,
                        arguments,
                    )

                    # Extract MCP result
                    tool_result = result.structured_content["result"]

                    print("MCP result:", tool_result)

                    # Send MCP result back to LLM
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        }
                    )

            if iteration >= max_iterations:
                print("\nAssistant:")
                print("I stopped because the tool-call limit was reached.")


if __name__ == "__main__":
    asyncio.run(main())

