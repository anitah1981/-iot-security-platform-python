# Git Worktree Setup Script

This directory contains scripts that automatically set up new Git worktrees for the IoT Security Platform.

## What It Does

When you create a new Git worktree, these scripts automatically:

1. ✅ Check Python installation
2. ✅ Create a virtual environment (`venv/`)
3. ✅ Install all dependencies from `requirements.txt`
4. ✅ Copy `.env.example` to `.env` (if `.env` doesn't exist)
5. ✅ Provide helpful next steps

## Files

- **`worktree-setup.ps1`** - PowerShell script for Windows
- **`worktree-setup.sh`** - Bash script for Linux/Mac
- **`.git/hooks/post-checkout`** - Git hook (runs automatically)

## Configuration

### Option 1: Configure in Cursor (Recommended)

1. When you see the message "Click here to configure a worktree setup script", click it
2. Cursor will open a configuration file
3. Set the script path to:
   - **Windows**: `scripts\worktree-setup.ps1`
   - **Linux/Mac**: `scripts/worktree-setup.sh`

Or manually edit `.cursor/worktree-setup.json`:

```json
{
  "worktreeSetupScript": {
    "windows": "scripts\\worktree-setup.ps1",
    "unix": "scripts/worktree-setup.sh"
  }
}
```

### Option 2: Git Hook (Automatic)

The Git hook (`.git/hooks/post-checkout`) will automatically run the setup script when:
- A new worktree is created
- You checkout a branch in an existing worktree

**Note:** Git hooks are not committed to the repository. You may need to copy the hook to each worktree or configure it globally.

### Option 3: Manual Execution

You can also run the script manually:

**Windows (PowerShell):**
```powershell
.\scripts\worktree-setup.ps1
```

**Linux/Mac:**
```bash
bash scripts/worktree-setup.sh
```

## How to Use Git Worktrees

### Create a New Worktree

```bash
# Create a worktree for a feature branch
git worktree add ../iot-security-feature feature-branch-name

# Or create in a specific directory
git worktree add c:\projects\iot-security-feature feature-branch-name
```

### List Worktrees

```bash
git worktree list
```

### Remove a Worktree

```bash
git worktree remove ../iot-security-feature
# Or delete the directory and run:
git worktree prune
```

## What Gets Set Up

Each worktree gets its own:

- ✅ Virtual environment (`venv/`)
- ✅ Installed dependencies
- ✅ `.env` file (copied from `.env.example`)

**Important:** Each worktree has its own `.env` file. Update it with your actual values!

## Troubleshooting

### Script Doesn't Run Automatically

1. **Check Cursor configuration**: Make sure the script path is configured in Cursor settings
2. **Check Git hook**: Ensure `.git/hooks/post-checkout` exists and is executable
3. **Run manually**: Execute the script manually as shown above

### Permission Errors (Windows)

If you get permission errors running PowerShell scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

Make sure Python 3.8+ is installed and in your PATH:

```bash
python --version
# or
python3 --version
```

### Virtual Environment Issues

If the virtual environment isn't activating:

**Windows:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

## Example Output

When you create a new worktree, you'll see:

```
🚀 Setting up new Git worktree...
================================

📁 Worktree location: C:\projects\iot-security-feature
📁 Project root: C:\IoT-security-app-python

🐍 Checking Python installation...
   ✓ Found: Python 3.11.5

📦 Creating virtual environment...
   ✓ Virtual environment created

🔌 Activating virtual environment...
   ✓ Virtual environment activated

📥 Installing Python dependencies...
   This may take a minute...
   ✓ Dependencies installed successfully

📝 Creating .env file from .env.example...
   ✓ .env file created
   ⚠ Remember to update .env with your actual values!

✅ Worktree setup complete!
================================

Next steps:
1. Review and update .env file with your configuration
2. Activate virtual environment: .\venv\Scripts\Activate.ps1
3. Run the app: python run.py
```

## Benefits

- ⚡ **Faster setup** - No manual dependency installation
- 🔒 **Isolated environments** - Each worktree has its own venv
- 📝 **Consistent configuration** - `.env` file created automatically
- 🎯 **Less errors** - Automated setup reduces mistakes

---

**Need help?** Check the main `README.md` or open an issue on GitHub.
