import os

def replace_in_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_content = content.replace('mistral_llm', 'mistral_llm') \
                         .replace('mistral_generate', 'mistral_generate') \
                         .replace('Mistral', 'Mistral') \
                         .replace('mistral', 'mistral') \
                         .replace('MISTRAL', 'MISTRAL')
                         
    if content != new_content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('.'):
    if '.git' in root or 'venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.md') or file.endswith('.txt'):
            replace_in_file(os.path.join(root, file))

# Rename the file itself
if os.path.exists('models/mistral_llm.py'):
    os.rename('models/mistral_llm.py', 'models/mistral_llm.py')
    print("Renamed models/mistral_llm.py to models/mistral_llm.py")
