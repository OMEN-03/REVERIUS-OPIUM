from pathlib import Path
import subprocess

root = Path(r'c:\Users\legen\OneDrive\REVERIUS OPIUM')
commands = [
    (['py', '-3', '-m', 'pre_commit', 'run', '--all-files', '--verbose'], 'precommit_debug.txt'),
    (['py', '-3', '-m', 'pytest', '-vv', '--maxfail=1'], 'pytest_debug.txt'),
]
for cmd, fname in commands:
    p = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    path = root / fname
    path.write_text(
        f'COMMAND: {cmd}\nRETURN_CODE: {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}',
        encoding='utf-8',
    )
    print(fname, p.returncode)
