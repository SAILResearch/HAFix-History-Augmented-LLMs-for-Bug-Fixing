from util import HistoryCategory

START = "<s>"
B_INST, E_INST = "[INST]", "[/INST]"  # for instruction models
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
MAX_NUM_FUNCTION_NAME = 300


def construct_prompt_codellama_34b_instruct(bug_info, history_category_flag, bug_history_info, bugs_description,
                                            is_buggy_line_labeled):
    SYSTEM_PROMPT, USER_INPUT = generate_system_prompt_and_user_input(
        True,
        bug_info,
        history_category_flag,
        bug_history_info,
        bugs_description,
        is_buggy_line_labeled
    )
    prompt = f"{START}{B_INST} {B_SYS}{SYSTEM_PROMPT}{E_SYS}{USER_INPUT} {E_INST}"
    return prompt


def construct_prompt_codellama_34b_python(bug_info, history_category_flag, bug_history_info, bugs_description):
    SYSTEM_PROMPT, USER_INPUT = generate_system_prompt_and_user_input(
        False,
        bug_info,
        history_category_flag,
        bug_history_info,
        bugs_description
    )
    prompt = f"{SYSTEM_PROMPT}\n\n{USER_INPUT}"
    return prompt


def construct_prompt_codellama_70b_instruct(bug_info, history_category_flag, bug_history_info, bugs_description):
    SYSTEM_PROMPT, USER_INPUT = generate_system_prompt_and_user_input(
        True,
        bug_info,
        history_category_flag,
        bug_history_info,
        bugs_description
    )
    prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_INPUT}
    ]
    return prompt


def construct_prompt_codellama_70b_python(bug_info, history_category_flag, bug_history_info, bugs_description):
    SYSTEM_PROMPT, USER_INPUT = generate_system_prompt_and_user_input(
        False,
        bug_info,
        history_category_flag,
        bug_history_info,
        bugs_description
    )
    prompt = f"{SYSTEM_PROMPT}\n\n{USER_INPUT}"
    return prompt


def generate_system_prompt_and_user_input(is_instruct_model: bool, bug_info, history_category_flag, bug_history_info,
                                          bugs_description, is_buggy_line_labeled):
    SYSTEM_PROMPT = ""
    USER_INPUT = ""

    project_name = bug_info['project_name']
    buggy_file_name = bug_info['file']['file_name']
    buggy_function_name = bug_info['function']['function_name']
    date_time = bug_info['commit']['commit_date']
    bug_desc = bugs_description['description']
    buggy_line_content = bug_info['buggy_line_content'].strip()
    buggy_code = bug_info['function']['function_before']

    # manually change the format of the buggy line content
    if str(bug_info['id']) == '14':
        buggy_line_content = "head = int(head) - 1 if head != '0' else id_"
    elif str(bug_info['id']) == '16':
        buggy_line_content = "return re.sub('&([^;]+;)', lambda m: _htmlentity_transform(m.group(1)), s)"
    elif str(bug_info['id']) == '18':
        buggy_line_content = "if re.match('^(?:https?:)?//', path):"
    elif str(bug_info['id']) == '21':
        buggy_line_content = "(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:\\\\s*:)?|"
    elif str(bug_info['id']) == '22':
        buggy_line_content = "m = re.match('(?:https?:|)//[^/]+/(?:[^/?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)"
    elif str(bug_info['id']) == '23':
        buggy_line_content = "msg = 'missing required arguments: %s' % ', '.join(missing)"
    elif str(bug_info['id']) == '46':
        buggy_line_content = "elif left_value != right_value:"
    elif str(bug_info['id']) == '59':
        buggy_line_content = "if not force and now - self.last_update < self.interval and (current < self.target):"
    elif str(bug_info['id']) == '63':
        buggy_line_content = "setter(self, max(vmin, vmax, oldmax), min(vmin, vmax, oldmin), ignore=True)"
    elif str(bug_info['id']) == '64':
        buggy_line_content = "setter(self, max(vmin, vmax, oldmax), min(vmin, vmax, oldmin), ignore=True)"

    if is_buggy_line_labeled:
        try:
            buggy_code = get_labeled_buggy_code(buggy_code, buggy_line_content, str(bug_info['id']))
        except:
            print(f"bug_id: {str(bug_info['id'])} meet error when label the buggy line")
            # buggy_code = manually_label_buggy_code(buggy_code, buggy_line_content, str(bug_info['id']))

    assert buggy_code != ""

    buggy_line_content_inst = "" if is_buggy_line_labeled else f"# The buggy line content: {buggy_line_content}\n\n"

    project_name_inst = f"# The project name: {project_name}\n"
    buggy_file_name_inst = f"# The buggy file name: {buggy_file_name}\n"
    buggy_function_name_inst = f"# The buggy function name: {buggy_function_name}\n"
    date_time_inst = f"# The date time: {date_time}\n"
    bug_desc_inst = f"# The bug description: {bug_desc}\n\n"
    buggy_code_inst = f"# The buggy code snippet:\n{buggy_code}\n\n"
    fixed_inst = f"# The fixed code snippet: "

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
    label_buggy_line_instruct = " The buggy line is identified within the #<BUGGY_LINE> section in the buggy code snippet." if is_buggy_line_labeled else ""

    # 1. baseline
    USER_INPUT_BASELINE = f"{project_name_inst}{buggy_file_name_inst}{buggy_function_name_inst}{date_time_inst}{buggy_code_inst}{bug_desc_inst}{buggy_line_content_inst}{fixed_inst}"
    SYSTEM_PROMPT_BASELINE = (f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. "
                              f"I mined a buggy code snippet and its related information from GitHub. "
                              f"I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet,"
                              f" the corresponding bug description that might indicate how this buggy code should be fixed, "
                              f"and the buggy line content that might suggest where this buggy code should be fixed. "
                              f"Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}")

    if history_category_flag == HistoryCategory.baseline.value:
        SYSTEM_PROMPT = SYSTEM_PROMPT_BASELINE
        USER_INPUT = USER_INPUT_BASELINE

    # 1.1 HAFix_36
    if history_category_flag == HistoryCategory.hafix_3_6.value:
        SYSTEM_PROMPT = (f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I "
                         f"mined a buggy code snippet and its related information from GitHub. To help you better "
                         f"understand how this code snippet evolved, I will first provide you with the co-evolved "
                         f"functions' names of relevant code files in the blame commit, and all co-evolved "
                         f"files’ names in the blame commit. Then, I will provide you with "
                         f"the project name, buggy file name, buggy function name, the date time, the current version "
                         f"of this buggy code snippet, the corresponding bug description that might indicate how this "
                         f"buggy code should be fixed, and the buggy line content that might suggest where this buggy "
                         f"code should be fixed. Please only generate the fixed code snippet of this buggy code, "
                         f"don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}")
        USER_INPUT = f"{co_evolved_functions_name_all_files_inst}{files_name_blame_inst}{USER_INPUT_BASELINE}"

    # 1.2 HAFix_362
    if history_category_flag == HistoryCategory.hafix_3_6_2.value:
        SYSTEM_PROMPT = (f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I "
                         f"mined a buggy code snippet and its related information from GitHub. To help you better "
                         f"understand how this code snippet evolved, I will first provide you with the co-evolved "
                         f"functions' names of relevant code files in the blame commit, all co-evolved "
                         f"files’ names in the blame commit, and the co-evolved "
                         f"functions' names of this source code file in the blame commit. Then, I will provide you with "
                         f"the project name, buggy file name, buggy function name, the date time, the current version "
                         f"of this buggy code snippet, the corresponding bug description that might indicate how this "
                         f"buggy code should be fixed, and the buggy line content that might suggest where this buggy "
                         f"code should be fixed. Please only generate the fixed code snippet of this buggy code, "
                         f"don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}")
        USER_INPUT = f"{co_evolved_functions_name_all_files_inst}{files_name_blame_inst}{co_evolved_functions_name_modified_file_inst}{USER_INPUT_BASELINE}"

    # 1.3 HAFix_3625
    if history_category_flag == HistoryCategory.hafix_3_6_2_5.value:
        SYSTEM_PROMPT = (f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I "
                         f"mined a buggy code snippet and its related information from GitHub. To help you better "
                         f"understand how this code snippet evolved, I will first provide you with the co-evolved "
                         f"functions' names of relevant code files in the blame commit, all co-evolved "
                         f"files’ names in the blame commit, the co-evolved "
                         f"functions' names of this source code file in the blame commit, and all functions"
                         f"names of relevant source code files in the blame commit. Then, I will provide you with "
                         f"the project name, buggy file name, buggy function name, the date time, the current version "
                         f"of this buggy code snippet, the corresponding bug description that might indicate how this "
                         f"buggy code should be fixed, and the buggy line content that might suggest where this buggy "
                         f"code should be fixed. Please only generate the fixed code snippet of this buggy code, "
                         f"don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}")
        USER_INPUT = (f"{co_evolved_functions_name_all_files_inst}{files_name_blame_inst}"
                      f"{co_evolved_functions_name_modified_file_inst}{functions_name_all_files_inst}{USER_INPUT_BASELINE}")

        # 1.4 HAFix_36258
    if history_category_flag == HistoryCategory.hafix_3_6_2_5_8.value:
        SYSTEM_PROMPT = (
            f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I "
            f"mined a buggy code snippet and its related information from GitHub. To help you better "
            f"understand how this code snippet evolved, I will first provide you with the co-evolved "
            f"functions' names of relevant code files in the blame commit, all co-evolved "
            f"files’ names in the blame commit, the co-evolved "
            f"functions' names of this source code file in the blame commit, all functions"
            f"names of relevant source code files in the blame commit, and the historical "
            f"patch code which consists of changes mined from the code base, it specifies the removed "
            f"and added lines. Then, I will provide you with "
            f"the project name, buggy file name, buggy function name, the date time, the current version "
            f"of this buggy code snippet, the corresponding bug description that might indicate how this "
            f"buggy code should be fixed, and the buggy line content that might suggest where this buggy "
            f"code should be fixed. Please only generate the fixed code snippet of this buggy code, "
            f"don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}")
        File_HISTORY_INPUT = get_file_history_input(bug_history_info)
        USER_INPUT = (f"{co_evolved_functions_name_all_files_inst}{files_name_blame_inst}"
                      f"{co_evolved_functions_name_modified_file_inst}{functions_name_all_files_inst}"
                      f"{File_HISTORY_INPUT}{USER_INPUT_BASELINE}")

    # 1.5 HAFix_362587
    if history_category_flag == HistoryCategory.hafix_3_6_2_5_8_7.value:
        SYSTEM_PROMPT = (
            f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I "
            f"mined a buggy code snippet and its related information from GitHub. To help you better "
            f"understand how this code snippet evolved, I will first provide you with the co-evolved "
            f"functions' names of relevant code files in the blame commit, all co-evolved "
            f"files’ names in the blame commit, the co-evolved "
            f"functions' names of this source code file in the blame commit, all functions"
            f"names of relevant source code files in the blame commit, the historical "
            f"patch code which consists of changes mined from the code base, it specifies the removed "
            f"and added lines, and a pair "
                         f"of a historical version of this code snippet, including the first version of this code "
                         f"snippet, the historical commit date time, the historical commit message, "
                         f"and the second version of this code snippet, note the historical commit message here "
                         f"might indicate how this code was changed between these two versions. Then, "
            f"I will provide you with"
            f"the project name, buggy file name, buggy function name, the date time, the current version "
            f"of this buggy code snippet, the corresponding bug description that might indicate how this "
            f"buggy code should be fixed, and the buggy line content that might suggest where this buggy "
            f"code should be fixed. Please only generate the fixed code snippet of this buggy code, "
            f"don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}")
        File_HISTORY_INPUT = get_file_history_input(bug_history_info)
        FUNCTION_HISTORY_INPUT = get_function_history_input(bug_history_info)
        USER_INPUT = (f"{co_evolved_functions_name_all_files_inst}{files_name_blame_inst}"
                      f"{co_evolved_functions_name_modified_file_inst}{functions_name_all_files_inst}"
                      f"{File_HISTORY_INPUT}{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}")

    # 1.6 HAFix_36257
    if history_category_flag == HistoryCategory.hafix_3_6_2_5_7.value:
        SYSTEM_PROMPT = (f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I "
                         f"mined a buggy code snippet and its related information from GitHub. To help you better "
                         f"understand how this code snippet evolved, I will first provide you with the co-evolved "
                         f"functions' names of relevant code files in the blame commit, all co-evolved "
                         f"files’ names in the blame commit, the co-evolved "
                         f"functions' names of this source code file in the blame commit, all functions"
                         f"names of relevant source code files in the blame commit, and a pair of a "
                         f"historical version of this code snippet, including the first version of this code snippet, "
                         f"the historical commit date time, the historical commit message, and the second version of "
                         f"this code snippet, note the historical commit message here might indicate how this code "
                         f"was changed between these two versions. Then, I will provide you with "
                         f"the project name, buggy file name, buggy function name, the date time, the current version "
                         f"of this buggy code snippet, the corresponding bug description that might indicate how this "
                         f"buggy code should be fixed, and the buggy line content that might suggest where this buggy "
                         f"code should be fixed. Please only generate the fixed code snippet of this buggy code, "
                         f"don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}")
        FUNCTION_HISTORY_INPUT = get_function_history_input(bug_history_info)
        USER_INPUT = (f"{co_evolved_functions_name_all_files_inst}{files_name_blame_inst}"
                      f"{co_evolved_functions_name_modified_file_inst}{functions_name_all_files_inst}"
                      f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}")

    # 2. baseline_co_evolved_functions_name_modified_file_blame
    elif history_category_flag == HistoryCategory.baseline_co_evolved_functions_name_modified_file_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the co-evolved functions' names of this source code file in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{co_evolved_functions_name_modified_file_inst}{USER_INPUT_BASELINE}"

    # 21. co_evolved_functions_name_modified_file_blame_recursive
    elif history_category_flag == HistoryCategory.co_evolved_functions_name_modified_file_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of co-evolved functions' names of this source code file mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = (
            f"# The first group is co-evolved functions' names of this source code file before the blame commit: {co_evolved_functions_name_modified_file_recursive}\n\n"
            f"# The second group is co-evolved functions' names of this source code file in the blame commit: {co_evolved_functions_name_modified_file}\n\n"
            f"{USER_INPUT_BASELINE}")


    # 3. baseline_co_evolved_functions_name_all_files_blame
    elif history_category_flag == HistoryCategory.baseline_co_evolved_functions_name_all_files_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the co-evolved functions' names of relevant code files in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{co_evolved_functions_name_all_files_inst}{USER_INPUT_BASELINE}"

    # 31. co_evolved_functions_name_modified_file_blame_recursive
    elif history_category_flag == HistoryCategory.co_evolved_functions_name_all_files_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of co-evolved functions' names of relevant code files mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = (
            f"# The first group is co-evolved functions' names of relevant code files before the blame commit: {co_evolved_functions_name_all_files_recursive}\n\n"
            f"# The second group is co-evolved functions' names of relevant code files in the blame commit: {co_evolved_functions_name_all_files}\n\n"
            f"{USER_INPUT_BASELINE}")


    # 4. baseline_all_functions_name_modified_file_blame
    elif history_category_flag == HistoryCategory.baseline_all_functions_name_modified_file_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all functions' names of this source code file in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{functions_name_modified_file_inst}{USER_INPUT_BASELINE}"

    # 41. all_functions_name_modified_file_blame_recursive
    elif history_category_flag == HistoryCategory.all_functions_name_modified_file_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of all functions' names of this source code file mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = (
            f"# The first group is all functions' names of this source code file before the blame commit: {functions_name_modified_file_recursive}\n\n"
            f"# The second group is all functions' names of this source code file in the blame commit: {functions_name_modified_file}\n\n"
            f"{USER_INPUT_BASELINE}")



    # 5. baseline_all_functions_name_all_files_blame
    elif history_category_flag == HistoryCategory.baseline_all_functions_name_all_files_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all functions' names of relevant source code files in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{functions_name_all_files_inst}{USER_INPUT_BASELINE}"

    # 51. all_functions_name_all_files_blame_recursive
    elif history_category_flag == HistoryCategory.all_functions_name_all_files_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of all functions' names of relevant source code files mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = (
            f"# The first group is all functions' names of relevant source code files before the blame commit: {functions_name_all_files_recursive}\n\n"
            f"# The second group is all functions' names of relevant source code files in the blame commit: {functions_name_all_files}\n\n"
            f"{USER_INPUT_BASELINE}")



    # 6. baseline_all_co_evolved_files_name_blame
    elif history_category_flag == HistoryCategory.baseline_all_co_evolved_files_name_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all co-evolved files’ names in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{files_name_blame_inst}{USER_INPUT_BASELINE}"

    # 61. all_co_evolved_files_name_blame_recursive
    elif history_category_flag == HistoryCategory.all_co_evolved_files_name_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of co-evolved files’ names of relevant source code files mined from historical commits in the code base. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = (
            f"# The first group is the co-evolved files’ names of relevant source code files before the blame commit: {files_name_blame_recursive}\n\n"
            f"# The second group is the co-evolved files’ names of relevant source code files in the blame commit: {files_name_blame}\n\n"
            f"{USER_INPUT_BASELINE}")



    # 7. baseline_function_code_pair_blame
    elif history_category_flag == HistoryCategory.baseline_function_code_pair_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with a pair of a historical version of this code snippet, including the first version of this code snippet, the historical commit date time, the historical commit message, and the second version of this code snippet, note the historical commit message here might indicate how this code was changed between these two versions. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        FUNCTION_HISTORY_INPUT = get_function_history_input(bug_history_info)
        USER_INPUT = f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    # 71. function_code_pair_blame_recursive
    elif history_category_flag == HistoryCategory.function_code_pair_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of code pairs mined from historical commits in the code base. Each group is a pair of a historical version of this code snippet, including the first version of this code snippet, the historical commit date time, the historical commit message, and the second version of this code snippet, note the historical commit message here might indicate how this code was changed between these two versions. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        FUNCTION_HISTORY_INPUT = get_function_history_input_recursive(bug_history_info)
        USER_INPUT = f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}"



    # 8. baseline_file_code_patch_blame
    elif history_category_flag == HistoryCategory.baseline_file_code_patch_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the historical patch code which consists of changes mined from the code base. It specifies the removed and added lines. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        File_HISTORY_INPUT = get_file_history_input(bug_history_info)
        USER_INPUT = f"{File_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    # 81. file_code_patch_blame_recursive
    elif history_category_flag == HistoryCategory.file_code_patch_blame_recursive.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in Python. I mined a buggy code snippet and its related historical information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with two groups of the historical patch code which consists of changes mined from historical commits in the code base. It specifies the removed and added lines. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. Please only generate the fixed code snippet of this buggy code, don't explain any other things. {label_buggy_line_instruct} {wrap_instruct}"
        FUNCTION_HISTORY_INPUT = get_file_history_input_recursive(bug_history_info)
        USER_INPUT = f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    return SYSTEM_PROMPT, USER_INPUT


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


# def manually_label_buggy_code(buggy_code: str, buggy_line_content: str, bug_id: str):
#     # manually change the format of the buggy line content
#     if bug_id == '14':
#         buggy_line_content = "head = int(head) - 1 if head != '0' else id_"
#     elif bug_id == '16':
#         buggy_line_content = "return re.sub('&([^;]+;)', lambda m: _htmlentity_transform(m.group(1)), s)"
#     elif bug_id == '18':
#         buggy_line_content = "if re.match('^(?:https?:)?//', path):"
#     elif bug_id == '21':
#         buggy_line_content = "(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:\\\\s*:)?|"
#     elif bug_id == '22':
#         buggy_line_content = "m = re.match('(?:https?:|)//[^/]+/(?:[^/?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)"
#     elif bug_id == '23':
#         buggy_line_content = "msg = 'missing required arguments: %s' % ', '.join(missing)"
#     elif bug_id == '46':
#         buggy_line_content = "elif left_value != right_value:"
#     elif bug_id == '59':
#         buggy_line_content = "if not force and now - self.last_update < self.interval and (current < self.target):"
#     elif bug_id == '63':
#         buggy_line_content = "setter(self, max(vmin, vmax, oldmax), min(vmin, vmax, oldmin), ignore=True)"
#     elif bug_id == '64':
#         buggy_line_content = "setter(self, max(vmin, vmax, oldmax), min(vmin, vmax, oldmin), ignore=True)"
#
#     buggy_code = get_labeled_buggy_code(buggy_code, buggy_line_content, bug_id)
#     return buggy_code


def get_labeled_buggy_code(buggy_code: str, buggy_line_content: str, bug_id: str):
    # There are more than one buggy line code in the buggy function
    if bug_id == '35':
        buggy_code = "def _get_with(self, key):\n    if isinstance(key, slice):\n        return self._slice(key)\n    elif isinstance(key, ABCDataFrame):\n        raise TypeError('Indexing a Series with DataFrame is not supported, use the appropriate DataFrame column')\n    elif isinstance(key, tuple):\n        try:\n            return self._get_values_tuple(key)\n        except ValueError:\n            if len(key) == 1:\n                key = key[0]\n                if isinstance(key, slice):\n                    return self._get_values(key)\n            raise\n    if not isinstance(key, (list, np.ndarray, Series, Index)):\n        key = list(key)\n    if isinstance(key, Index):\n        key_type = key.inferred_type\n    else:\n        key_type = lib.infer_dtype(key, skipna=False)\n    if key_type == 'integer':\n        if self.index.is_integer() or self.index.is_floating():\n            return self.loc[key]\n        elif isinstance(self.index, IntervalIndex):\n            indexer = self.index.get_indexer_for(key)\n            return self.iloc[indexer]\n        else:\n            #<BUGGY_LINE>\n            return self._get_values(key)\n            #<BUGGY_LINE>\n    if isinstance(key, (list, tuple)):\n        if len(key) == 1 and isinstance(key[0], slice):\n            return self._get_values(key)\n        return self.loc[key]\n    return self.reindex(key)"
        return buggy_code
    elif bug_id == '36':
        buggy_code = "def __init__(self, df, na_rep: str='', float_format: Optional[str]=None, cols: Optional[Sequence[Label]]=None, header: Union[Sequence[Label], bool]=True, index: bool=True, index_label: Optional[Union[Label, Sequence[Label]]]=None, merge_cells: bool=False, inf_rep: str='inf', style_converter: Optional[Callable]=None):\n    self.rowcounter = 0\n    self.na_rep = na_rep\n    if hasattr(df, 'render'):\n        self.styler = df\n        df = df.data\n        if style_converter is None:\n            style_converter = CSSToExcelConverter()\n        self.style_converter = style_converter\n    else:\n        self.styler = None\n    self.df = df\n    if cols is not None:\n        if not len(Index(cols) & df.columns):\n            raise KeyError('passes columns are not ALL present dataframe')\n        if len(Index(cols) & df.columns) != len(cols):\n            raise KeyError(\"Not all names specified in 'columns' are found\")\n        #<BUGGY_LINE>\n        self.df = df\n        #<BUGGY_LINE>\n    self.columns = self.df.columns\n    self.float_format = float_format\n    self.index = index\n    self.index_label = index_label\n    self.header = header\n    self.merge_cells = merge_cells\n    self.inf_rep = inf_rep"
        return buggy_code
    elif bug_id == '39':
        buggy_code = "def _try_convert_data(self, name, data, use_dtypes=True, convert_dates=True):\n    \"\"\"\n        Try to parse a ndarray like into a column by inferring dtype.\n        \"\"\"\n    if use_dtypes:\n        if not self.dtype:\n            return (data, False)\n        elif self.dtype is True:\n            pass\n        else:\n            dtype = self.dtype.get(name) if isinstance(self.dtype, dict) else self.dtype\n            if dtype is not None:\n                try:\n                    dtype = np.dtype(dtype)\n                    return (data.astype(dtype), True)\n                except (TypeError, ValueError):\n                    return (data, False)\n    if convert_dates:\n        new_data, result = self._try_convert_to_date(data)\n        if result:\n            return (new_data, True)\n    result = False\n    if data.dtype == 'object':\n        try:\n            data = data.astype('float64')\n            result = True\n        except (TypeError, ValueError):\n            pass\n    if data.dtype.kind == 'f':\n        if data.dtype != 'float64':\n            try:\n                data = data.astype('float64')\n                result = True\n            except (TypeError, ValueError):\n                pass\n    if len(data) and (data.dtype == 'float' or data.dtype == 'object'):\n        try:\n            new_data = data.astype('int64')\n            if (new_data == data).all():\n                data = new_data\n                result = True\n        #<BUGGY_LINE>\n        except (TypeError, ValueError):\n        #<BUGGY_LINE>\n            pass\n    if data.dtype == 'int':\n        try:\n            data = data.astype('int64')\n            result = True\n        except (TypeError, ValueError):\n            pass\n    return (data, result)"
        return buggy_code
    elif bug_id == '54':
        buggy_code = "def initialize(self, make_current=None):\n    if make_current is None:\n        if IOLoop.current(instance=False) is None:\n            self.make_current()\n    elif make_current:\n        #<BUGGY_LINE>\n        if IOLoop.current(instance=False) is None:\n        #<BUGGY_LINE>\n            raise RuntimeError('current IOLoop already exists')\n        self.make_current()"
        return buggy_code
    # rewrite the buggy code format
    elif bug_id == '67':
        buggy_code = "def __len__(self):\n    return self.total if self.iterable is None else         (self.iterable.shape[0] if hasattr(self.iterable, \"shape\")\n         else len(self.iterable) if hasattr(self.iterable, \"__len__\")\n        #<BUGGY_LINE>\n        else self.total)\n        #<BUGGY_LINE>"
        return buggy_code

    buggy_line_content_strip = buggy_line_content.strip(" ")
    buggy_code_split = buggy_code.split(buggy_line_content_strip)
    assert len(buggy_code_split) == 2
    buggy_code_indent = buggy_code_split[0][len(buggy_code_split[0].strip(" ")):]
    labeled_code = buggy_code_split[
                       0] + "#<BUGGY_LINE>\n" + buggy_code_indent + buggy_line_content_strip + "\n" + buggy_code_indent + "#<BUGGY_LINE>" + \
                   buggy_code_split[1]
    return labeled_code
