import os
import json
import re


def collect_bug_cases(input_dir, output_json_path):
    label_cases = []
    mask_cases = []

    for filename in os.listdir(input_dir):
        match = re.match(r"(\d+)-(label|mask)\.java$", filename)
        if not match:
            continue  # skip files that don't match pattern
        bug_id = int(match.group(1))
        case_type = match.group(2)

        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
            code = f.read()

        if case_type == 'label':
            label_cases.append({
                "bug_id": f'{bug_id}',
                "buggy_code": code
            })
        elif case_type == 'mask':
            mask_cases.append({
                "bug_id": f'{bug_id}',
                "masked_code": code
            })

    assert len(label_cases) == len(mask_cases)
    # Sort by bug_id for consistency
    label_cases.sort(key=lambda x: int(x["bug_id"]))
    mask_cases.sort(key=lambda x: int(x["bug_id"]))

    # Final structure
    output_data = {
        "label_cases": label_cases,
        "mask_cases": mask_cases
    }

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)


# Example usage
if __name__ == '__main__':
    collect_bug_cases(input_dir='.', output_json_path='correct_format_bugs.json')
