import json
import os
from collections import OrderedDict

# Path to your JSON file
json_file = os.path.join('..', 'bugs_meta_data.json')


def extract_function_signature(function_code):
    for line in function_code.splitlines():
        line = line.strip()
        if line.startswith('def '):
            return line
    return ""

# Load the JSON data
with open(json_file, 'r') as f:
    data = json.load(f)

# Rebuild each "function" dictionary with "function_signature" after "function_name"
for bug in data.values():
    function_data = bug.get('function', {})
    function_before = function_data.get('function_before', '')
    if function_before:
        signature = extract_function_signature(function_before)
        new_function_data = OrderedDict()
        for key, value in function_data.items():
            new_function_data[key] = value
            if key == 'function_name':
                new_function_data['function_signature'] = signature
        bug['function'] = new_function_data

# Save updated data back to the same file
with open(json_file, 'w') as f:
    json.dump(data, f, indent=2)
