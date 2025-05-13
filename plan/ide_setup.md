# IDE Configuration for CivitAI Flux Dev LoRA Tagging Assistant

This document explains how the project is configured to work with Cursor IDE and VS Code.

## Configuration Files

### `.vscode/settings.json`

This file configures VS Code settings (which Cursor IDE also uses):

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python3",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ],
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "autopep8",
    "editor.formatOnSave": true,
    "editor.insertSpaces": true,
    "editor.tabSize": 4,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}
```

This configuration:
- Sets the Python interpreter to the virtual environment created by UV
- Automatically activates the virtual environment in terminals
- Enables linting and formatting
- Configures editor behavior to match our style guidelines

### `.python-version`

This file specifies the Python version for tools that support it:

```
3.12.9
```

### `.gitignore`

The `.gitignore` file excludes virtual environments and other generated files from version control.

### `activate_env.sh`

This script provides a convenient way to activate the virtual environment:

```bash
#!/bin/bash
# Script to activate the virtual environment for this project

# Path to the virtual environment
VENV_PATH="$(pwd)/.venv"

if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_PATH"
    source "$VENV_PATH/bin/activate"
    echo "Python interpreter: $(which python3)"
    echo "Python version: $(python3 --version)"
    echo "Installed packages:"
    uv pip list
else
    echo "Virtual environment not found at $VENV_PATH"
    echo "Please run 'uv venv' to create a virtual environment"
fi
```

## Using with Cursor IDE

When opening the project in Cursor IDE:

1. The IDE will automatically use the Python interpreter specified in `.vscode/settings.json`
2. The virtual environment will be activated in any integrated terminals
3. Code completion, linting, and other features will use the project's virtual environment

## Manual Setup

If you need to manually configure Cursor IDE or VS Code:

1. Open the project folder in the IDE
2. Open Command Palette (Cmd+Shift+P or Ctrl+Shift+P)
3. Select "Python: Select Interpreter"
4. Choose the interpreter at `.venv/bin/python3`

## Troubleshooting

If the IDE is not using the correct virtual environment:

1. Check that the `.venv` directory exists in the project root
2. Ensure `.vscode/settings.json` has the correct interpreter path
3. Reload the IDE window
4. Try manually activating the environment with `./activate_env.sh`
