# MCP Azure DevOps Server

A Model Context Protocol (MCP) server enabling AI assistants to interact with Azure DevOps services. This is a Python-based server built with the MCP SDK that provides tools for work item management, project administration, and team operations.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap and Setup Environment
1. **Install uv package manager**: `python3 -m pip install uv` -- takes 5-10 seconds
2. **Create virtual environment**: `uv venv` -- takes under 1 second
3. **Activate virtual environment**: `source .venv/bin/activate`
4. **Install project dependencies**: `uv pip install -e ".[dev]"` -- takes 6-10 seconds. NEVER CANCEL. Set timeout to 60+ seconds.
5. **Configure environment**: Create `.env` file with:
   ```
   AZURE_DEVOPS_PAT=your_personal_access_token
   AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-organisation
   ```

### Build and Test Commands
- **Run tests**: `uv run pytest tests/` -- takes 1-2 seconds. NEVER CANCEL. Set timeout to 30+ seconds.
  - 62/63 tests typically pass (1 test may fail due to missing trio module, which is expected and harmless)
- **Run linting**: `uv run ruff check .` -- takes under 1 second
  - May show line length warnings (29 errors typical) which are acceptable
- **Fix linting issues**: `uv run ruff check --fix .` -- takes under 1 second  
- **Format code**: `uv run ruff format .` -- takes under 1 second (may report "X files left unchanged")
- **Type checking**: `uv run pyright src/` -- takes 2-3 seconds. NEVER CANCEL. Set timeout to 30+ seconds.
  - Should report "0 errors, 0 warnings, 0 informations"

### Run the Server
- **Development mode with MCP Inspector**: `uv run mcp dev src/mcp_azure_devops/server.py`
  - Requires internet access to download MCP Inspector npm package
- **Direct server execution**: `uv run python src/mcp_azure_devops/server.py`
- **Using helper script**: `./start_server.sh` (requires virtual environment activation)

### Alternative Setup Using Setup Script
- **Linux/macOS**: `./setup_environment.sh` (interactive, sets up everything including Claude Desktop integration)
- **Windows**: `./setup_environment.ps1` (PowerShell version)

## Validation
- **ALWAYS run the complete test suite after making code changes** using `uv run pytest tests/`
  - Expected: 62/63 tests pass (1 trio-related failure is normal)
- **ALWAYS run linting and formatting** before committing: `uv run ruff check --fix . && uv run ruff format .`
  - Line length warnings are acceptable (this codebase has intentionally long doc strings)
- **ALWAYS run type checking** for critical changes: `uv run pyright src/`
  - Expected: "0 errors, 0 warnings, 0 informations"
- **Test server startup** by running `uv run python src/mcp_azure_devops/server.py` and verifying it starts without errors
- **Test module imports**: `python3 -c "from mcp_azure_devops.server import mcp; print('Server imports successfully')"`
- **Manual functional testing**: If you modify tools or features, test them by running the server and using an MCP client to invoke the tools

## Key Project Structure

### Source Code (`src/mcp_azure_devops/`)
- `server.py`: Main MCP server entry point and FastMCP setup
- `features/`: Feature modules organized by Azure DevOps capabilities
  - `work_items/`: Work item management (create, read, update, query, comments, attachments)
  - `projects/`: Project management and metadata
  - `teams/`: Team operations and member management
- `utils/`: Shared utilities (Azure client, prompts)

### Tests (`tests/`)
- Mirror structure of `src/` directory
- Use `pytest` with `anyio` for async testing
- Mock Azure DevOps API responses for deterministic testing

### Configuration Files
- `pyproject.toml`: Project configuration, dependencies, and tool settings
- `.env`: Environment variables (Azure DevOps PAT and organization URL)
- `uv.lock`: Dependency lock file for reproducible builds

## Common Patterns and Conventions

### Error Handling
- Use `AzureDevOpsClientError` for Azure DevOps-specific errors
- Return error messages as strings from MCP tools
- Always wrap Azure DevOps client calls in try-except blocks

### Tool Implementation
- Private implementation functions: `_tool_name_impl(client, params)`
- Public MCP tool functions with proper error handling and client initialization
- Detailed docstrings following the established pattern

### Code Style
- Line length: 79 characters (enforced by ruff)
- Use type hints for all function parameters and returns
- Import sorting: standard library → third-party → local imports

## Development Workflow
1. **Create feature branch** from main
2. **Make minimal changes** focusing on single responsibilities
3. **Run tests frequently**: `uv run pytest tests/` during development
4. **Lint and format**: `uv run ruff check --fix . && uv run ruff format .`
5. **Type check critical changes**: `uv run pyright src/`
6. **Test server functionality** by running and testing tools
7. **Commit with descriptive messages** following conventional commit format

## Troubleshooting
- **Import errors**: Ensure virtual environment is activated and dependencies installed
- **Azure DevOps connection errors**: Verify PAT token has correct permissions and organization URL is valid
- **Test failures**: Single trio-related test failure is expected; other failures indicate real issues
- **Linting errors**: Run `uv run ruff check --fix .` to auto-fix most formatting issues
- **Server won't start**: Check `.env` file exists with valid Azure DevOps credentials

## Performance Expectations
- **Installation**: 6-10 seconds for full dependency installation
- **Tests**: 1-2 seconds for complete test suite (63 tests)
- **Linting/Formatting**: Under 1 second each
- **Type checking**: 2-3 seconds
- **Server startup**: Under 2 seconds for basic startup
- **Module import**: Instantaneous for testing imports

**NEVER CANCEL long-running operations.** All build and test commands complete within 10 seconds under normal conditions.