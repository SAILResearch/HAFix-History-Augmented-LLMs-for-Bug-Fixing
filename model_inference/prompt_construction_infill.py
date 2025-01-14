from util import HistoryCategory

START = "<s>"
B_INST, E_INST = "[INST]", "[/INST]"  # for instruction models
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
MAX_NUM_FUNCTION_NAME = 300


def construct_prompt_infill(bug_info, history_category_flag, bug_history_info, bugs_description):
    SYSTEM_PROMPT, USER_INPUT, BUGGY_MASKED = generate_system_prompt_user_input_and_buggy_masked(
        True,
        bug_info,
        history_category_flag,
        bug_history_info,
        bugs_description
    )
    prompt = f"{START}{B_INST} {B_SYS}{SYSTEM_PROMPT}{E_SYS}{USER_INPUT}\n{E_INST}\n{BUGGY_MASKED}"
    return prompt, BUGGY_MASKED


def generate_system_prompt_user_input_and_buggy_masked(is_instruct_model: bool, bug_info, history_category_flag,
                                                       bug_history_info,
                                                       bugs_description):
    SYSTEM_PROMPT = ""
    USER_INPUT = ""
    BUGGY_MASKED = ""

    project_name = bug_info['project_name']
    buggy_file_name = bug_info['file']['file_name']
    buggy_function_name = bug_info['function']['function_name']
    date_time = bug_info['commit']['commit_date']
    bug_desc = bugs_description['description']
    buggy_line_content = bug_info['buggy_line_content'].strip()
    buggy_code = bug_info['function']['function_before']

    project_name_inst = f"# The project name: {project_name}\n"
    buggy_file_name_inst = f"# The buggy file name: {buggy_file_name}\n"
    buggy_function_name_inst = f"# The buggy function name: {buggy_function_name}\n"
    date_time_inst = f"# The date time: {date_time}\n"
    bug_desc_inst = f"# The bug description: {bug_desc}\n\n"
    buggy_line_content_inst = f"# The buggy line content: {buggy_line_content}\n\n"
    buggy_code_inst = f"# The buggy code snippet:\n{buggy_code}\n\n"
    # fixed_inst = f"# The fixed code snippet: "

    try:
        BUGGY_MASKED = mask_code_manually(buggy_code, buggy_line_content, str(bug_info['id']))
        # BUGGY_MASKED = mask_code(buggy_code, buggy_line_content)
    except:
        print(f"bug_id: {str(bug_info['id'])} meet error when mask the buggy line")

    assert BUGGY_MASKED != ""

    if history_category_flag == HistoryCategory.pure_infill.value:
        return "", "", BUGGY_MASKED

    # 2 and 21
    co_evolved_functions_name_modified_file_ = list(
        bug_history_info['blame_commit']['function']['functions_name_co_evolved_modified_file'])
    if len(co_evolved_functions_name_modified_file_) > MAX_NUM_FUNCTION_NAME:
        co_evolved_functions_name_modified_file_ = co_evolved_functions_name_modified_file_[:MAX_NUM_FUNCTION_NAME]
    co_evolved_functions_name_modified_file = ', '.join(co_evolved_functions_name_modified_file_)

    if 'recursive_blame_commits' in bug_history_info and 'commits' in bug_history_info['recursive_blame_commits']:
        co_evolved_functions_name_modified_file_recursive_ = list(
            next(iter(bug_history_info['recursive_blame_commits']['commits'].items()))[1]['function'][
                'functions_name_co_evolved_modified_file'])
        if len(co_evolved_functions_name_modified_file_recursive_) > MAX_NUM_FUNCTION_NAME:
            co_evolved_functions_name_modified_file_recursive_ = co_evolved_functions_name_modified_file_recursive_[
                                                                 :MAX_NUM_FUNCTION_NAME]
        co_evolved_functions_name_modified_file_recursive = ', '.join(
            co_evolved_functions_name_modified_file_recursive_)
    else:
        co_evolved_functions_name_modified_file_recursive = ''

    # 3 and 31
    co_evolved_functions_name_all_files_ = list(
        bug_history_info['blame_commit']['function']['functions_name_co_evolved_all_files'])
    if len(co_evolved_functions_name_all_files_) > MAX_NUM_FUNCTION_NAME:
        co_evolved_functions_name_all_files_ = co_evolved_functions_name_all_files_[:MAX_NUM_FUNCTION_NAME]
    co_evolved_functions_name_all_files = ', '.join(co_evolved_functions_name_all_files_)

    if 'recursive_blame_commits' in bug_history_info and 'commits' in bug_history_info['recursive_blame_commits']:
        co_evolved_functions_name_all_files_recursive_ = list(
            next(iter(bug_history_info['recursive_blame_commits']['commits'].items()))[1]['function'][
                'functions_name_co_evolved_all_files'])
        if len(co_evolved_functions_name_all_files_recursive_) > MAX_NUM_FUNCTION_NAME:
            co_evolved_functions_name_all_files_recursive_ = co_evolved_functions_name_all_files_recursive_[
                                                             :MAX_NUM_FUNCTION_NAME]
        co_evolved_functions_name_all_files_recursive = ', '.join(co_evolved_functions_name_all_files_recursive_)
    else:
        co_evolved_functions_name_all_files_recursive = ''

    # 4 and 41
    functions_name_modified_file_ = list(bug_history_info['blame_commit']['function']['functions_name_modified_file'])
    if len(functions_name_modified_file_) > MAX_NUM_FUNCTION_NAME:
        functions_name_modified_file_ = functions_name_modified_file_[:MAX_NUM_FUNCTION_NAME]
    functions_name_modified_file = ', '.join(functions_name_modified_file_)

    if 'recursive_blame_commits' in bug_history_info and 'commits' in bug_history_info['recursive_blame_commits']:
        functions_name_modified_file_recursive_ = list(
            next(iter(bug_history_info['recursive_blame_commits']['commits'].items()))[1]['function'][
                'functions_name_modified_file'])
        if len(functions_name_modified_file_recursive_) > MAX_NUM_FUNCTION_NAME:
            functions_name_modified_file_recursive_ = functions_name_modified_file_recursive_[:MAX_NUM_FUNCTION_NAME]
        functions_name_modified_file_recursive = ', '.join(functions_name_modified_file_recursive_)
    else:
        functions_name_modified_file_recursive = ''

    # 5 and 51
    functions_name_all_files_ = list(bug_history_info['blame_commit']['function']['functions_name_all_files'])
    if len(functions_name_all_files_) > MAX_NUM_FUNCTION_NAME:
        functions_name_all_files_ = functions_name_all_files_[:MAX_NUM_FUNCTION_NAME]
    functions_name_all_files = ', '.join(functions_name_all_files_)

    if 'recursive_blame_commits' in bug_history_info and 'commits' in bug_history_info['recursive_blame_commits']:
        functions_name_all_files_recursive_ = list(
            next(iter(bug_history_info['recursive_blame_commits']['commits'].items()))[1]['function'][
                'functions_name_all_files'])
        if len(functions_name_all_files_recursive_) > MAX_NUM_FUNCTION_NAME:
            functions_name_all_files_recursive_ = functions_name_all_files_recursive_[:MAX_NUM_FUNCTION_NAME]
        functions_name_all_files_recursive = ', '.join(functions_name_all_files_recursive_)
    else:
        functions_name_all_files_recursive = ''

    co_evolved_functions_name_modified_file_inst = (
        f"# Co-evolved functions' names of this source code file in the blame commit: {co_evolved_functions_name_modified_file}\n\n")
    co_evolved_functions_name_all_files_inst = (
        f"# Co-evolved functions' names of relevant code files in the blame commit: {co_evolved_functions_name_all_files}\n\n")

    functions_name_modified_file_inst = f"# All functions' names of this source code file in the blame commit: {functions_name_modified_file}\n\n"
    functions_name_all_files_inst = f"# All functions' names of relevant source code files in the blame commit: {functions_name_all_files}\n\n"

    # 6 and 61
    files_name_blame_ = list(bug_history_info['blame_commit']['file']['files_name_in_blame_commit'])
    if len(files_name_blame_) > MAX_NUM_FUNCTION_NAME:
        files_name_blame_ = files_name_blame_[:MAX_NUM_FUNCTION_NAME]
    files_name_blame = ', '.join(files_name_blame_)

    if 'recursive_blame_commits' in bug_history_info and 'commits' in bug_history_info['recursive_blame_commits']:
        files_name_blame_recursive_ = list(
            next(iter(bug_history_info['recursive_blame_commits']['commits'].items()))[1]['file'][
                'files_name_in_blame_commit'])
        if len(files_name_blame_recursive_) > MAX_NUM_FUNCTION_NAME:
            files_name_blame_recursive_ = files_name_blame_recursive_[:MAX_NUM_FUNCTION_NAME]
        files_name_blame_recursive = ', '.join(files_name_blame_recursive_)
    else:
        files_name_blame_recursive = ''

    files_name_blame_inst = f"# The co-evolved files’ names of relevant source code files in the blame commit: {files_name_blame}\n\n"

    wrap_instruct = "Please wrap your fixed code snippet between ```python and ```" if is_instruct_model else ""
    # 1. baseline
    USER_INPUT_BASELINE = f"{project_name_inst}{buggy_file_name_inst}{buggy_function_name_inst}{date_time_inst}{buggy_code_inst}{bug_desc_inst}{buggy_line_content_inst}"
    SYSTEM_PROMPT_BASELINE = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."

    if history_category_flag == HistoryCategory.baseline.value:
        SYSTEM_PROMPT = SYSTEM_PROMPT_BASELINE
        USER_INPUT = USER_INPUT_BASELINE

    # 2. baseline_co_evolved_functions_name_modified_file_blame
    elif history_category_flag == HistoryCategory.baseline_co_evolved_functions_name_modified_file_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the co-evolved functions' names of this source code file in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = f"{co_evolved_functions_name_modified_file_inst}{USER_INPUT_BASELINE}"

    # 21. co_evolved_functions_name_modified_file_blame_recursive
    elif history_category_flag == HistoryCategory.co_evolved_functions_name_modified_file_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of co-evolved functions' names of this source code file mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = (
            f"# The first group is co-evolved functions' names of this source code file before the blame commit: {co_evolved_functions_name_modified_file_recursive}\n\n"
            f"# The second group is co-evolved functions' names of this source code file in the blame commit: {co_evolved_functions_name_modified_file}\n\n"
            f"{USER_INPUT_BASELINE}")


    # 3. baseline_co_evolved_functions_name_all_files_blame
    elif history_category_flag == HistoryCategory.baseline_co_evolved_functions_name_all_files_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the co-evolved functions' names of relevant code files in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = f"{co_evolved_functions_name_all_files_inst}{USER_INPUT_BASELINE}"

    # 31. co_evolved_functions_name_modified_file_blame_recursive
    elif history_category_flag == HistoryCategory.co_evolved_functions_name_all_files_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of co-evolved functions' names of relevant code files mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = (
            f"# The first group is co-evolved functions' names of relevant code files before the blame commit: {co_evolved_functions_name_all_files_recursive}\n\n"
            f"# The second group is co-evolved functions' names of relevant code files in the blame commit: {co_evolved_functions_name_all_files}\n\n"
            f"{USER_INPUT_BASELINE}")


    # 4. baseline_all_functions_name_modified_file_blame
    elif history_category_flag == HistoryCategory.baseline_all_functions_name_modified_file_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all functions' names of this source code file in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = f"{functions_name_modified_file_inst}{USER_INPUT_BASELINE}"

    # 41. all_functions_name_modified_file_blame_recursive
    elif history_category_flag == HistoryCategory.all_functions_name_modified_file_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of all functions' names of this source code file mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = (
            f"# The first group is all functions' names of this source code file before the blame commit: {functions_name_modified_file_recursive}\n\n"
            f"# The second group is all functions' names of this source code file in the blame commit: {functions_name_modified_file}\n\n"
            f"{USER_INPUT_BASELINE}")



    # 5. baseline_all_functions_name_all_files_blame
    elif history_category_flag == HistoryCategory.baseline_all_functions_name_all_files_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all functions' names of relevant source code files in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = f"{functions_name_all_files_inst}{USER_INPUT_BASELINE}"

    # 51. all_functions_name_all_files_blame_recursive
    elif history_category_flag == HistoryCategory.all_functions_name_all_files_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of all functions' names of relevant source code files mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = (
            f"# The first group is all functions' names of relevant source code files before the blame commit: {functions_name_all_files_recursive}\n\n"
            f"# The second group is all functions' names of relevant source code files in the blame commit: {functions_name_all_files}\n\n"
            f"{USER_INPUT_BASELINE}")



    # 6. baseline_all_co_evolved_files_name_blame
    elif history_category_flag == HistoryCategory.baseline_all_co_evolved_files_name_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all co-evolved files’ names in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = f"{files_name_blame_inst}{USER_INPUT_BASELINE}"

    # 61. all_co_evolved_files_name_blame_recursive
    elif history_category_flag == HistoryCategory.all_co_evolved_files_name_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of co-evolved files’ names of relevant source code files mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        USER_INPUT = (
            f"# The first group is the co-evolved files’ names of relevant source code files before the blame commit: {files_name_blame_recursive}\n\n"
            f"# The second group is the co-evolved files’ names of relevant source code files in the blame commit: {files_name_blame}\n\n"
            f"{USER_INPUT_BASELINE}")



    # 7. baseline_function_code_pair_blame
    elif history_category_flag == HistoryCategory.baseline_function_code_pair_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with a pair of a historical version of this code snippet, including the first version of this code snippet, the historical commit date time, the historical commit message, and the second version of this code snippet, note the historical commit message here might indicate how this code was changed between these two versions. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        FUNCTION_HISTORY_INPUT = get_function_history_input(bug_history_info)
        USER_INPUT = f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    # 71. function_code_pair_blame_recursive
    elif history_category_flag == HistoryCategory.function_code_pair_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of code pairs mined from historical commits in the code base. Each group is a pair of a historical version of this code snippet, including the first version of this code snippet, the historical commit date time, the historical commit message, and the second version of this code snippet, note the historical commit message here might indicate how this code was changed between these two versions. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        FUNCTION_HISTORY_INPUT = get_function_history_input_recursive(bug_history_info)
        USER_INPUT = f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}"



    # 8. baseline_file_code_patch_blame
    elif history_category_flag == HistoryCategory.baseline_file_code_patch_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the historical patch code which consists of changes mined from the code base. It specifies the removed and added lines. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        File_HISTORY_INPUT = get_file_history_input(bug_history_info)
        USER_INPUT = f"{File_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    # 81. file_code_patch_blame_recursive
    elif history_category_flag == HistoryCategory.file_code_patch_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of the historical patch code which consists of changes mined from historical commits in the code base. It specifies the removed and added lines. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. There is just one line being needed to be infilled. Please only generate one line of code, don't explain any other things."
        FUNCTION_HISTORY_INPUT = get_file_history_input_recursive(bug_history_info)
        USER_INPUT = f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    return SYSTEM_PROMPT, USER_INPUT, BUGGY_MASKED


def get_function_history_input(bug_history_info):
    history_function_before = bug_history_info['blame_commit']['function']['function_code_before']
    history_commit_date = bug_history_info['blame_commit']['commit']['commit_date']
    history_commit_msg = bug_history_info['blame_commit']['commit']['commit_message']
    history_function_after = bug_history_info['blame_commit']['function']['function_code_after']

    history_before_inst_code = f"# The first version:\n{history_function_before}\n\n"
    history_commit_date_inst = f"# The historical commit date time: {history_commit_date}\n"
    history_commit_inst_msg = f"# The historical commit message: {history_commit_msg}\n\n"
    history_after_inst_code = f"# The second version:\n{history_function_after}\n\n"
    return f"{history_before_inst_code}{history_commit_date_inst}{history_commit_inst_msg}{history_after_inst_code}"


def get_function_history_input_recursive(bug_history_info):
    blame_commit_user_input_function = get_function_history_input(bug_history_info)

    if 'recursive_blame_commits' in bug_history_info and 'commits' in bug_history_info['recursive_blame_commits']:
        latest_recursive_commit = next(iter(bug_history_info['recursive_blame_commits']['commits'].items()))[1]

        history_function_before = latest_recursive_commit['function']['function_code_before']
        history_commit_date = latest_recursive_commit['commit']['commit_date']
        history_commit_msg = latest_recursive_commit['commit']['commit_message']
        history_function_after = latest_recursive_commit['function']['function_code_after']

        history_before_inst_code = f"# The first version:\n{history_function_before}\n\n"
        history_commit_date_inst = f"# The historical commit date time: {history_commit_date}\n"
        history_commit_inst_msg = f"# The historical commit message: {history_commit_msg}\n\n"
        history_after_inst_code = f"# The second version:\n{history_function_after}\n\n"
        return (f"The first group of code pairs is:\n"
                f"{history_before_inst_code}{history_commit_date_inst}{history_commit_inst_msg}{history_after_inst_code}"
                f"The second group of code pairs is:\n{blame_commit_user_input_function}")
    else:
        return blame_commit_user_input_function


def get_file_history_input(bug_history_info):
    # history_file_before = bug_history_info['blame_commit']['file']['file_before']
    # history_file_after = bug_history_info['blame_commit']['file']['file_after']
    # history_before_inst_code = f"# The first version of the source code file:\n{history_file_before}\n\n"
    # history_after_inst_code = f"# The second version of the source code file:\n{history_file_after}\n\n"
    history_commit_date = bug_history_info['blame_commit']['commit']['commit_date']
    history_commit_msg = bug_history_info['blame_commit']['commit']['commit_message']
    history_file_patch = bug_history_info['blame_commit']['file']['file_patch']
    history_commit_date_inst = f"# The historical commit date time: {history_commit_date}\n"
    history_commit_inst_msg = f"# The historical commit message: {history_commit_msg}\n\n"
    history_file_patch_inst = f"# The historical patch code:\n{history_file_patch}\n\n"
    return f"{history_commit_date_inst}{history_commit_inst_msg}{history_file_patch_inst}"


def get_file_history_input_recursive(bug_history_info):
    blame_commit_user_input_file = get_file_history_input(bug_history_info)

    if 'recursive_blame_commits' in bug_history_info and 'commits' in bug_history_info['recursive_blame_commits']:
        latest_recursive_commit = next(iter(bug_history_info['recursive_blame_commits']['commits'].items()))[1]

        history_commit_date = latest_recursive_commit['commit']['commit_date']
        history_commit_msg = latest_recursive_commit['commit']['commit_message']
        history_file_patch = latest_recursive_commit['file']['file_patch']
        history_commit_date_inst = f"# The historical commit date time: {history_commit_date}\n"
        history_commit_inst_msg = f"# The historical commit message: {history_commit_msg}\n\n"
        history_file_patch_inst = f"# The historical patch code:\n{history_file_patch}\n\n"

        return (f"The first historical patch code is:\n"
                f"{history_commit_date_inst}{history_commit_inst_msg}{history_file_patch_inst}"
                f"The second historical patch code is:\n{blame_commit_user_input_file}")
    else:
        return blame_commit_user_input_file


def mask_code(buggy_code: str, buggy_line_content: str):
    buggy_line_content_strip = buggy_line_content.strip(" ")
    masked_code = buggy_code.split(buggy_line_content_strip)[0].strip(" ") + "<FILL_ME>" + \
                  buggy_code.split(buggy_line_content_strip)[1]
    return masked_code


def mask_code_manually(buggy_code: str, buggy_line_content: str, bug_id: str):
    # <FILL_ME>
    # cases: There are format issue in the buggy line content
    if bug_id == '14':
        masked_code = "def read_conllx(input_data, use_morphology=False, n=0):\n    i = 0\n    for sent in input_data.strip().split('\\n\\n'):\n        lines = sent.strip().split('\\n')\n        if lines:\n            while lines[0].startswith('#'):\n                lines.pop(0)\n            tokens = []\n            for line in lines:\n                parts = line.split('\\t')\n                id_, word, lemma, pos, tag, morph, head, dep, _1, iob = parts\n                if '-' in id_ or '.' in id_:\n                    continue\n                try:\n                    id_ = int(id_) - 1\n<FILL_ME>\n                    dep = 'ROOT' if dep == 'root' else dep\n                    tag = pos if tag == '_' else tag\n                    tag = tag + '__' + morph if use_morphology else tag\n                    iob = iob if iob else 'O'\n                    tokens.append((id_, word, tag, head, dep, iob))\n                except:\n                    print(line)\n                    raise\n            tuples = [list(t) for t in zip(*tokens)]\n            yield (None, [[tuples, []]])\n            i += 1\n            if n >= 1 and i >= n:\n                break"
    elif bug_id == '16':
        masked_code = "def unescapeHTML(s):\n    if s is None:\n        return None\n    assert type(s) == compat_str\n    return re.sub(\n<FILL_ME>"
    elif bug_id == '18':
        masked_code = "def urljoin(base, path):\n    if isinstance(path, bytes):\n        path = path.decode('utf-8')\n    if not isinstance(path, compat_str) or not path:\n        return None\n<FILL_ME>\n        return path\n    if isinstance(base, bytes):\n        base = base.decode('utf-8')\n    if not isinstance(base, compat_str) or not re.match('^(?:https?:)?//', base):\n        return None\n    return compat_urlparse.urljoin(base, path)"
    elif bug_id == '21':
        masked_code = "def js_to_json(code):\n\n    def fix_kv(m):\n        v = m.group(0)\n        if v in ('true', 'false', 'null'):\n            return v\n        elif v.startswith('/*') or v == ',':\n            return ''\n        if v[0] in (\"'\", '\"'):\n            v = re.sub('(?s)\\\\\\\\.|\"', lambda m: {'\"': '\\\\\"', \"\\\\'\": \"'\", '\\\\\\n': '', '\\\\x': '\\\\u00'}.get(m.group(0), m.group(0)), v[1:-1])\n        INTEGER_TABLE = (('^0[xX][0-9a-fA-F]+', 16), ('^0+[0-7]+', 8))\n        for regex, base in INTEGER_TABLE:\n            im = re.match(regex, v)\n            if im:\n                i = int(im.group(0), base)\n                return '\"%d\":' % i if v.endswith(':') else '%d' % i\n        return '\"%s\"' % v\n    return re.sub('(?sx)\\n        \"(?:[^\"\\\\\\\\]*(?:\\\\\\\\\\\\\\\\|\\\\\\\\[\\'\"nurtbfx/\\\\n]))*[^\"\\\\\\\\]*\"|\\n        \\'(?:[^\\'\\\\\\\\]*(?:\\\\\\\\\\\\\\\\|\\\\\\\\[\\'\"nurtbfx/\\\\n]))*[^\\'\\\\\\\\]*\\'|\\n        /\\\\*.*?\\\\*/|,(?=\\\\s*[\\\\]}])|\\n        [a-zA-Z_][.a-zA-Z_0-9]*|\\n<FILL_ME>\n        [0-9]+(?=\\\\s*:)\\n        ', fix_kv, code)"
    elif bug_id == '22':
        masked_code = "def url_basename(url):\n<FILL_ME>\n    if not m:\n        return u''\n    return m.group(1)"
    elif bug_id == '23':
        masked_code = "def check_required_arguments(argument_spec, module_parameters):\n    \"\"\"Check all paramaters in argument_spec and return a list of parameters\n    that are required but not present in module_parameters\n\n    Raises TypeError if the check fails\n\n    :arg argument_spec: Argument spec dicitionary containing all parameters\n        and their specification\n    :arg module_paramaters: Dictionary of module parameters\n\n    :returns: Empty list or raises TypeError if the check fails.\n    \"\"\"\n    missing = []\n    if argument_spec is None:\n        return missing\n    for k, v in argument_spec.items():\n        required = v.get('required', False)\n        if required and k not in module_parameters:\n            missing.append(k)\n    if missing:\n<FILL_ME>\n        raise TypeError(to_native(msg))\n    return missing"
    elif bug_id == '24':
        masked_code = "def map_obj_to_commands(updates, module, warnings):\n    commands = list()\n    want, have = updates\n\n    def needs_update(x):\n        return want.get(x) is not None and want.get(x) != have.get(x)\n\n    def add(cmd):\n        if 'management api http-commands' not in commands:\n            commands.insert(0, 'management api http-commands')\n        commands.append(cmd)\n    if any((needs_update('http'), needs_update('http_port'))):\n        if want['http'] is False:\n            add('no protocol http')\n        elif have['http'] is False and want['http'] in (False, None):\n            warnings.append('protocol http is not enabled, not configuring http port value')\n        else:\n            port = want['http_port'] or 80\n            add('protocol http port %s' % port)\n    if any((needs_update('https'), needs_update('https_port'))):\n        if want['https'] is False:\n            add('no protocol https')\n        elif have['https'] is False and want['https'] in (False, None):\n            warnings.append('protocol https is not enabled, not configuring https port value')\n        else:\n            port = want['https_port'] or 443\n            add('protocol https port %s' % port)\n    if any((needs_update('local_http'), needs_update('local_http_port'))):\n        if want['local_http'] is False:\n            add('no protocol http localhost')\n        elif have['local_http'] is False and want['local_http'] in (False, None):\n            warnings.append('protocol local_http is not enabled, not configuring local_http port value')\n        else:\n            port = want['local_http_port'] or 8080\n            add('protocol http localhost port %s' % port)\n    if any((needs_update('socket'), needs_update('socket'))):\n        if want['socket'] is False:\n            add('no protocol unix-socket')\n        else:\n            add('protocol unix-socket')\n    if needs_update('state') and (not needs_update('vrf')):\n        if want['state'] == 'stopped':\n            add('shutdown')\n        elif want['state'] == 'started':\n            add('no shutdown')\n    if needs_update('vrf'):\n        add('vrf %s' % want['vrf'])\n        if want['state'] == 'stopped':\n            add('shutdown')\n        elif want['state'] == 'started':\n            add('no shutdown')\n    return commands"
    elif bug_id == '46':
        masked_code = "def array_equivalent(left, right, strict_nan=False):\n    \"\"\"\n    True if two arrays, left and right, have equal non-NaN elements, and NaNs\n    in corresponding locations.  False otherwise. It is assumed that left and\n    right are NumPy arrays of the same dtype. The behavior of this function\n    (particularly with respect to NaNs) is not defined if the dtypes are\n    different.\n\n    Parameters\n    ----------\n    left, right : ndarrays\n    strict_nan : bool, default False\n        If True, consider NaN and None to be different.\n\n    Returns\n    -------\n    b : bool\n        Returns True if the arrays are equivalent.\n\n    Examples\n    --------\n    >>> array_equivalent(\n    ...     np.array([1, 2, np.nan]),\n    ...     np.array([1, 2, np.nan]))\n    True\n    >>> array_equivalent(\n    ...     np.array([1, np.nan, 2]),\n    ...     np.array([1, 2, np.nan]))\n    False\n    \"\"\"\n    left, right = (np.asarray(left), np.asarray(right))\n    if left.shape != right.shape:\n        return False\n    if is_string_dtype(left) or is_string_dtype(right):\n        if not strict_nan:\n            return lib.array_equivalent_object(ensure_object(left.ravel()), ensure_object(right.ravel()))\n        for left_value, right_value in zip(left, right):\n            if left_value is NaT and right_value is not NaT:\n                return False\n            elif isinstance(left_value, float) and np.isnan(left_value):\n                if not isinstance(right_value, float) or not np.isnan(right_value):\n                    return False\n<FILL_ME>\n                return False\n        return True\n    if is_float_dtype(left) or is_complex_dtype(left):\n        if not (np.prod(left.shape) and np.prod(right.shape)):\n            return True\n        return ((left == right) | isna(left) & isna(right)).all()\n    elif is_datetimelike_v_numeric(left, right):\n        return False\n    elif needs_i8_conversion(left) and needs_i8_conversion(right):\n        if not is_dtype_equal(left.dtype, right.dtype):\n            return False\n        left = left.view('i8')\n        right = right.view('i8')\n    if left.dtype.type is np.void or right.dtype.type is np.void:\n        if left.dtype != right.dtype:\n            return False\n    return np.array_equal(left, right)"
    elif bug_id == '59':
        masked_code = "def update(self, current, values=None, force=False):\n    \"\"\"Updates the progress bar.\n\n        # Arguments\n            current: Index of current step.\n            values: List of tuples (name, value_for_last_step).\n                The progress bar will display averages for these values.\n            force: Whether to force visual progress update.\n        \"\"\"\n    values = values or []\n    for k, v in values:\n        if k not in self.sum_values:\n            self.sum_values[k] = [v * (current - self.seen_so_far), current - self.seen_so_far]\n            self.unique_values.append(k)\n        else:\n            self.sum_values[k][0] += v * (current - self.seen_so_far)\n            self.sum_values[k][1] += current - self.seen_so_far\n    self.seen_so_far = current\n    now = time.time()\n    info = ' - %.0fs' % (now - self.start)\n    if self.verbose == 1:\n<FILL_ME>\n            return\n        prev_total_width = self.total_width\n        if self._dynamic_display:\n            sys.stdout.write('\\x08' * prev_total_width)\n            sys.stdout.write('\\r')\n        else:\n            sys.stdout.write('\\n')\n        if self.target is not None:\n            numdigits = int(np.floor(np.log10(self.target))) + 1\n            barstr = '%%%dd/%d [' % (numdigits, self.target)\n            bar = barstr % current\n            prog = float(current) / self.target\n            prog_width = int(self.width * prog)\n            if prog_width > 0:\n                bar += '=' * (prog_width - 1)\n                if current < self.target:\n                    bar += '>'\n                else:\n                    bar += '='\n            bar += '.' * (self.width - prog_width)\n            bar += ']'\n        else:\n            bar = '%7d/Unknown' % current\n        self.total_width = len(bar)\n        sys.stdout.write(bar)\n        if current:\n            time_per_unit = (now - self.start) / current\n        else:\n            time_per_unit = 0\n        if self.target is not None and current < self.target:\n            eta = time_per_unit * (self.target - current)\n            if eta > 3600:\n                eta_format = '%d:%02d:%02d' % (eta // 3600, eta % 3600 // 60, eta % 60)\n            elif eta > 60:\n                eta_format = '%d:%02d' % (eta // 60, eta % 60)\n            else:\n                eta_format = '%ds' % eta\n            info = ' - ETA: %s' % eta_format\n        elif time_per_unit >= 1:\n            info += ' %.0fs/step' % time_per_unit\n        elif time_per_unit >= 0.001:\n            info += ' %.0fms/step' % (time_per_unit * 1000.0)\n        else:\n            info += ' %.0fus/step' % (time_per_unit * 1000000.0)\n        for k in self.unique_values:\n            info += ' - %s:' % k\n            if isinstance(self.sum_values[k], list):\n                avg = np.mean(self.sum_values[k][0] / max(1, self.sum_values[k][1]))\n                if abs(avg) > 0.001:\n                    info += ' %.4f' % avg\n                else:\n                    info += ' %.4e' % avg\n            else:\n                info += ' %s' % self.sum_values[k]\n        self.total_width += len(info)\n        if prev_total_width > self.total_width:\n            info += ' ' * (prev_total_width - self.total_width)\n        if self.target is not None and current >= self.target:\n            info += '\\n'\n        sys.stdout.write(info)\n        sys.stdout.flush()\n    elif self.verbose == 2:\n        if self.target is None or current >= self.target:\n            for k in self.unique_values:\n                info += ' - %s:' % k\n                avg = np.mean(self.sum_values[k][0] / max(1, self.sum_values[k][1]))\n                if avg > 0.001:\n                    info += ' %.4f' % avg\n                else:\n                    info += ' %.4e' % avg\n            info += '\\n'\n            sys.stdout.write(info)\n            sys.stdout.flush()\n    self.last_update = now"
    elif bug_id == '63':
        masked_code = "def _make_getset_interval(method_name, lim_name, attr_name):\n    \"\"\"\n    Helper to generate ``get_{data,view}_interval`` and\n    ``set_{data,view}_interval`` implementations.\n    \"\"\"\n\n    def getter(self):\n        return getattr(getattr(self.axes, lim_name), attr_name)\n\n    def setter(self, vmin, vmax, ignore=False):\n        if ignore:\n            setattr(getattr(self.axes, lim_name), attr_name, (vmin, vmax))\n        else:\n            oldmin, oldmax = getter(self)\n            if oldmin < oldmax:\n                setter(self, min(vmin, vmax, oldmin), max(vmin, vmax, oldmax), ignore=True)\n            else:\n<FILL_ME>\n        self.stale = True\n    getter.__name__ = f'get_{method_name}_interval'\n    setter.__name__ = f'set_{method_name}_interval'\n    return (getter, setter)"
    elif bug_id == '64':
        masked_code = "def _make_getset_interval(method_name, lim_name, attr_name):\n    \"\"\"\n    Helper to generate ``get_{data,view}_interval`` and\n    ``set_{data,view}_interval`` implementations.\n    \"\"\"\n\n    def getter(self):\n        return getattr(getattr(self.axes, lim_name), attr_name)\n\n    def setter(self, vmin, vmax, ignore=False):\n        if ignore:\n            setattr(getattr(self.axes, lim_name), attr_name, (vmin, vmax))\n        else:\n            oldmin, oldmax = getter(self)\n            if oldmin < oldmax:\n                setter(self, min(vmin, vmax, oldmin), max(vmin, vmax, oldmax), ignore=True)\n            else:\n<FILL_ME>\n        self.stale = True\n    getter.__name__ = f'get_{method_name}_interval'\n    setter.__name__ = f'set_{method_name}_interval'\n    return (getter, setter)"

    # cases: There are more than one buggy line code in the buggy function
    elif bug_id == '35':
        masked_code = "def _get_with(self, key):\n    if isinstance(key, slice):\n        return self._slice(key)\n    elif isinstance(key, ABCDataFrame):\n        raise TypeError('Indexing a Series with DataFrame is not supported, use the appropriate DataFrame column')\n    elif isinstance(key, tuple):\n        try:\n            return self._get_values_tuple(key)\n        except ValueError:\n            if len(key) == 1:\n                key = key[0]\n                if isinstance(key, slice):\n                    return self._get_values(key)\n            raise\n    if not isinstance(key, (list, np.ndarray, Series, Index)):\n        key = list(key)\n    if isinstance(key, Index):\n        key_type = key.inferred_type\n    else:\n        key_type = lib.infer_dtype(key, skipna=False)\n    if key_type == 'integer':\n        if self.index.is_integer() or self.index.is_floating():\n            return self.loc[key]\n        elif isinstance(self.index, IntervalIndex):\n            indexer = self.index.get_indexer_for(key)\n            return self.iloc[indexer]\n        else:\n<FILL_ME>\n    if isinstance(key, (list, tuple)):\n        if len(key) == 1 and isinstance(key[0], slice):\n            return self._get_values(key)\n        return self.loc[key]\n    return self.reindex(key)"
    elif bug_id == '36':
        masked_code = "def __init__(self, df, na_rep: str='', float_format: Optional[str]=None, cols: Optional[Sequence[Label]]=None, header: Union[Sequence[Label], bool]=True, index: bool=True, index_label: Optional[Union[Label, Sequence[Label]]]=None, merge_cells: bool=False, inf_rep: str='inf', style_converter: Optional[Callable]=None):\n    self.rowcounter = 0\n    self.na_rep = na_rep\n    if hasattr(df, 'render'):\n        self.styler = df\n        df = df.data\n        if style_converter is None:\n            style_converter = CSSToExcelConverter()\n        self.style_converter = style_converter\n    else:\n        self.styler = None\n    self.df = df\n    if cols is not None:\n        if not len(Index(cols) & df.columns):\n            raise KeyError('passes columns are not ALL present dataframe')\n        if len(Index(cols) & df.columns) != len(cols):\n            raise KeyError(\"Not all names specified in 'columns' are found\")\n<FILL_ME>\n    self.columns = self.df.columns\n    self.float_format = float_format\n    self.index = index\n    self.index_label = index_label\n    self.header = header\n    self.merge_cells = merge_cells\n    self.inf_rep = inf_rep"
    elif bug_id == '39':
        masked_code = "def _try_convert_data(self, name, data, use_dtypes=True, convert_dates=True):\n    \"\"\"\n        Try to parse a ndarray like into a column by inferring dtype.\n        \"\"\"\n    if use_dtypes:\n        if not self.dtype:\n            return (data, False)\n        elif self.dtype is True:\n            pass\n        else:\n            dtype = self.dtype.get(name) if isinstance(self.dtype, dict) else self.dtype\n            if dtype is not None:\n                try:\n                    dtype = np.dtype(dtype)\n                    return (data.astype(dtype), True)\n                except (TypeError, ValueError):\n                    return (data, False)\n    if convert_dates:\n        new_data, result = self._try_convert_to_date(data)\n        if result:\n            return (new_data, True)\n    result = False\n    if data.dtype == 'object':\n        try:\n            data = data.astype('float64')\n            result = True\n        except (TypeError, ValueError):\n            pass\n    if data.dtype.kind == 'f':\n        if data.dtype != 'float64':\n            try:\n                data = data.astype('float64')\n                result = True\n            except (TypeError, ValueError):\n                pass\n    if len(data) and (data.dtype == 'float' or data.dtype == 'object'):\n        try:\n            new_data = data.astype('int64')\n            if (new_data == data).all():\n                data = new_data\n                result = True\n<FILL_ME>\n            pass\n    if data.dtype == 'int':\n        try:\n            data = data.astype('int64')\n            result = True\n        except (TypeError, ValueError):\n            pass\n    return (data, result)"
    elif bug_id == '54':
        masked_code = "def initialize(self, make_current=None):\n    if make_current is None:\n        if IOLoop.current(instance=False) is None:\n            self.make_current()\n    elif make_current:\n<FILL_ME>\n            raise RuntimeError('current IOLoop already exists')\n        self.make_current()"
    elif bug_id == '67':
        masked_code = "def __len__(self):\n    return self.total if self.iterable is None else         (self.iterable.shape[0] if hasattr(self.iterable, \"shape\")\n         else len(self.iterable) if hasattr(self.iterable, \"__len__\")\n        #<BUGGY_LINE>\n        else self.total)\n<FILL_ME>"

    else:
        masked_code = mask_code(buggy_code, buggy_line_content)
    return masked_code




















