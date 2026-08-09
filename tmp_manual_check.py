import os
os.chdir(r'c:\Users\legen\OneDrive\REVERIUS OPIUM')
import modules.command_processing as cp
captured = []
cp.terminal_print = lambda message, color=None: captured.append((message, color))
cp.process_command('help')
print('manual_seen', any('MANUAL' in message for message, _ in captured))
print('help_seen', any('help' in message.lower() for message, _ in captured))
print('status_seen', any('status' in message.lower() for message, _ in captured))
