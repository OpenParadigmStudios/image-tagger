# Setting Up UV for CivitAI Flux Dev LoRA Tagging Assistant

This guide will walk you through setting up the UV package manager for this project.

## What is UV?

UV is a fast Python package installer and resolver, built in Rust. It's designed to be significantly faster than pip while maintaining compatibility with the Python packaging ecosystem. UV also includes virtual environment management features.

## Step-by-Step Setup Guide

### 1. Verify Installation

You mentioned that you've already installed UV using Homebrew:

```bash
brew install uv
```

To verify it's properly installed, run:

```bash
uv --version
```

You should see the version information displayed.

### 2. Create a Virtual Environment

Navigate to your project directory:

```bash
cd /Users/jns/Documents/ai_art/src
```

Create a new virtual environment in the project directory:

```bash
uv venv
```

This creates a `.venv` directory in your project folder.

### 3. Activate the Virtual Environment

On macOS, activate the virtual environment:

```bash
source .venv/bin/activate
```

Your terminal prompt should change to indicate that you're now working within the virtual environment.

### 4. Install Dependencies

Install the project dependencies from the requirements.txt file:

```bash
uv pip install -r requirements.txt
```

This will install all required packages faster than traditional pip.

### 5. Verify Installation

Verify that the packages have been installed correctly:

```bash
uv pip list
```

You should see all the packages from requirements.txt listed.

## Using UV for Development

### Adding New Dependencies

When you need to add a new dependency to your project:

```bash
uv pip install <package-name>
```

And then update your requirements.txt:

```bash
uv pip freeze > requirements.txt
```

### Updating Dependencies

To update all dependencies to their latest versions:

```bash
uv pip install --upgrade -r requirements.txt
```

### Removing Dependencies

To remove a dependency:

```bash
uv pip uninstall <package-name>
```

And then update requirements.txt:

```bash
uv pip freeze > requirements.txt
```

## Running Your Application

With your virtual environment activated, run your application as normal:

```bash
python3 civitai_tagger.py /path/to/images
```

## Benefits of Using UV

- Faster package installation
- Improved dependency resolution
- Virtual environment management
- Compatible with the existing Python ecosystem
- Better performance for CI/CD pipelines

## Troubleshooting

If you encounter any issues with UV:

1. Ensure you have activated the virtual environment
2. Try updating UV: `brew upgrade uv`
3. Check the official UV documentation if needed

UV maintains compatibility with pip, so you can always fall back to pip commands if necessary. 