from mcp.server.mcpserver import MCPServer
from pathlib import Path
import os

mcp = MCPServer("Developer Assistant")


@mcp.tool()
def get_project_name() -> str:
    """Returns the name of the project."""
    return "MCP-Powered Developer Assistant"
@mcp.tool()
def get_developer_name() -> str:
    """Returns the developer name."""
    return "AI Developer"


@mcp.tool() 
def get_current_directory() -> str:
    """Returns the current working directory."""
    return os.getcwd()





# Anchor to the project, not to wherever the client was launched
PROJECT_ROOT = Path(__file__).resolve().parent.parent

IGNORED_DIRS = {
    ".venv", "venv", "env", ".env",
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", "build", "dist",
}


def is_ignored_dir(path: Path) -> bool:
    """True if this directory is ignored by name or is a virtual environment."""
    return (
        path.name in IGNORED_DIRS
        or path.name.endswith(".egg-info")
        or (path / "pyvenv.cfg").exists()   # catches venvs with any name
    )


def is_inside_ignored(path: Path) -> bool:
    """True if any parent directory of the path (within the project) is ignored."""
    for parent in path.relative_to(PROJECT_ROOT).parents:
        if parent != Path(".") and is_ignored_dir(PROJECT_ROOT / parent):
            return True
    return False


@mcp.tool()
def read_file(file_path: str) -> str:
    """Reads a text file inside the project directory."""
    requested_path = (PROJECT_ROOT / file_path).resolve()

    if PROJECT_ROOT not in requested_path.parents:
        return "Error: File is outside the project directory."
    if is_inside_ignored(requested_path):
        return "Error: File is in an ignored directory (e.g. virtual environment)."
    if not requested_path.is_file():
        return "Error: File does not exist."

    try:
        return requested_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "Error: File is not a UTF-8 text file."


@mcp.tool()
def list_files() -> str:
    """Lists project files, skipping virtual environments and tool/cache directories."""
    files = []
    for current_dir, dirs, filenames in os.walk(PROJECT_ROOT):
        current = Path(current_dir)
        dirs[:] = [d for d in dirs if not is_ignored_dir(current / d)]
        for filename in filenames:
            files.append(str((current / filename).relative_to(PROJECT_ROOT)))

    return "\n".join(sorted(files)) if files else "No files found."

@mcp.tool()
def git_status()-> str:
    """Returns the current git status of the project."""
    import subprocess

    try:
        result = subprocess.run(["git", "status", "--short"], 
                                cwd=PROJECT_ROOT,
                                capture_output=True,
                                text=True,
                                check=True)
        return result.stdout.strip() or "Working tree is clean ."
    except subprocess.CalledProcessError as e:
        return f"Git error: {e.stderr.strip()}"


    except FileNotFoundError:
        return "Error: Git is not installed or not found in PATH."
    
if __name__ == "__main__":
    mcp.run()