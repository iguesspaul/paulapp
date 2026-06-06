#!/bin/bash
set -e

echo "=== Remote Machine Setup Script ==="

# 1. Install Rust
if ! command -v rustc &> /dev/null; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo "Rust is already installed: $(rustc --version)"
fi

# 2. Install Hermes Agent
if ! command -v hermes &> /dev/null; then
    echo "Installing Hermes Agent..."
    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
    export PATH="$PATH:$HOME/.local/bin"
else
    echo "Hermes Agent is already installed."
fi

# 3. Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama is already installed: $(ollama --version)"
fi

# 4. Start Ollama and Pull Qwen model
echo "Starting Ollama service..."
if command -v systemctl &> /dev/null && systemctl is-active --quiet ollama; then
    echo "Ollama systemd service is already running."
else
    if command -v systemctl &> /dev/null; then
        echo "Starting Ollama systemd service..."
        sudo systemctl start ollama || true
    fi
    
    # If still not running, launch in the background
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo "Ollama is not running. Starting 'ollama serve' in the background..."
        nohup ollama serve > /dev/null 2>&1 &
        
        # Wait for Ollama to start
        echo -n "Waiting for Ollama to start"
        for i in {1..30}; do
            if curl -s http://localhost:11434/api/tags &> /dev/null; then
                echo " Success!"
                break
            fi
            echo -n "."
            sleep 1
        done
        if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
            echo " Error: Ollama failed to start."
            exit 1
        fi
    fi
fi

echo "Pulling Qwen 3.6 35B model..."
ollama pull qwen3.6:35b

echo "=== Setup Completed Successfully! ==="
