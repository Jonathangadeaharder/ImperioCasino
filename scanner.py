import os

# Define the list of code file extensions you want to include
code_extensions = [
    '.py','ts',
    '.css', '.tsx'
]

# Define directories to exclude from the search
exclude_dirs = {'node_modules', '.git', '__pycache__', 'build', 'dist', 'venv', '.idea', 'migrations'}

# Define file patterns to exclude
exclude_files = { 'scanner.py' }

# Specify the output file name
output_file = 'concatenated_code.txt'

# Open the output file in write mode with UTF-8 encoding
with open(output_file, 'w', encoding='utf-8') as outfile:
    # Walk through the directory tree
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            # Skip excluded files
            if file in exclude_files:
                continue

            # Get the file extension
            _, ext = os.path.splitext(file)
            # Check if the file is a code file
            if ext.lower() in code_extensions:
                # Get the relative file path
                rel_dir = os.path.relpath(root, '.')
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
