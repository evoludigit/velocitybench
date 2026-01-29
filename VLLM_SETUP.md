# vLLM Server Setup Guide

## Problem

When running `make comments-generate`, you get an error:
```
Error: vLLM server not running at localhost:8000
Start it with: vllm-switch implementer
```

Running `vllm-switch implementer` directly or via `make vllm-start` fails with:
```
sudo: a terminal is required to read the password
```

## Root Cause

The `vllm-switch` command uses `sudo systemctl` to manage the vLLM systemd service. Without passwordless sudo configuration, sudo requires interactive password authentication, which fails in non-interactive contexts (like Makefiles).

## Solution

Configure sudo to allow `vllm-switch` operations without password authentication:

### Step 1: Open sudoers editor
```bash
sudo visudo
```

### Step 2: Add this line
At the end of the file, add:
```
lionel ALL=(ALL) NOPASSWD: /usr/bin/systemctl start vllm,/usr/bin/systemctl stop vllm,/usr/bin/systemctl daemon-reload,/usr/bin/tee /etc/systemd/system/vllm.env
```

**Important:** Replace `lionel` with your actual username!

### Step 3: Save and verify

- Save the file (in `visudo`, press `Ctrl+O`, then `Enter`, then `Ctrl+X`)
- Verify it works:
  ```bash
  sudo -l | grep vllm
  ```

## Usage

Once configured, you can use these commands:

```bash
# Start vLLM server (automatic prerequisite for comment generation)
make vllm-start

# Check vLLM server status
make vllm-status

# Stop vLLM server
make vllm-stop

# Generate comments (automatically starts vLLM first)
make comments-generate
```

## How It Works

1. **Make target dependencies**: `comments-generate` now depends on `vllm-start`, so the server starts automatically
2. **Helper script**: `bin/vllm-start-helper.sh` handles the startup with proper error checking
3. **Passwordless sudo**: The sudoers configuration allows vLLM systemd operations without password prompts

## vLLM Models Available

The `vllm-switch` command can switch between three models:

- **implementer** - Ministral-3-8B-Instruct (fast implementation, default)
- **architect** - Ministral-3-8B-Reasoning (planning/review)
- **scaffolder** - Qwen2.5-7B-Instruct (structured output)

You can manually switch models with:
```bash
vllm-switch architect  # Switch to planning model
vllm-switch scaffolder # Switch to scaffolding model
vllm-switch implementer # Switch back to implementation model
```

## Troubleshooting

### sudo still prompts for password
- Double-check your sudoers entry has `NOPASSWD`
- Verify you edited the right line (should be at the end of the file)
- Make sure there are no typos in the command paths

### vLLM service starts but doesn't respond
- Check service logs: `sudo journalctl -u vllm -n 20`
- Verify the model files exist: `ls /data/models/fp16/`
- Check if port 8000 is already in use: `lsof -i :8000`

### Model fails to load
- Check available GPU memory: `nvidia-smi`
- vLLM needs significant VRAM (8B model needs ~8GB)
- Check logs: `sudo journalctl -u vllm --follow`

## Automated Workflow

```bash
# Everything happens automatically now:
make comments-generate

# Internally does:
# 1. make vllm-start        (ensures server is running)
# 2. generate_blog_comments.py --all
```

## Manual vLLM Management

If you need to manage vLLM manually:

```bash
# Start with a specific model
vllm-switch implementer

# Check status
vllm-switch status

# Stop the service
vllm-switch stop
```
