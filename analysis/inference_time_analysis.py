import re


def get_nucleus_sampling_start_time(file_path):
    with open(file_path, 'r') as file:
        text = file.read()

    # Regular expression to find finish_at timestamps and bug_ids
    pattern = re.compile \
        (r'Current time (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): Finish generation.*?finish the bug: (\d+)', re.DOTALL)

    # Find all matches in the text
    matches = pattern.findall(text)

    # Print out the results
    for match in matches:
        start_at, bug_id = match
        print(f"bug_id={bug_id} start_at={start_at}")


def get_nucleus_sampling_end_time(file_path):
    with open(file_path, 'r') as file:
        text = file.read()

    # Regular expression to find finish_at timestamps and bug_ids
    pattern = re.compile \
        (r'Current time (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): Finish generation.*?finish the bug: (\d+)', re.DOTALL)

    pattern = re.compile \
        (r'finish the bug: (\d+).*?Current time (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): Start generation', re.DOTALL)

    # Find all matches in the text
    matches = pattern.findall(text)

    # Print out the results
    for match in matches:
        bug_id, finish_at = match
        print(f"bug_id={bug_id} finish_at={finish_at}")


def main():
    for i in range(8):
        file_path = f"/home/22ys22/project/fm-apr-replay/model_inference/log/old_prompt/codellama_7b_instruct_{i+1}.log"
        print(f"==========================log {i + 1}==========================")
        get_nucleus_sampling_start_time(file_path)
        print(f"=============================================================")
        get_nucleus_sampling_end_time(file_path)


if __name__ == '__main__':
    main()
