#!/usr/bin/env python3
"""Fix bare except blocks in Python files."""

import re
import sys
from pathlib import Path

def fix_bare_excepts(file_path):
    """Replace bare except: blocks with except Exception:"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Pattern to match bare except: followed by newline
    # This captures the indentation level
    pattern = r'(\n\s+)except:\s*\n'
    replacement = r'\1except Exception:\n'
    
    content = re.sub(pattern, replacement, content)
    
    # Count replacements
    changes = len(re.findall(pattern, original)) - len(re.findall(pattern, content))
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return 0

def main():
    files_to_fix = [
        Path("c:/Users/legen/OneDrive/REVERIUS OPIUM/core/reverius_opium.py"),
        Path("c:/Users/legen/OneDrive/REVERIUS OPIUM/modules/ai_backend.py"),
        Path("c:/Users/legen/OneDrive/REVERIUS OPIUM/modules/command_processing.py"),
        Path("c:/Users/legen/OneDrive/REVERIUS OPIUM/modules/system_modules.py"),
        Path("c:/Users/legen/OneDrive/REVERIUS OPIUM/modules/utilities.py"),
        Path("c:/Users/legen/OneDrive/REVERIUS OPIUM/modules/voice.py"),
    ]
    
    total_fixes = 0
    for file_path in files_to_fix:
        if file_path.exists():
            fixes = fix_bare_excepts(file_path)
            if fixes > 0:
                print(f"✓ {file_path.name}: Fixed {fixes} bare except blocks")
                total_fixes += fixes
        else:
            print(f"✗ {file_path.name}: File not found")
    
    print(f"\nTotal bare except blocks fixed: {total_fixes}")
    return 0 if total_fixes > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
