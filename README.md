# MCP-Powered Developer Assistant

A command-line AI assistant that answers questions about a software project by **calling tools through the Model Context Protocol (MCP)**. The LLM (served by **Groq**) decides which tools to use: list the project's files, read a file, check `git status`. An MCP client runs those tools on an MCP server and sends the results back, repeating until the model can answer.

The project is built step by step; see [`PROJECT_ROADMAP.md`](PROJECT_ROADMAP.md) for the plan and the next features.

---

## What it can do

Ask questions about the project in plain English, for example:

- *"Which Python files are in this project?"*
- *"Read app/mcp_server.py and explain what each tool does."*
- *"Find the Python files and tell me what each one does."* (several tool calls in one request)
- *"What files have changed?"* (uses `git status`)
- *"What is the current working directory?"*

The model chooses the tools itself, and can call several in a row before answering.

---

## Why MCP?

Without MCP, every tool has to be written into the chat program, as in [`app/main.py`](app/main.py). With MCP:

- **Tools live in a separate server** ([`app/mcp_server.py`](app/mcp_server.py)), and any MCP-compatible client can use them.
- **The client discovers tools at runtime** (`list_tools()`), so adding a tool to the server needs no change in the client.
- **Each tool's name, description and input schema come from the server**, so they're defined in one place.

---

## Architecture

```text
User (terminal)
   │  question
   ▼
MCP client (app/mcp_client.py)
   │  1. discovers the tools on the MCP server
   │  2. sends the question + tool definitions to the LLM
   ▼
Groq LLM (openai/gpt-oss-20b, through Groq's OpenAI-compatible API)
   │  answers, or requests tool calls
   ▼
MCP client ── call_tool() over stdio ──► MCP server (app/mcp_server.py)
   ▲                                         │ runs the tool
   └──────────── tool result ◄───────────────┘
   │  results go back to the LLM; repeat (at most 10 rounds) until it answers
   ▼
Final answer printed in the terminal
```

---

## Project structure

```text
mp/
├── app/
│   ├── main.py            # Step 1: plain Groq function calling with two local Python tools (no MCP)
│   ├── mcp_server.py      # MCP server: the developer tools
│   └── mcp_client.py      # MCP client: tool discovery, the LLM ⇄ tool loop, chat
├── PROJECT_ROADMAP.md     # Plan, design principles and next steps
├── requirements.txt       # Pinned dependencies
└── .gitignore             # Keeps venv/ and .env (your API key) out of git
```

---

## MCP tools

Defined in [`app/mcp_server.py`](app/mcp_server.py):

| Tool | Arguments | What it returns |
|---|---|---|
| `list_files` | none | All project files, skipping virtual environments, `.git`, caches and build folders |
| `read_file` | `file_path` | The text of a file inside the project |
| `git_status` | none | `git status --short` for the project (read-only) |
| `get_current_directory` | none | The server's current working directory |
| `get_project_name` | none | The project name (a simple demo tool) |
| `get_developer_name` | none | The developer name (a simple demo tool) |

---

## Safety measures

The assistant reads your files on behalf of an LLM, so the tools are restricted:

- **Project-root restriction:** `read_file` resolves the path and refuses anything outside the project folder (for example `../../secret.txt`).
- **Ignored folders:** virtual environments (any folder containing `pyvenv.cfg`, as well as `venv`, `.venv` and `env`), `.git`, caches, `node_modules` and build folders are skipped by `list_files` and refused by `read_file`.
- **Text only:** files that aren't UTF-8 text are refused, not sent to the model.
- **No shell commands:** `git_status` runs a fixed command (`git status --short`) without `shell=True`, so the model can't run arbitrary commands.
- **A loop limit:** the client stops after 10 rounds of tool calls per question.

---

## Setup

Requirements: **Python 3.11** and a **Groq API key** (create one at https://console.groq.com/keys).

```bash
git clone https://github.com/hmadhe/mcp-developer-assistant.git
cd mcp-developer-assistant

python -m venv venv
venv\Scripts\activate          # Windows (PowerShell: .\venv\Scripts\Activate.ps1)
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

Create a file named **`.env`** in the project folder:

```text
GROQ_API_KEY=your-key-here
```

`.env` is listed in `.gitignore`, so the key is never committed.

---

## Running it

Run the commands **from the project folder**, with the virtual environment **activated**. The client starts the server with `python app/mcp_server.py`, so the active `python` must be the one with the dependencies installed.

**The MCP assistant:**

```bash
python app/mcp_client.py
```

It prints the tools it discovered, then waits for your questions. While it works, it shows which tools the model requested and what they returned. Type `exit` to quit.

**The earlier step, without MCP** (function calling with two local Python tools):

```bash
python app/main.py
```

---

## How the tool loop works

1. The client starts the MCP server and calls `list_tools()`.
2. Each MCP tool is converted to the OpenAI function-calling format that Groq accepts (name, description, JSON schema of its inputs).
3. For each question, the client sends the conversation and the tool definitions to the LLM.
4. If the LLM requests tools, the client parses each call's JSON arguments, runs the tool on the MCP server with `call_tool()`, and adds the result to the conversation as a `tool` message.
5. Steps 3–4 repeat until the LLM answers without requesting a tool, or until 10 rounds have run.

The conversation is kept across questions, so follow-up questions have context.

---

## Known limitations

- **Command-line only,** with one conversation at a time.
- **The model's argument names aren't validated yet.** The client fixes one known mismatch (`path` → `file_path` for `read_file`); better validation is on the roadmap.
- **Large files are sent whole** to the model; there's no size limit or line-range reading yet.
- **No automated tests yet** (planned in the roadmap).
- **Git support is read-only** and currently limited to `git status`.

See [`PROJECT_ROADMAP.md`](PROJECT_ROADMAP.md) for what's planned next: more Git tools (`git_log`, `git_diff`), better validation, a project summary tool, read-only SQLite tools, tests, and later LangGraph orchestration.
