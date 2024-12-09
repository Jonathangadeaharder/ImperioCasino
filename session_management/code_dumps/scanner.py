import os

# Define the list of code file extensions you want to include
code_extensions = [
    '.py', '.c', '.cpp', '.h', '.hpp', '.java', '.js', '.ts',
    '.html', '.css', '.sh', '.bat', '.ps1', '.rb', '.go',
    '.php', '.pl', '.cs', '.swift', '.kt', '.kts'
]

# Define the list of directories to skip
dirs_to_skip = ['code_dumps', 'logs','migrations']

# Define the list of files to skip
files_to_skip = ['zipme.ps1']

# Specify the output file name in the current directory
script_dir = os.path.dirname(__file__)
output_file = os.path.join(script_dir, 'concatenated_code.txt')

# Open the output file in write mode with UTF-8 encoding
with open(output_file, 'w', encoding='utf-8') as outfile:
    # Walk through the directory tree
    for root, dirs, files in os.walk('..'):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in dirs_to_skip]
        for file in files:
            # Skip files
            if file in files_to_skip:
                continue
            # Get the file extension
            _, ext = os.path.splitext(file)
            # Check if the file is a code file
            if ext.lower() in code_extensions:
                # Get the relative file path
                rel_dir = os.path.relpath(root, '..')
                rel_file = os.path.join(rel_dir, file)
                if rel_dir == '.':
                    rel_file = file
                # Write the title (relative filepath and filename)
                outfile.write(f'=== {rel_file} ===\n\n')
                # Construct the full file path
                filepath = os.path.join(root, file)
                # Open and read the code file
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
                    contents = infile.read()
                    # Write the contents to the output file
                    outfile.write(contents)
                    outfile.write('\n\n')
