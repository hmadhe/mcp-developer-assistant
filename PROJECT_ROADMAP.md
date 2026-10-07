# MCP-Powered Developer Assistant — Product Roadmap

## 1. Current Status

The project currently has a working end-to-end MCP tool-calling flow.

Current architecture:

```text
User
  ↓
Groq LLM
  ↓
MCP Client
  ↓
MCP Server
  ├── get_project_name
  ├── get_developer_name
  ├── get_current_directory
  ├── read_file
  └── list_files
```

The assistant can:

- Discover MCP tools dynamically.
- Send MCP tools to the LLM as function tools.
- Let the LLM decide when a tool is useful.
- Execute MCP tools through the MCP client.
- Return tool results to the LLM.
- Perform multiple tool calls in one user request.
- Read project files safely.
- Ignore virtual environments, `.git`, caches, build folders, etc.
- Produce a final natural-language answer after tool execution.

Example working flow:

```text
User:
"Find the Python files in my project and tell me what each one does."

        ↓

LLM
        ↓
list_files()
        ↓
MCP Server
        ↓
file list
        ↓
LLM decides more information is needed
        ↓
read_file("app/mcp_client.py")
        ↓
MCP Server
        ↓
file contents
        ↓
read_file("app/mcp_server.py")
        ↓
MCP Server
        ↓
file contents
        ↓
LLM
        ↓
Final answer
```

This is an important milestone. The MCP foundation and multi-step tool-calling loop are working.

---

# 2. Development Philosophy

Do NOT turn this into a huge framework immediately.

Continue with:

```text
Build small
   ↓
Run
   ↓
Test
   ↓
Debug
   ↓
Understand
   ↓
Improve
   ↓
Next feature
```

The goal is to build a product that is:

- understandable
- reliable
- secure
- testable
- useful to developers
- resume-worthy
- appropriate for an AI developer with around 1 year of experience

Avoid adding complexity only because a technology is popular.

---

# 3. Immediate Next Step — Git MCP Tools

The next milestone should be adding Git capabilities to the MCP server.

Start with ONE tool.

Recommended first tool:

```text
git_status
```

Expected user experience:

```text
You:
"What files have changed in my project?"

Assistant:
"I'll check the Git status."

→ git_status()

Assistant:
"You have 2 modified files:
- app/mcp_client.py
- app/mcp_server.py"
```

## Why Git is the next step

The assistant is currently able to understand the filesystem.

Git gives it awareness of the project's development state.

This moves the project from:

```text
File assistant
```

toward:

```text
Developer assistant
```

---

# 4. Git Tool Roadmap

Add Git tools incrementally.

## Phase 1 — Read-only Git tools

Start here.

- [ ] `git_status`
- [ ] `git_log`
- [ ] `git_diff`

These tools should initially be READ-ONLY.

The assistant should be able to answer questions such as:

```text
What changed in my project?

What was my last commit?

Show me the changes in mcp_server.py.

What files are currently modified?
```

## Phase 2 — More Git information

Later:

- [ ] current branch
- [ ] recent commits
- [ ] commit details
- [ ] branch list

## Phase 3 — Git actions

Only after the read-only tools are reliable:

- [ ] create commit
- [ ] create branch
- [ ] checkout branch
- [ ] stage files

These are potentially destructive or state-changing operations.

They should NOT be added casually.

---

# 5. Security Rules

Security becomes increasingly important as the assistant gets more powerful.

## Filesystem

The current `read_file` implementation already protects against paths escaping the project directory.

Keep this rule:

```text
Assistant can access:
    project/
        ↓
        allowed files

Assistant cannot access:
    ../../private_file
    /etc/passwd
    arbitrary system paths
```

Continue applying the same project-root restriction to future filesystem tools.

## Git

Git commands should execute against the intended project repository.

Do not allow the LLM to freely construct arbitrary shell commands.

Prefer:

```python
subprocess.run(
    ["git", "status", "--short"],
    ...
)
```

over:

```python
subprocess.run(user_generated_command, shell=True)
```

Avoid `shell=True` unless there is a very specific and justified reason.

---

# 6. Tool Design Principles

Every MCP tool should have:

1. A clear name.
2. A useful description.
3. A small responsibility.
4. Predictable input.
5. Predictable output.
6. Good error handling.

Example:

```text
git_status
```

is better than:

```text
run_any_git_command
```

The second tool gives the model too much freedom and makes security harder.

Prefer several focused tools:

```text
git_status
git_log
git_diff
```

instead of:

```text
execute_git(command)
```

---

# 7. Improve Error Handling

Current error handling is good enough for development, but should become more structured.

Instead of returning only:

```text
Error: File does not exist.
```

we can eventually standardize tool results.

Example:

```json
{
  "success": false,
  "error": "FILE_NOT_FOUND",
  "message": "The requested file does not exist."
}
```

Successful result:

```json
{
  "success": true,
  "data": "..."
}
```

Do this gradually.

Do NOT redesign every existing tool immediately.

---

# 8. Improve Tool Argument Validation

The LLM may sometimes generate arguments that do not exactly match the expected schema.

Example:

Expected:

```json
{
  "file_path": "app/main.py"
}
```

Model might generate:

```json
{
  "path": "app/main.py"
}
```

The current client contains compatibility handling for this.

Keep this temporarily while learning.

Later, improve the tool schemas and validation so that the model is more likely to produce the correct structure.

Potential future approach:

```text
LLM
 ↓
Pydantic validation
 ↓
Validated arguments
 ↓
MCP tool
```

This is one area where Pydantic can eventually become useful.

---

# 9. Tool Output Size

A future problem will be large files.

For example:

```text
read_file("huge_file.py")
```

could return thousands of lines.

That creates:

```text
Large tool result
      ↓
Large LLM context
      ↓
Higher latency
      ↓
Higher token usage
```

Improve this later by supporting things such as:

```text
read_file(file_path)
read_file(file_path, start_line, end_line)
```

or:

```text
read_file(...)
```

with a maximum output size.

Do not optimize this before it becomes a real problem.

---

# 10. Add a Project Summary Tool

After Git tools, a useful product feature would be:

```text
project_summary
```

The assistant could answer:

```text
What is this project?

What technologies are being used?

What files are important?

How is the project structured?
```

Possible information:

```text
Project name
Python version
Dependencies
Important directories
Git status
Main application files
MCP tools
README
```

This can eventually become a strong "developer onboarding" feature.

---

# 11. SQLite MCP Tools

After filesystem + Git, add SQLite.

Possible tools:

```text
list_tables
describe_table
query_database
```

Start READ-ONLY.

Example:

```text
User:
"What tables are in the database?"

LLM
 ↓
list_tables()
 ↓
MCP
 ↓
SQLite
 ↓
result
 ↓
LLM
```

Do NOT initially allow:

```text
DELETE
DROP
UPDATE
```

Read-only database access is enough to demonstrate the concept.

---

# 12. Testing Strategy

The project should eventually have tests.

Start small.

## Unit tests

Test individual functions:

```text
read_file()
list_files()
is_ignored_dir()
is_inside_ignored()
```

Examples:

- Can read a valid file?
- What happens with a missing file?
- What happens with a binary file?
- Can the tool escape the project directory?
- Are `.venv` files excluded?

## MCP integration tests

Test:

```text
MCP client
    ↓
MCP server
    ↓
tool
    ↓
result
```

## LLM integration tests

Eventually test scenarios such as:

```text
Question
   ↓
Expected tool
   ↓
Expected result
   ↓
Final answer
```

Do not try to build a huge test framework at once.

---

# 13. Improve Observability

As the project grows, debugging tool calls will become harder.

Eventually add structured logging.

Useful information:

```text
timestamp
user request
LLM response
selected tool
tool arguments
tool execution time
tool result status
errors
```

Example:

```text
[INFO] Tool requested: list_files
[INFO] Tool completed: list_files
[INFO] Duration: 12ms
```

Remember:

MCP stdio uses stdout for protocol communication.

Do not print debugging information to MCP stdout.

Use stderr or a proper logging system.

---

# 14. LangGraph — Later, Not Now

Do not add LangGraph yet.

The current manual loop is important because it teaches the underlying mechanism.

Current:

```text
while loop
    ↓
LLM
    ↓
tool?
    ↓
execute tool
    ↓
LLM again
```

Later LangGraph can represent this as a graph:

```text
START
  ↓
LLM
  ↓
Tool needed?
 ┌───────┴───────┐
No              Yes
 ↓               ↓
END          Execute tool
                ↓
               LLM
                ↓
               ...
```

LangGraph should solve an orchestration problem, not just be added because it is popular.

---

# 15. Future Architecture

A more mature version could look like:

```text
                    User
                      ↓
                AI Assistant
                      ↓
                 LangGraph
                      ↓
                 MCP Client
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
 Filesystem          Git          SQLite
 MCP Server       MCP Server     MCP Server
        ↓             ↓             ↓
     Project       Repository    Database
```

Eventually there could be multiple MCP servers rather than putting every tool into one server.

---

# 16. Product-Level Features

After the core system is stable, consider:

## Developer onboarding

```text
"Explain this project to me."
```

## Code exploration

```text
"Where is authentication implemented?"
```

## Git understanding

```text
"What changed since yesterday?"
```

## Debugging assistance

```text
"Find files related to this error."
```

## Project health

```text
"Give me a quick project health report."
```

## Database exploration

```text
"Show me the database schema."
```

## Change explanation

```text
"Explain the current Git diff."
```

These features should emerge from reliable tools rather than from one giant tool.

---

# 17. Possible Future Tool Set

A reasonable mature tool set could be:

### Filesystem

```text
list_files
read_file
search_files
```

### Git

```text
git_status
git_log
git_diff
git_branches
```

### SQLite

```text
list_tables
describe_table
query_database
```

### Project

```text
project_summary
project_structure
```

Avoid creating dozens of tools without a clear product reason.

---

# 18. Reliability Improvements

Eventually handle:

- [ ] MCP server unavailable
- [ ] tool execution timeout
- [ ] invalid tool arguments
- [ ] malformed model tool calls
- [ ] tool returning an error
- [ ] very large tool output
- [ ] repeated tool calls
- [ ] maximum iteration limit
- [ ] unknown tool requested by model
- [ ] malformed JSON
- [ ] missing environment variables
- [ ] Git command failure
- [ ] non-Git project
- [ ] SQLite connection failure

The existing `max_iterations` safeguard should remain.

---

# 19. User Experience Improvements

Current:

```text
LLM requested tool:
- list_files
```

Later, make the interface cleaner.

For example:

```text
You: What changed in my project?

● Checking Git status...
✓ Found 3 modified files.

Assistant:
You have 3 modified files...
```

The user should understand what the assistant is doing without seeing excessive implementation details.

Keep detailed logs available for development/debug mode.

---

# 20. Configuration

Eventually move configuration into environment variables.

Examples:

```text
GROQ_API_KEY
MODEL_NAME
PROJECT_ROOT
MAX_TOOL_ITERATIONS
```

Do not hard-code secrets.

Keep `.env` out of Git.

---

# 21. Documentation

Eventually add:

```text
README.md
ARCHITECTURE.md
PROJECT_ROADMAP.md
```

README should explain:

- What the project does.
- Why MCP is used.
- Architecture.
- Setup.
- How to run it.
- Available tools.
- Example conversations.

Architecture documentation should explain:

```text
User
 ↓
LLM
 ↓
MCP Client
 ↓
MCP Server
 ↓
Tools
```

This will also make the project easier to explain during interviews.

---

# 22. Resume-Worthy Final Version

A strong final project does NOT need 50 features.

A better target is:

```text
Reliable MCP-powered developer assistant
        +
Filesystem tools
        +
Git tools
        +
SQLite tools
        +
Safe tool execution
        +
Multi-step reasoning
        +
Validation
        +
Testing
        +
LangGraph orchestration
        +
Good documentation
```

The important part is being able to explain every layer.

You should be able to answer:

```text
Why MCP?

Why not directly call Python functions?

How does the LLM know which tools exist?

How are tools discovered?

How are tool arguments generated?

How does the client execute the tool?

How does the tool result return to the LLM?

How do you prevent filesystem traversal?

How do you prevent dangerous commands?

Why use LangGraph?

How do you test the system?
```

---

# 23. Recommended Development Order

Follow this order.

## Completed

- [x] Basic Python project
- [x] Groq LLM connection
- [x] Interactive chat
- [x] Conversation memory
- [x] Basic function calling
- [x] MCP server
- [x] MCP client
- [x] MCP tool discovery
- [x] LLM → MCP tool execution
- [x] `read_file`
- [x] `list_files`
- [x] Multi-step tool calling
- [x] Tool-call iteration limit
- [x] Basic argument compatibility handling
- [x] Safe project-root filesystem access
- [x] Ignoring virtual environments/cache directories

## Next

- [ ] Add `git_status`
- [ ] Test `git_status`
- [ ] Add `git_log`
- [ ] Test `git_log`
- [ ] Add `git_diff`
- [ ] Test `git_diff`
- [ ] Improve Git error handling

## Then

- [ ] Add better tool validation
- [ ] Add search_files
- [ ] Improve large-file handling
- [ ] Add project summary
- [ ] Add SQLite read-only tools
- [ ] Add unit tests
- [ ] Add MCP integration tests
- [ ] Add logging/observability

## Later

- [ ] Introduce LangGraph
- [ ] Separate MCP servers if useful
- [ ] Improve UX
- [ ] Add configuration
- [ ] Add stronger security controls
- [ ] Improve documentation

---

# 24. Current Next Task

Do only this next:

```text
Add git_status to mcp_server.py
```

The intended flow is:

```text
User
 ↓
"What files are modified?"
 ↓
LLM
 ↓
git_status
 ↓
MCP server
 ↓
git status output
 ↓
LLM
 ↓
Answer
```

Do not implement all Git tools at once.

After `git_status` works:

```text
Build
 ↓
Run
 ↓
Test
 ↓
Debug
 ↓
Understand
```

Then move to `git_log`.

---

# 25. Project Rule

Whenever adding a new capability, ask:

```text
1. Does this solve a real developer problem?
2. Can I implement it as a small MCP tool?
3. Is the tool safe?
4. Can I test it?
5. Can I explain how it works?
```

If the answer is yes, add it.

If the feature only adds complexity without improving the product, postpone it.

---

# 26. Final Target

The goal is not:

```text
"I built an AI chatbot."
```

The goal is:

```text
"I built a tool-using AI developer assistant that
discovers and executes MCP tools for filesystem,
Git, and database operations, supports multi-step
tool calling, validates and secures tool execution,
and uses graph-based orchestration for more complex
developer workflows."
```

Build toward that gradually.

---

# CHANGE LOG

Update this section whenever the architecture changes.

## Current

```text
MCP server:
- get_project_name
- get_developer_name
- get_current_directory
- read_file
- list_files

MCP client:
- tool discovery
- Groq tool conversion
- multi-step tool loop
- argument parsing
- tool execution
- iteration limit

Security:
- project-root restriction
- ignored directories
- UTF-8 validation
```

## Next change

```text
Add:
- git_status
```

After implementing it, update the checklist and describe what changed.

---

# IMPORTANT

Do not treat this document as a requirement to implement everything.

It is a roadmap.

The development process should remain incremental:

```text
One feature
    ↓
Understand it
    ↓
Test it
    ↓
Keep it
    ↓
Next feature
```
