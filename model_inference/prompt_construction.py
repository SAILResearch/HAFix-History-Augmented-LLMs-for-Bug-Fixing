from util import HistoryCategory

BUG_LABEL_TOKEN = "#<BUGGY_LINE>"
BUG_MASK_TOKEN = "<FILL_ME>"

START = "<s>"
B_INST, E_INST = "[INST]", "[/INST]"  # for instruction models
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
MAX_NUM_FUNCTION_NAME = 300
MASK_INST = "# Generate one line of the infilling code:"


def construct_prompt(dataset_name, model_id, prompt_style, bug_info, history_category_flag, bug_history_info, bugs_description, dataset_language):
    SYSTEM_PROMPT, USER_INPUT, BUGGY_MASKED, indent_space_str = generate_system_prompt_and_user_input(
        dataset_name,
        model_id,
        prompt_style,
        bug_info,
        history_category_flag,
        bug_history_info,
        bugs_description,
        dataset_language
    )
    if "codellama" in model_id:
        if prompt_style == "InstructionMask":
            prompt = f"{START}{B_INST} {B_SYS}{SYSTEM_PROMPT}{E_SYS}{USER_INPUT}\n{E_INST}\n{BUGGY_MASKED}\n\n{MASK_INST}"
        else:
            prompt = f"{START}{B_INST} {B_SYS}{SYSTEM_PROMPT}{E_SYS}{USER_INPUT} {E_INST}"
    elif "deepseek" in model_id:
        if prompt_style == "InstructionMask":
            prompt = f"{SYSTEM_PROMPT}\n\n{USER_INPUT}\n{BUGGY_MASKED}\n\n{MASK_INST}"
        else:
            prompt = f"{SYSTEM_PROMPT}\n\n{USER_INPUT}"
    else:
        print(f"Error: model {model_id} not support, please use correct model!")
        return
    return prompt, BUGGY_MASKED, indent_space_str


def generate_system_prompt_and_user_input(dataset_name, model_id, prompt_style, bug_info, history_category_flag,
                                          bug_history_info,
                                          bugs_description,
                                          dataset_language):
    SYSTEM_PROMPT = ""
    USER_INPUT = ""

    project_name = bug_info['project_name']
    buggy_file_name = bug_info['file']['file_name']
    buggy_function_name = bug_info['function']['function_name']
    date_time = bug_info['commit']['commit_date']
    bug_desc = bugs_description['description']
    buggy_line_content = bug_info['buggy_line_content'].strip()
    buggy_code = bug_info['function']['function_before']

    BUGGY_MASKED = ""
    indent_space_str = ""

    # 1. bugsinpy dataset
    if dataset_name == "bugsinpy":
        if prompt_style == "InstructionMask":
            try:
                BUGGY_MASKED = mask_code_manually_bugsinpy(buggy_code, buggy_line_content, str(bug_info['id']))
                # BUGGY_MASKED = mask_code(buggy_code, buggy_line_content)
            except:
                print(f"bug_id: {str(bug_info['id'])} meet error when mask the buggy line")

            buggy_line_content = get_buggy_line_content_for_special_cases_of_bugsinpy(str(bug_info['id']), buggy_line_content)

            try:
                _, indent_space_str = label_code_manually_bugsinpy(buggy_code, buggy_line_content, str(bug_info['id']))
            except:
                print(f"bug_id: {str(bug_info['id'])} meet error when obtain the indent space of buggy line")

        # right now only bugsinpy has buggy line labeled
        if prompt_style == "InstructionLabel":
            try:
                buggy_code, _ = label_code_manually_bugsinpy(buggy_code, buggy_line_content, str(bug_info['id']))
            except:
                print(f"bug_id: {str(bug_info['id'])} meet error when label the buggy line")
    # 2. defects4j dataset
    elif dataset_name == "defects4j":
        buggy_line_content = get_buggy_line_content_for_special_cases_of_defects4j(bug_info, buggy_line_content)
        if prompt_style == "InstructionMask":
            try:
                BUGGY_MASKED = mask_code_manually_defects4j(buggy_code, buggy_line_content, str(bug_info['id']))
            except:
                print(f"bug_id: {str(bug_info['id'])} meet error when mask the buggy line")

            try:
                _, indent_space_str = label_code_manually_defects4j(buggy_code, buggy_line_content, str(bug_info['id']))
            except:
                print(f"bug_id: {str(bug_info['id'])} meet error when obtain the indent space of buggy line")

        if prompt_style == "InstructionLabel":
            try:
                buggy_code, _ = label_code_manually_defects4j(buggy_code, buggy_line_content, str(bug_info['id']))
            except:
                print(f"bug_id: {str(bug_info['id'])} meet error when label the buggy line")
    else:
        print(f"Error: dataset {dataset_name} not support, please use correct dataset name!")
        return

    assert buggy_code != ""

    buggy_line_content_inst = "" if prompt_style == "InstructionLabel" else \
        f"{get_inst('The buggy line content: ', model_id)}{buggy_line_content}\n\n"

    project_name_inst = f"{get_inst('The project name: ', model_id)}{project_name}\n"
    buggy_file_name_inst = f"{get_inst('The buggy file name: ', model_id)}{buggy_file_name}\n"
    buggy_function_name_inst = f"{get_inst('The buggy function name: ', model_id)}{buggy_function_name}\n"
    date_time_inst = f"{get_inst('The date time: ', model_id)}{date_time}\n"
    bug_desc_inst = f"{get_inst('The bug description: ', model_id)}{bug_desc}\n\n"
    buggy_code_inst = f"{get_inst('The buggy code snippet:', model_id)}\n{buggy_code}\n\n"

    fixed_inst = ""
    if 'codellama' in model_id:
        if prompt_style != "InstructionMask":
            fixed_inst = f"# The fixed code snippet: "
    elif 'deepseek' in model_id:
        if prompt_style != "InstructionMask":
            fixed_inst = f"Fixed version of the {dataset_language} function {buggy_function_name}: \n\n### Response:"
    else:
        print(f"Error: model {model_id} not support, please use correct model!")
        return

    wrap_instruct = (
        f"In your generated code, you must only edit the buggy line and all other lines of code and the "
        f"function name must remain exactly the same as in the original buggy version. Please generate "
        f"the entire fixed version of the {dataset_language} function, not just the modified lines. Do "
        f"not include any explanation or comments outside the code block. Please wrap your fixed version "
        f"of the {dataset_language} function between ```{dataset_language.lower()} and ```"
    ) if prompt_style != "InstructionMask" else ""

    label_buggy_line_instruct = (
        f"The buggy line is identified within the {BUG_LABEL_TOKEN} section in the buggy code snippet."
    ) if prompt_style == "InstructionLabel" else ""

    change_scope_instruct = (
        "Please only generate the fixed code snippet of this buggy code, don't explain any other things."
    ) if prompt_style != "InstructionMask" else (
        "There is just one line being needed to be infilled. Please only generate one line of code, "
        "don't explain any other things."
    )

    # 2
    co_evolved_functions_name_modified_file_ = list(
        bug_history_info['blame_commit']['function']['functions_name_co_evolved_modified_file'])
    if len(co_evolved_functions_name_modified_file_) > MAX_NUM_FUNCTION_NAME:
        co_evolved_functions_name_modified_file_ = co_evolved_functions_name_modified_file_[:MAX_NUM_FUNCTION_NAME]
    co_evolved_functions_name_modified_file = ', '.join(co_evolved_functions_name_modified_file_)

    # 3
    co_evolved_functions_name_all_files_ = list(
        bug_history_info['blame_commit']['function']['functions_name_co_evolved_all_files'])
    if len(co_evolved_functions_name_all_files_) > MAX_NUM_FUNCTION_NAME:
        co_evolved_functions_name_all_files_ = co_evolved_functions_name_all_files_[:MAX_NUM_FUNCTION_NAME]
    co_evolved_functions_name_all_files = ', '.join(co_evolved_functions_name_all_files_)

    # 4
    functions_name_modified_file_ = list(bug_history_info['blame_commit']['function']['functions_name_modified_file'])
    if len(functions_name_modified_file_) > MAX_NUM_FUNCTION_NAME:
        functions_name_modified_file_ = functions_name_modified_file_[:MAX_NUM_FUNCTION_NAME]
    functions_name_modified_file = ', '.join(functions_name_modified_file_)

    # 5
    functions_name_all_files_ = list(bug_history_info['blame_commit']['function']['functions_name_all_files'])
    if len(functions_name_all_files_) > MAX_NUM_FUNCTION_NAME:
        functions_name_all_files_ = functions_name_all_files_[:MAX_NUM_FUNCTION_NAME]
    functions_name_all_files = ', '.join(functions_name_all_files_)

    # 6
    files_name_blame_ = list(bug_history_info['blame_commit']['file']['files_name_in_blame_commit'])
    if len(files_name_blame_) > MAX_NUM_FUNCTION_NAME:
        files_name_blame_ = files_name_blame_[:MAX_NUM_FUNCTION_NAME]
    files_name_blame = ', '.join(files_name_blame_)

    temp2 = "Co-evolved functions' names of this source code file in the blame commit: "
    co_evolved_functions_name_modified_file_inst = (
        f"{get_inst(temp2, model_id)}{co_evolved_functions_name_modified_file}\n\n")

    temp3 = "Co-evolved functions' names of relevant code files in the blame commit: "
    co_evolved_functions_name_all_files_inst = (
        f"{get_inst(temp3, model_id)}{co_evolved_functions_name_all_files}\n\n")

    temp4 = "All functions' names of this source code file in the blame commit: "
    functions_name_modified_file_inst = f"{get_inst(temp4, model_id)}{functions_name_modified_file}\n\n"

    temp5 = "All functions' names of relevant source code files in the blame commit: "
    functions_name_all_files_inst = f"{get_inst(temp5, model_id)}{functions_name_all_files}\n\n"

    temp6 = "The co-evolved files’ names of relevant source code files in the blame commit: "
    files_name_blame_inst = f"{get_inst(temp6, model_id)}{files_name_blame}\n\n"

    # 1. baseline
    USER_INPUT_BASELINE = (f"{project_name_inst}{buggy_file_name_inst}{buggy_function_name_inst}{date_time_inst}"
                           f"{buggy_code_inst}{bug_desc_inst}{buggy_line_content_inst}{fixed_inst}")
    SYSTEM_PROMPT_BASELINE = (
        f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. "
        f"I mined a buggy code snippet and its related information from GitHub. I will provide you with the "
        f"project name, buggy file name, buggy function name, the date time, the current version of this "
        f"buggy code snippet, the corresponding bug description that might indicate how this buggy code "
        f"should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. "
        f"{change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
    )

    if history_category_flag == HistoryCategory.baseline.value:
        SYSTEM_PROMPT = SYSTEM_PROMPT_BASELINE
        USER_INPUT = USER_INPUT_BASELINE

    # 2. baseline_co_evolved_functions_name_modified_file_blame
    elif history_category_flag == HistoryCategory.baseline_co_evolved_functions_name_modified_file_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the co-evolved functions' names of this source code file in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. {change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{co_evolved_functions_name_modified_file_inst}{USER_INPUT_BASELINE}"

    # 3. baseline_co_evolved_functions_name_all_files_blame
    elif history_category_flag == HistoryCategory.baseline_co_evolved_functions_name_all_files_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the co-evolved functions' names of relevant code files in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. {change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{co_evolved_functions_name_all_files_inst}{USER_INPUT_BASELINE}"

    # 4. baseline_all_functions_name_modified_file_blame
    elif history_category_flag == HistoryCategory.baseline_all_functions_name_modified_file_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all functions' names of this source code file in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. {change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{functions_name_modified_file_inst}{USER_INPUT_BASELINE}"

    # 5. baseline_all_functions_name_all_files_blame
    elif history_category_flag == HistoryCategory.baseline_all_functions_name_all_files_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all functions' names of relevant source code files in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. {change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{functions_name_all_files_inst}{USER_INPUT_BASELINE}"

    # 6. baseline_all_co_evolved_files_name_blame
    elif history_category_flag == HistoryCategory.baseline_all_co_evolved_files_name_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with all co-evolved files’ names in the blame commit. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. {change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
        USER_INPUT = f"{files_name_blame_inst}{USER_INPUT_BASELINE}"

    # 7. baseline_function_code_pair_blame
    elif history_category_flag == HistoryCategory.baseline_function_code_pair_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with a pair of a historical version of this code snippet, including the first version of this code snippet, the historical commit date time, the historical commit message, and the second version of this code snippet, note the historical commit message here might indicate how this code was changed between these two versions. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. {change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
        FUNCTION_HISTORY_INPUT = get_function_history_input(bug_history_info, model_id)
        USER_INPUT = f"{FUNCTION_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    # 8. baseline_file_code_patch_blame
    elif history_category_flag == HistoryCategory.baseline_file_code_patch_blame.value:
        SYSTEM_PROMPT = f"You are a helpful and honest code assistant expert in fixing the buggy code in {dataset_language}. I mined a buggy code snippet and its related information from GitHub. To help you better understand how this code snippet evolved, I will first provide you with the historical patch code which consists of changes mined from the code base. It specifies the removed and added lines. Then, I will provide you with the project name, buggy file name, buggy function name, the date time, the current version of this buggy code snippet, the corresponding bug description that might indicate how this buggy code should be fixed, and the buggy line content that might suggest where this buggy code should be fixed. {change_scope_instruct} {label_buggy_line_instruct} {wrap_instruct}"
        File_HISTORY_INPUT = get_file_history_input(bug_history_info, model_id)
        USER_INPUT = f"{File_HISTORY_INPUT}{USER_INPUT_BASELINE}"

    return SYSTEM_PROMPT, USER_INPUT, BUGGY_MASKED, indent_space_str


def get_function_history_input(bug_history_info, model_id):
    history_function_before = bug_history_info['blame_commit']['function']['function_code_before']
    history_commit_date = bug_history_info['blame_commit']['commit']['commit_date']
    history_commit_msg = bug_history_info['blame_commit']['commit']['commit_message']
    history_function_after = bug_history_info['blame_commit']['function']['function_code_after']

    history_before_inst_code = f"{get_inst('The first version:', model_id)}\n{history_function_before}\n\n"
    history_commit_date_inst = f"{get_inst('The historical commit date time: ', model_id)}{history_commit_date}\n"
    history_commit_inst_msg = f"{get_inst('The historical commit message: ', model_id)}{history_commit_msg}\n\n"
    history_after_inst_code = f"{get_inst('The second version:', model_id)}\n{history_function_after}\n\n"
    return f"{history_before_inst_code}{history_commit_date_inst}{history_commit_inst_msg}{history_after_inst_code}"


def get_file_history_input(bug_history_info, model_id):
    history_commit_date = bug_history_info['blame_commit']['commit']['commit_date']
    history_commit_msg = bug_history_info['blame_commit']['commit']['commit_message']
    history_file_patch = bug_history_info['blame_commit']['file']['file_patch']

    history_commit_date_inst = f"{get_inst('The historical commit date time ', model_id)}{history_commit_date}\n"
    history_commit_inst_msg = f"{get_inst('The historical commit message: ', model_id)}{history_commit_msg}\n\n"
    history_file_patch_inst = f"{get_inst('The historical patch code:', model_id)}\n{history_file_patch}\n\n"
    return f"{history_commit_date_inst}{history_commit_inst_msg}{history_file_patch_inst}"


def get_inst(inst_tag: str, model_id: str):
    if 'codellama' in model_id:
        return f"# {inst_tag}"
    elif 'deepseek' in model_id:
        return inst_tag
    return inst_tag


def get_buggy_line_content_for_special_cases_of_bugsinpy(bug_id: str, buggy_line_content_default):
    # manually give the correct format of the buggy line content
    if bug_id == '14':
        buggy_line_content = "head = int(head) - 1 if head != '0' else id_"
    elif bug_id == '16':
        buggy_line_content = "return re.sub('&([^;]+;)', lambda m: _htmlentity_transform(m.group(1)), s)"
    elif bug_id == '18':
        buggy_line_content = "if re.match('^(?:https?:)?//', path):"
    elif bug_id == '21':
        buggy_line_content = "(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:\\\\s*:)?|"
    elif bug_id == '22':
        buggy_line_content = "m = re.match('(?:https?:|)//[^/]+/(?:[^/?#]+/)?([^/?#]+)/?(?:[?#]|$)', url)"
    elif bug_id == '23':
        buggy_line_content = "msg = 'missing required arguments: %s' % ', '.join(missing)"
    elif bug_id == '46':
        buggy_line_content = "elif left_value != right_value:"
    elif bug_id == '59':
        buggy_line_content = "if not force and now - self.last_update < self.interval and (current < self.target):"
    elif bug_id == '63':
        buggy_line_content = "setter(self, max(vmin, vmax, oldmax), min(vmin, vmax, oldmin), ignore=True)"
    elif bug_id == '64':
        buggy_line_content = "setter(self, max(vmin, vmax, oldmax), min(vmin, vmax, oldmin), ignore=True)"
    else:
        buggy_line_content = buggy_line_content_default
    return buggy_line_content


def get_buggy_line_content_for_special_cases_of_defects4j(bug_id: str, buggy_line_content_default):
    # manually give the correct format of the buggy line content
    if bug_id == '4':
        buggy_line_content = "return \" title=\\\"\" + toolTipText + \"\\\" alt=\\\"\\\"\";"
    elif bug_id == '61':
        buggy_line_content = "return _bindAndReadValues(_considerFilter(_parserFactory.createParser(src), true));"
    elif bug_id == '68':
        buggy_line_content = "clone.classNames(); // creates linked set of class names from class attribute"
    elif bug_id == '82':
        buggy_line_content = "return compute(args[0].computeValue(context), args[1].computeValue(context)) ? Boolean.TRUE : Boolean.FALSE;"
    else:
        buggy_line_content = buggy_line_content_default
    return buggy_line_content


def label_code_manually_bugsinpy(buggy_code: str, buggy_line_content: str, bug_id: str):
    # There are more than one buggy line code in the buggy function
    if bug_id == '35':
        buggy_code = f"def _get_with(self, key):\n    if isinstance(key, slice):\n        return self._slice(key)\n    elif isinstance(key, ABCDataFrame):\n        raise TypeError('Indexing a Series with DataFrame is not supported, use the appropriate DataFrame column')\n    elif isinstance(key, tuple):\n        try:\n            return self._get_values_tuple(key)\n        except ValueError:\n            if len(key) == 1:\n                key = key[0]\n                if isinstance(key, slice):\n                    return self._get_values(key)\n            raise\n    if not isinstance(key, (list, np.ndarray, Series, Index)):\n        key = list(key)\n    if isinstance(key, Index):\n        key_type = key.inferred_type\n    else:\n        key_type = lib.infer_dtype(key, skipna=False)\n    if key_type == 'integer':\n        if self.index.is_integer() or self.index.is_floating():\n            return self.loc[key]\n        elif isinstance(self.index, IntervalIndex):\n            indexer = self.index.get_indexer_for(key)\n            return self.iloc[indexer]\n        else:\n            {BUG_LABEL_TOKEN}\n            return self._get_values(key)\n            {BUG_LABEL_TOKEN}\n    if isinstance(key, (list, tuple)):\n        if len(key) == 1 and isinstance(key[0], slice):\n            return self._get_values(key)\n        return self.loc[key]\n    return self.reindex(key)"
        return buggy_code, "            "
    elif bug_id == '36':
        buggy_code = f"def __init__(self, df, na_rep: str='', float_format: Optional[str]=None, cols: Optional[Sequence[Label]]=None, header: Union[Sequence[Label], bool]=True, index: bool=True, index_label: Optional[Union[Label, Sequence[Label]]]=None, merge_cells: bool=False, inf_rep: str='inf', style_converter: Optional[Callable]=None):\n    self.rowcounter = 0\n    self.na_rep = na_rep\n    if hasattr(df, 'render'):\n        self.styler = df\n        df = df.data\n        if style_converter is None:\n            style_converter = CSSToExcelConverter()\n        self.style_converter = style_converter\n    else:\n        self.styler = None\n    self.df = df\n    if cols is not None:\n        if not len(Index(cols) & df.columns):\n            raise KeyError('passes columns are not ALL present dataframe')\n        if len(Index(cols) & df.columns) != len(cols):\n            raise KeyError(\"Not all names specified in 'columns' are found\")\n        {BUG_LABEL_TOKEN}\n        self.df = df\n        {BUG_LABEL_TOKEN}\n    self.columns = self.df.columns\n    self.float_format = float_format\n    self.index = index\n    self.index_label = index_label\n    self.header = header\n    self.merge_cells = merge_cells\n    self.inf_rep = inf_rep"
        return buggy_code, "        "
    elif bug_id == '39':
        buggy_code = f"def _try_convert_data(self, name, data, use_dtypes=True, convert_dates=True):\n    \"\"\"\n        Try to parse a ndarray like into a column by inferring dtype.\n        \"\"\"\n    if use_dtypes:\n        if not self.dtype:\n            return (data, False)\n        elif self.dtype is True:\n            pass\n        else:\n            dtype = self.dtype.get(name) if isinstance(self.dtype, dict) else self.dtype\n            if dtype is not None:\n                try:\n                    dtype = np.dtype(dtype)\n                    return (data.astype(dtype), True)\n                except (TypeError, ValueError):\n                    return (data, False)\n    if convert_dates:\n        new_data, result = self._try_convert_to_date(data)\n        if result:\n            return (new_data, True)\n    result = False\n    if data.dtype == 'object':\n        try:\n            data = data.astype('float64')\n            result = True\n        except (TypeError, ValueError):\n            pass\n    if data.dtype.kind == 'f':\n        if data.dtype != 'float64':\n            try:\n                data = data.astype('float64')\n                result = True\n            except (TypeError, ValueError):\n                pass\n    if len(data) and (data.dtype == 'float' or data.dtype == 'object'):\n        try:\n            new_data = data.astype('int64')\n            if (new_data == data).all():\n                data = new_data\n                result = True\n        {BUG_LABEL_TOKEN}\n        except (TypeError, ValueError):\n        {BUG_LABEL_TOKEN}\n            pass\n    if data.dtype == 'int':\n        try:\n            data = data.astype('int64')\n            result = True\n        except (TypeError, ValueError):\n            pass\n    return (data, result)"
        return buggy_code, "        "
    elif bug_id == '54':
        buggy_code = f"def initialize(self, make_current=None):\n    if make_current is None:\n        if IOLoop.current(instance=False) is None:\n            self.make_current()\n    elif make_current:\n        {BUG_LABEL_TOKEN}\n        if IOLoop.current(instance=False) is None:\n        {BUG_LABEL_TOKEN}\n            raise RuntimeError('current IOLoop already exists')\n        self.make_current()"
        return buggy_code, "        "
    # rewrite the buggy code format
    elif bug_id == '67':
        buggy_code = f"def __len__(self):\n    return self.total if self.iterable is None else         (self.iterable.shape[0] if hasattr(self.iterable, \"shape\")\n         else len(self.iterable) if hasattr(self.iterable, \"__len__\")\n        {BUG_LABEL_TOKEN}\n        else self.total)\n        {BUG_LABEL_TOKEN}"
        return buggy_code, "        "
    else:
        labeled_code, buggy_code_indent = label_code(buggy_code, buggy_line_content)
        return labeled_code, buggy_code_indent


def mask_code_manually_bugsinpy(buggy_code: str, buggy_line_content: str, bug_id: str):
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
        masked_code = "def __len__(self):\n    return self.total if self.iterable is None else         (self.iterable.shape[0] if hasattr(self.iterable, \"shape\")\n         else len(self.iterable) if hasattr(self.iterable, \"__len__\")\n<FILL_ME>"

    else:
        masked_code = mask_code(buggy_code, buggy_line_content)
    return masked_code


def label_code_manually_defects4j(buggy_code: str, buggy_line_content: str, bug_id: str):
    if bug_id == '3':
        buggy_code = "public TimeSeries createCopy(RegularTimePeriod start, RegularTimePeriod end)\n    throws CloneNotSupportedException {\n\n    if (start == null) {\n        throw new IllegalArgumentException(\"Null 'start' argument.\");\n    }\n    if (end == null) {\n        throw new IllegalArgumentException(\"Null 'end' argument.\");\n    }\n    if (start.compareTo(end) > 0) {\n        throw new IllegalArgumentException(\n                \"Requires start on or before end.\");\n    }\n    boolean emptyRange = false;\n    int startIndex = getIndex(start);\n    if (startIndex < 0) {\n        startIndex = -(startIndex + 1);\n        if (startIndex == this.data.size()) {\n            emptyRange = true;  // start is after last data item\n        }\n    }\n    int endIndex = getIndex(end);\n    if (endIndex < 0) {             // end period is not in original series\n        endIndex = -(endIndex + 1); // this is first item AFTER end period\n        endIndex = endIndex - 1;    // so this is last item BEFORE end\n    }\n    #<BUGGY_LINE>\n    if (endIndex < 0) {\n    #<BUGGY_LINE>\n        emptyRange = true;\n    }\n    if (emptyRange) {\n        TimeSeries copy = (TimeSeries) super.clone();\n        copy.data = new java.util.ArrayList();\n        return copy;\n    }\n    else {\n        return createCopy(startIndex, endIndex);\n    }\n\n}"
        return buggy_code, "    "
    elif bug_id == '16':
        buggy_code = "Node parseInputs() {\n  boolean devMode = options.devMode != DevMode.OFF;\n\n  // If old roots exist (we are parsing a second time), detach each of the\n  // individual file parse trees.\n  if (externsRoot != null) {\n    externsRoot.detachChildren();\n  }\n  if (jsRoot != null) {\n    jsRoot.detachChildren();\n  }\n\n  // Parse main JS sources.\n  jsRoot = IR.block();\n  jsRoot.setIsSyntheticBlock(true);\n\n  externsRoot = IR.block();\n  externsRoot.setIsSyntheticBlock(true);\n\n  externAndJsRoot = IR.block(externsRoot, jsRoot);\n  externAndJsRoot.setIsSyntheticBlock(true);\n\n  if (options.tracer.isOn()) {\n    tracker = new PerformanceTracker(jsRoot, options.tracer);\n    addChangeHandler(tracker.getCodeChangeHandler());\n  }\n\n  Tracer tracer = newTracer(\"parseInputs\");\n\n  try {\n    // Parse externs sources.\n    for (CompilerInput input : externs) {\n      Node n = input.getAstRoot(this);\n      if (hasErrors()) {\n        return null;\n      }\n      externsRoot.addChildToBack(n);\n    }\n\n    // Modules inferred in ProcessCommonJS pass.\n    if (options.transformAMDToCJSModules || options.processCommonJSModules) {\n      processAMDAndCommonJSModules();\n    }\n\n    hoistExterns(externsRoot);\n\n    // Check if the sources need to be re-ordered.\n    boolean staleInputs = false;\n    #<BUGGY_LINE>\n    if (options.dependencyOptions.needsManagement() && options.closurePass) {\n    #<BUGGY_LINE>\n      for (CompilerInput input : inputs) {\n        // Forward-declare all the provided types, so that they\n        // are not flagged even if they are dropped from the process.\n        for (String provide : input.getProvides()) {\n          getTypeRegistry().forwardDeclareType(provide);\n        }\n      }\n\n      try {\n        inputs =\n            (moduleGraph == null ? new JSModuleGraph(modules) : moduleGraph)\n            .manageDependencies(options.dependencyOptions, inputs);\n        staleInputs = true;\n      } catch (CircularDependencyException e) {\n        report(JSError.make(\n            JSModule.CIRCULAR_DEPENDENCY_ERROR, e.getMessage()));\n\n        // If in IDE mode, we ignore the error and keep going.\n        if (hasErrors()) {\n          return null;\n        }\n      } catch (MissingProvideException e) {\n        report(JSError.make(\n            MISSING_ENTRY_ERROR, e.getMessage()));\n\n        // If in IDE mode, we ignore the error and keep going.\n        if (hasErrors()) {\n          return null;\n        }\n      }\n    }\n\n    hoistNoCompileFiles();\n\n    if (staleInputs) {\n      repartitionInputs();\n    }\n\n    // Build the AST.\n    for (CompilerInput input : inputs) {\n      Node n = input.getAstRoot(this);\n      if (n == null) {\n        continue;\n      }\n\n      if (devMode) {\n        runSanityCheck();\n        if (hasErrors()) {\n          return null;\n        }\n      }\n\n      if (options.sourceMapOutputPath != null ||\n          options.nameReferenceReportPath != null) {\n\n        // Annotate the nodes in the tree with information from the\n        // input file. This information is used to construct the SourceMap.\n        SourceInformationAnnotator sia =\n            new SourceInformationAnnotator(\n                input.getName(), options.devMode != DevMode.OFF);\n        NodeTraversal.traverse(this, n, sia);\n      }\n\n      jsRoot.addChildToBack(n);\n    }\n\n    if (hasErrors()) {\n      return null;\n    }\n    return externAndJsRoot;\n  } finally {\n    stopTracer(tracer, \"parseInputs\");\n  }\n}"
        return buggy_code, "    "
    elif bug_id == '21':
        buggy_code = "private boolean isPrototypePropertyAssign(Node assign) {\n  Node n = assign.getFirstChild();\n  if (n != null && NodeUtil.isVarOrSimpleAssignLhs(n, assign) &&\n    n.getType() == Token.GETPROP\n  #<BUGGY_LINE>\n  ) {\n  #<BUGGY_LINE>\n    // We want to exclude the assignment itself from the usage list\n    boolean isChainedProperty =\n      n.getFirstChild().getType() == Token.GETPROP;\n\n    if (isChainedProperty) {\n      Node child = n.getFirstChild().getFirstChild().getNext();\n\n      if (child.getType() == Token.STRING &&\n        child.getString().equals(\"prototype\")) {\n        return true;\n      }\n    }\n  }\n\n  return false;\n}"
        return buggy_code, "  "
    elif bug_id == '25':
        buggy_code = "static boolean evaluatesToLocalValue(Node value, Predicate<Node> locals) {\n  switch (value.getType()) {\n    case Token.ASSIGN:\n      // A result that is aliased by a non-local name, is the effectively the\n      // same as returning a non-local name, but this doesn't matter if the\n      // value is immutable.\n      return NodeUtil.isImmutableValue(value.getLastChild())\n          || (locals.apply(value)\n              && evaluatesToLocalValue(value.getLastChild(), locals));\n    case Token.COMMA:\n      return evaluatesToLocalValue(value.getLastChild(), locals);\n    case Token.AND:\n    case Token.OR:\n      return evaluatesToLocalValue(value.getFirstChild(), locals)\n         && evaluatesToLocalValue(value.getLastChild(), locals);\n    case Token.HOOK:\n      return evaluatesToLocalValue(value.getFirstChild().getNext(), locals)\n         && evaluatesToLocalValue(value.getLastChild(), locals);\n    case Token.INC:\n    case Token.DEC:\n      if (value.getBooleanProp(Node.INCRDECR_PROP)) {\n        return evaluatesToLocalValue(value.getFirstChild(), locals);\n      } else {\n        return true;\n      }\n    case Token.THIS:\n      return locals.apply(value);\n    case Token.NAME:\n      return isImmutableValue(value) || locals.apply(value);\n    case Token.GETELEM:\n    case Token.GETPROP:\n      // There is no information about the locality of object properties.\n      return locals.apply(value);\n    case Token.CALL:\n      return callHasLocalResult(value)\n          || isToStringMethodCall(value)\n          || locals.apply(value);\n    case Token.NEW:\n      #<BUGGY_LINE>\n      return true;\n      #<BUGGY_LINE>\n    case Token.FUNCTION:\n    case Token.REGEXP:\n    case Token.ARRAYLIT:\n    case Token.OBJECTLIT:\n      // Literals objects with non-literal children are allowed.\n      return true;\n    case Token.IN:\n      // TODO(johnlenz): should IN operator be included in #isSimpleOperator?\n      return true;\n    default:\n      // Other op force a local value:\n      //  x = '' + g (x is now an local string)\n      //  x -= g (x is now an local number)\n      if (isAssignmentOp(value)\n          || isSimpleOperator(value)\n          || isImmutableValue(value)) {\n        return true;\n      }\n\n      throw new IllegalStateException(\n          \"Unexpected expression node\" + value +\n          \"\\n parent:\" + value.getParent());\n  }\n}"
        return buggy_code, "      "
    elif bug_id == '29':
        buggy_code = "private void recordAssignment(NodeTraversal t, Node n, Node recordNode) {\n  Node nameNode = n.getFirstChild();\n  Node parent = n.getParent();\n  NameInformation ns = createNameInformation(t, nameNode);\n  if (ns != null) {\n    if (parent.isFor() && !NodeUtil.isForIn(parent)) {\n      // Patch for assignments that appear in the init,\n      // condition or iteration part of a FOR loop.  Without\n      // this change, all 3 of those parts try to claim the for\n      // loop as their dependency scope.  The last assignment in\n      // those three fields wins, which can result in incorrect\n      // reference edges between referenced and assigned variables.\n      //\n      // TODO(user) revisit the dependency scope calculation\n      // logic.\n      if (parent.getFirstChild().getNext() != n) {\n        recordDepScope(recordNode, ns);\n      } else {\n        recordDepScope(nameNode, ns);\n      }\n    #<BUGGY_LINE>\n    } else {\n    #<BUGGY_LINE>\n      recordDepScope(recordNode, ns);\n    }\n  }\n}"
        return buggy_code, "    "
    elif bug_id == '61':
        buggy_code = "public <T> MappingIterator<T> readValues(byte[] src, int offset, int length)\n    throws IOException, JsonProcessingException\n{\n    if (_dataFormatReaders != null) {\n        return _detectBindAndReadValues(_dataFormatReaders.findFormat(src, offset, length), false);\n    }\n    #<BUGGY_LINE>\n    return _bindAndReadValues(_considerFilter(_parserFactory.createParser(src), true));\n    #<BUGGY_LINE>\n}"
        return buggy_code, "    "
    elif bug_id == '73':
        buggy_code = "static void escape(StringBuilder accum, String string, Document.OutputSettings out,\n                   boolean inAttribute, boolean normaliseWhite, boolean stripLeadingWhite) {\n\n    boolean lastWasWhite = false;\n    boolean reachedNonWhite = false;\n    final EscapeMode escapeMode = out.escapeMode();\n    final CharsetEncoder encoder = out.encoder();\n    final CoreCharset coreCharset = CoreCharset.byName(encoder.charset().name());\n    final Map<Character, String> map = escapeMode.getMap();\n    final int length = string.length();\n\n    int codePoint;\n    for (int offset = 0; offset < length; offset += Character.charCount(codePoint)) {\n        codePoint = string.codePointAt(offset);\n\n        if (normaliseWhite) {\n            if (StringUtil.isWhitespace(codePoint)) {\n                if ((stripLeadingWhite && !reachedNonWhite) || lastWasWhite)\n                    continue;\n                accum.append(' ');\n                lastWasWhite = true;\n                continue;\n            } else {\n                lastWasWhite = false;\n                reachedNonWhite = true;\n            }\n        }\n        // surrogate pairs, split implementation for efficiency on single char common case (saves creating strings, char[]):\n        if (codePoint < Character.MIN_SUPPLEMENTARY_CODE_POINT) {\n            final char c = (char) codePoint;\n            // html specific and required escapes:\n            switch (c) {\n                case '&':\n                    accum.append(\"&amp;\");\n                    break;\n                case 0xA0:\n                    if (escapeMode != EscapeMode.xhtml)\n                        accum.append(\"&nbsp;\");\n                    else\n                        #<BUGGY_LINE>\n                        accum.append(c);\n                        #<BUGGY_LINE>\n                    break;\n                case '<':\n                    if (!inAttribute)\n                        accum.append(\"&lt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '>':\n                    if (!inAttribute)\n                        accum.append(\"&gt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '\"':\n                    if (inAttribute)\n                        accum.append(\"&quot;\");\n                    else\n                        accum.append(c);\n                    break;\n                default:\n                    if (canEncode(coreCharset, c, encoder))\n                        accum.append(c);\n                    else if (map.containsKey(c))\n                        accum.append('&').append(map.get(c)).append(';');\n                    else\n                        accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n            }\n        } else {\n            final String c = new String(Character.toChars(codePoint));\n            if (encoder.canEncode(c)) // uses fallback encoder for simplicity\n                accum.append(c);\n            else\n                accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n        }\n    }\n}"
        return buggy_code, "                        "
    elif bug_id == '74':
        buggy_code = "static void escape(StringBuilder accum, String string, Document.OutputSettings out,\n                   boolean inAttribute, boolean normaliseWhite, boolean stripLeadingWhite) {\n\n    boolean lastWasWhite = false;\n    boolean reachedNonWhite = false;\n    final EscapeMode escapeMode = out.escapeMode();\n    final CharsetEncoder encoder = out.encoder();\n    final CoreCharset coreCharset = CoreCharset.byName(encoder.charset().name());\n    final Map<Character, String> map = escapeMode.getMap();\n    final int length = string.length();\n\n    int codePoint;\n    for (int offset = 0; offset < length; offset += Character.charCount(codePoint)) {\n        codePoint = string.codePointAt(offset);\n\n        if (normaliseWhite) {\n            if (StringUtil.isWhitespace(codePoint)) {\n                if ((stripLeadingWhite && !reachedNonWhite) || lastWasWhite)\n                    continue;\n                accum.append(' ');\n                lastWasWhite = true;\n                continue;\n            } else {\n                lastWasWhite = false;\n                reachedNonWhite = true;\n            }\n        }\n        // surrogate pairs, split implementation for efficiency on single char common case (saves creating strings, char[]):\n        if (codePoint < Character.MIN_SUPPLEMENTARY_CODE_POINT) {\n            final char c = (char) codePoint;\n            // html specific and required escapes:\n            switch (c) {\n                case '&':\n                    accum.append(\"&amp;\");\n                    break;\n                case 0xA0:\n                    if (escapeMode != EscapeMode.xhtml)\n                        accum.append(\"&nbsp;\");\n                    else\n                        accum.append(\"&#xa0;\");\n                    break;\n                case '<':\n                    #<BUGGY_LINE>\n                    if (!inAttribute)\n                    #<BUGGY_LINE>\n                        accum.append(\"&lt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '>':\n                    if (!inAttribute)\n                        accum.append(\"&gt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '\"':\n                    if (inAttribute)\n                        accum.append(\"&quot;\");\n                    else\n                        accum.append(c);\n                    break;\n                default:\n                    if (canEncode(coreCharset, c, encoder))\n                        accum.append(c);\n                    else if (map.containsKey(c))\n                        accum.append('&').append(map.get(c)).append(';');\n                    else\n                        accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n            }\n        } else {\n            final String c = new String(Character.toChars(codePoint));\n            if (encoder.canEncode(c)) // uses fallback encoder for simplicity\n                accum.append(c);\n            else\n                accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n        }\n    }\n}"
        return buggy_code, "                    "
    elif bug_id == '82':
        buggy_code = "public final Object computeValue(EvalContext context) {\n    #<BUGGY_LINE>\n    return compute(args[0].computeValue(context), args[1].computeValue(context)) ? Boolean.TRUE : Boolean.FALSE;\n    #<BUGGY_LINE>\n}"
        return buggy_code, "    "
    elif bug_id == '91':
        buggy_code = "public StrBuilder appendFixedWidthPadRight(Object obj, int width, char padChar) {\n    if (width > 0) {\n        ensureCapacity(size + width);\n        String str = (obj == null ? getNullText() : obj.toString());\n        int strLen = str.length();\n        if (strLen >= width) {\n            #<BUGGY_LINE>\n            str.getChars(0, strLen, buffer, size);\n            #<BUGGY_LINE>\n        } else {\n            int padLen = width - strLen;\n            str.getChars(0, strLen, buffer, size);\n            for (int i = 0; i < padLen; i++) {\n                buffer[size + strLen + i] = padChar;\n            }\n        }\n        size += width;\n    }\n    return this;\n}"
        return buggy_code, "            "
    elif bug_id == '93':
        buggy_code = "public Complex reciprocal() {\n    if (isNaN) {\n        return NaN;\n    }\n\n    if (real == 0.0 && imaginary == 0.0) {\n        #<BUGGY_LINE>\n        return NaN;\n        #<BUGGY_LINE>\n    }\n\n    if (isInfinite) {\n        return ZERO;\n    }\n\n    if (FastMath.abs(real) < FastMath.abs(imaginary)) {\n        double q = real / imaginary;\n        double scale = 1. / (real * q + imaginary);\n        return createComplex(scale * q, -scale);\n    } else {\n        double q = imaginary / real;\n        double scale = 1. / (imaginary * q + real);\n        return createComplex(scale, -scale * q);\n    }\n}"
        return buggy_code, "        "
    elif bug_id == '110':
        buggy_code = "public boolean equals(Object other) {\n    boolean ret;\n\n    if (this == other) {\n        ret = true;\n    } else if (other == null) {\n        ret = false;\n    } else {\n        try {\n            Complex rhs = (Complex) other;\n            if (rhs.isNaN()) {\n                ret = this.isNaN();\n            } else {\n                #<BUGGY_LINE>\n                ret = (Double.doubleToRawLongBits(real) == Double.doubleToRawLongBits(rhs.getReal())) && (Double.doubleToRawLongBits(imaginary) == Double.doubleToRawLongBits(rhs.getImaginary()));\n                #<BUGGY_LINE>\n            }\n        } catch (ClassCastException ex) {\n            // ignore exception\n            ret = false;\n        }\n    }\n\n    return ret;\n}"
        return buggy_code, "                "
    else:
        labeled_code, buggy_code_indent = label_code(buggy_code, buggy_line_content)
        return labeled_code, buggy_code_indent


def mask_code_manually_defects4j(buggy_code: str, buggy_line_content: str, bug_id: str):
    if bug_id == '3':
        masked_code = "public TimeSeries createCopy(RegularTimePeriod start, RegularTimePeriod end)\n    throws CloneNotSupportedException {\n\n    if (start == null) {\n        throw new IllegalArgumentException(\"Null 'start' argument.\");\n    }\n    if (end == null) {\n        throw new IllegalArgumentException(\"Null 'end' argument.\");\n    }\n    if (start.compareTo(end) > 0) {\n        throw new IllegalArgumentException(\n                \"Requires start on or before end.\");\n    }\n    boolean emptyRange = false;\n    int startIndex = getIndex(start);\n    if (startIndex < 0) {\n        startIndex = -(startIndex + 1);\n        if (startIndex == this.data.size()) {\n            emptyRange = true;  // start is after last data item\n        }\n    }\n    int endIndex = getIndex(end);\n    if (endIndex < 0) {             // end period is not in original series\n        endIndex = -(endIndex + 1); // this is first item AFTER end period\n        endIndex = endIndex - 1;    // so this is last item BEFORE end\n    }\n<FILL_ME>\n        emptyRange = true;\n    }\n    if (emptyRange) {\n        TimeSeries copy = (TimeSeries) super.clone();\n        copy.data = new java.util.ArrayList();\n        return copy;\n    }\n    else {\n        return createCopy(startIndex, endIndex);\n    }\n\n}"
    elif bug_id == '16':
        masked_code = "Node parseInputs() {\n  boolean devMode = options.devMode != DevMode.OFF;\n\n  // If old roots exist (we are parsing a second time), detach each of the\n  // individual file parse trees.\n  if (externsRoot != null) {\n    externsRoot.detachChildren();\n  }\n  if (jsRoot != null) {\n    jsRoot.detachChildren();\n  }\n\n  // Parse main JS sources.\n  jsRoot = IR.block();\n  jsRoot.setIsSyntheticBlock(true);\n\n  externsRoot = IR.block();\n  externsRoot.setIsSyntheticBlock(true);\n\n  externAndJsRoot = IR.block(externsRoot, jsRoot);\n  externAndJsRoot.setIsSyntheticBlock(true);\n\n  if (options.tracer.isOn()) {\n    tracker = new PerformanceTracker(jsRoot, options.tracer);\n    addChangeHandler(tracker.getCodeChangeHandler());\n  }\n\n  Tracer tracer = newTracer(\"parseInputs\");\n\n  try {\n    // Parse externs sources.\n    for (CompilerInput input : externs) {\n      Node n = input.getAstRoot(this);\n      if (hasErrors()) {\n        return null;\n      }\n      externsRoot.addChildToBack(n);\n    }\n\n    // Modules inferred in ProcessCommonJS pass.\n    if (options.transformAMDToCJSModules || options.processCommonJSModules) {\n      processAMDAndCommonJSModules();\n    }\n\n    hoistExterns(externsRoot);\n\n    // Check if the sources need to be re-ordered.\n    boolean staleInputs = false;\n<FILL_ME>\n      for (CompilerInput input : inputs) {\n        // Forward-declare all the provided types, so that they\n        // are not flagged even if they are dropped from the process.\n        for (String provide : input.getProvides()) {\n          getTypeRegistry().forwardDeclareType(provide);\n        }\n      }\n\n      try {\n        inputs =\n            (moduleGraph == null ? new JSModuleGraph(modules) : moduleGraph)\n            .manageDependencies(options.dependencyOptions, inputs);\n        staleInputs = true;\n      } catch (CircularDependencyException e) {\n        report(JSError.make(\n            JSModule.CIRCULAR_DEPENDENCY_ERROR, e.getMessage()));\n\n        // If in IDE mode, we ignore the error and keep going.\n        if (hasErrors()) {\n          return null;\n        }\n      } catch (MissingProvideException e) {\n        report(JSError.make(\n            MISSING_ENTRY_ERROR, e.getMessage()));\n\n        // If in IDE mode, we ignore the error and keep going.\n        if (hasErrors()) {\n          return null;\n        }\n      }\n    }\n\n    hoistNoCompileFiles();\n\n    if (staleInputs) {\n      repartitionInputs();\n    }\n\n    // Build the AST.\n    for (CompilerInput input : inputs) {\n      Node n = input.getAstRoot(this);\n      if (n == null) {\n        continue;\n      }\n\n      if (devMode) {\n        runSanityCheck();\n        if (hasErrors()) {\n          return null;\n        }\n      }\n\n      if (options.sourceMapOutputPath != null ||\n          options.nameReferenceReportPath != null) {\n\n        // Annotate the nodes in the tree with information from the\n        // input file. This information is used to construct the SourceMap.\n        SourceInformationAnnotator sia =\n            new SourceInformationAnnotator(\n                input.getName(), options.devMode != DevMode.OFF);\n        NodeTraversal.traverse(this, n, sia);\n      }\n\n      jsRoot.addChildToBack(n);\n    }\n\n    if (hasErrors()) {\n      return null;\n    }\n    return externAndJsRoot;\n  } finally {\n    stopTracer(tracer, \"parseInputs\");\n  }\n}"
    elif bug_id == '21':
        masked_code = "private boolean isPrototypePropertyAssign(Node assign) {\n  Node n = assign.getFirstChild();\n  if (n != null && NodeUtil.isVarOrSimpleAssignLhs(n, assign) &&\n    n.getType() == Token.GETPROP\n<FILL_ME>\n    // We want to exclude the assignment itself from the usage list\n    boolean isChainedProperty =\n      n.getFirstChild().getType() == Token.GETPROP;\n\n    if (isChainedProperty) {\n      Node child = n.getFirstChild().getFirstChild().getNext();\n\n      if (child.getType() == Token.STRING &&\n        child.getString().equals(\"prototype\")) {\n        return true;\n      }\n    }\n  }\n\n  return false;\n}"
    elif bug_id == '25':
        masked_code = "static boolean evaluatesToLocalValue(Node value, Predicate<Node> locals) {\n  switch (value.getType()) {\n    case Token.ASSIGN:\n      // A result that is aliased by a non-local name, is the effectively the\n      // same as returning a non-local name, but this doesn't matter if the\n      // value is immutable.\n      return NodeUtil.isImmutableValue(value.getLastChild())\n          || (locals.apply(value)\n              && evaluatesToLocalValue(value.getLastChild(), locals));\n    case Token.COMMA:\n      return evaluatesToLocalValue(value.getLastChild(), locals);\n    case Token.AND:\n    case Token.OR:\n      return evaluatesToLocalValue(value.getFirstChild(), locals)\n         && evaluatesToLocalValue(value.getLastChild(), locals);\n    case Token.HOOK:\n      return evaluatesToLocalValue(value.getFirstChild().getNext(), locals)\n         && evaluatesToLocalValue(value.getLastChild(), locals);\n    case Token.INC:\n    case Token.DEC:\n      if (value.getBooleanProp(Node.INCRDECR_PROP)) {\n        return evaluatesToLocalValue(value.getFirstChild(), locals);\n      } else {\n        return true;\n      }\n    case Token.THIS:\n      return locals.apply(value);\n    case Token.NAME:\n      return isImmutableValue(value) || locals.apply(value);\n    case Token.GETELEM:\n    case Token.GETPROP:\n      // There is no information about the locality of object properties.\n      return locals.apply(value);\n    case Token.CALL:\n      return callHasLocalResult(value)\n          || isToStringMethodCall(value)\n          || locals.apply(value);\n    case Token.NEW:\n<FILL_ME>\n    case Token.FUNCTION:\n    case Token.REGEXP:\n    case Token.ARRAYLIT:\n    case Token.OBJECTLIT:\n      // Literals objects with non-literal children are allowed.\n      return true;\n    case Token.IN:\n      // TODO(johnlenz): should IN operator be included in #isSimpleOperator?\n      return true;\n    default:\n      // Other op force a local value:\n      //  x = '' + g (x is now an local string)\n      //  x -= g (x is now an local number)\n      if (isAssignmentOp(value)\n          || isSimpleOperator(value)\n          || isImmutableValue(value)) {\n        return true;\n      }\n\n      throw new IllegalStateException(\n          \"Unexpected expression node\" + value +\n          \"\\n parent:\" + value.getParent());\n  }\n}"
    elif bug_id == '29':
        masked_code = "private void recordAssignment(NodeTraversal t, Node n, Node recordNode) {\n  Node nameNode = n.getFirstChild();\n  Node parent = n.getParent();\n  NameInformation ns = createNameInformation(t, nameNode);\n  if (ns != null) {\n    if (parent.isFor() && !NodeUtil.isForIn(parent)) {\n      // Patch for assignments that appear in the init,\n      // condition or iteration part of a FOR loop.  Without\n      // this change, all 3 of those parts try to claim the for\n      // loop as their dependency scope.  The last assignment in\n      // those three fields wins, which can result in incorrect\n      // reference edges between referenced and assigned variables.\n      //\n      // TODO(user) revisit the dependency scope calculation\n      // logic.\n      if (parent.getFirstChild().getNext() != n) {\n        recordDepScope(recordNode, ns);\n      } else {\n        recordDepScope(nameNode, ns);\n      }\n<FILL_ME>\n      recordDepScope(recordNode, ns);\n    }\n  }\n}"
    elif bug_id == '61':
        masked_code = "public <T> MappingIterator<T> readValues(byte[] src, int offset, int length)\n    throws IOException, JsonProcessingException\n{\n    if (_dataFormatReaders != null) {\n        return _detectBindAndReadValues(_dataFormatReaders.findFormat(src, offset, length), false);\n    }\n<FILL_ME>\n}"
    elif bug_id == '73':
        masked_code = "static void escape(StringBuilder accum, String string, Document.OutputSettings out,\n                   boolean inAttribute, boolean normaliseWhite, boolean stripLeadingWhite) {\n\n    boolean lastWasWhite = false;\n    boolean reachedNonWhite = false;\n    final EscapeMode escapeMode = out.escapeMode();\n    final CharsetEncoder encoder = out.encoder();\n    final CoreCharset coreCharset = CoreCharset.byName(encoder.charset().name());\n    final Map<Character, String> map = escapeMode.getMap();\n    final int length = string.length();\n\n    int codePoint;\n    for (int offset = 0; offset < length; offset += Character.charCount(codePoint)) {\n        codePoint = string.codePointAt(offset);\n\n        if (normaliseWhite) {\n            if (StringUtil.isWhitespace(codePoint)) {\n                if ((stripLeadingWhite && !reachedNonWhite) || lastWasWhite)\n                    continue;\n                accum.append(' ');\n                lastWasWhite = true;\n                continue;\n            } else {\n                lastWasWhite = false;\n                reachedNonWhite = true;\n            }\n        }\n        // surrogate pairs, split implementation for efficiency on single char common case (saves creating strings, char[]):\n        if (codePoint < Character.MIN_SUPPLEMENTARY_CODE_POINT) {\n            final char c = (char) codePoint;\n            // html specific and required escapes:\n            switch (c) {\n                case '&':\n                    accum.append(\"&amp;\");\n                    break;\n                case 0xA0:\n                    if (escapeMode != EscapeMode.xhtml)\n                        accum.append(\"&nbsp;\");\n                    else\n<FILL_ME>\n                    break;\n                case '<':\n                    if (!inAttribute)\n                        accum.append(\"&lt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '>':\n                    if (!inAttribute)\n                        accum.append(\"&gt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '\"':\n                    if (inAttribute)\n                        accum.append(\"&quot;\");\n                    else\n                        accum.append(c);\n                    break;\n                default:\n                    if (canEncode(coreCharset, c, encoder))\n                        accum.append(c);\n                    else if (map.containsKey(c))\n                        accum.append('&').append(map.get(c)).append(';');\n                    else\n                        accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n            }\n        } else {\n            final String c = new String(Character.toChars(codePoint));\n            if (encoder.canEncode(c)) // uses fallback encoder for simplicity\n                accum.append(c);\n            else\n                accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n        }\n    }\n}"
    elif bug_id == '74':
        masked_code = "static void escape(StringBuilder accum, String string, Document.OutputSettings out,\n                   boolean inAttribute, boolean normaliseWhite, boolean stripLeadingWhite) {\n\n    boolean lastWasWhite = false;\n    boolean reachedNonWhite = false;\n    final EscapeMode escapeMode = out.escapeMode();\n    final CharsetEncoder encoder = out.encoder();\n    final CoreCharset coreCharset = CoreCharset.byName(encoder.charset().name());\n    final Map<Character, String> map = escapeMode.getMap();\n    final int length = string.length();\n\n    int codePoint;\n    for (int offset = 0; offset < length; offset += Character.charCount(codePoint)) {\n        codePoint = string.codePointAt(offset);\n\n        if (normaliseWhite) {\n            if (StringUtil.isWhitespace(codePoint)) {\n                if ((stripLeadingWhite && !reachedNonWhite) || lastWasWhite)\n                    continue;\n                accum.append(' ');\n                lastWasWhite = true;\n                continue;\n            } else {\n                lastWasWhite = false;\n                reachedNonWhite = true;\n            }\n        }\n        // surrogate pairs, split implementation for efficiency on single char common case (saves creating strings, char[]):\n        if (codePoint < Character.MIN_SUPPLEMENTARY_CODE_POINT) {\n            final char c = (char) codePoint;\n            // html specific and required escapes:\n            switch (c) {\n                case '&':\n                    accum.append(\"&amp;\");\n                    break;\n                case 0xA0:\n                    if (escapeMode != EscapeMode.xhtml)\n                        accum.append(\"&nbsp;\");\n                    else\n                        accum.append(\"&#xa0;\");\n                    break;\n                case '<':\n<FILL_ME>\n                        accum.append(\"&lt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '>':\n                    if (!inAttribute)\n                        accum.append(\"&gt;\");\n                    else\n                        accum.append(c);\n                    break;\n                case '\"':\n                    if (inAttribute)\n                        accum.append(\"&quot;\");\n                    else\n                        accum.append(c);\n                    break;\n                default:\n                    if (canEncode(coreCharset, c, encoder))\n                        accum.append(c);\n                    else if (map.containsKey(c))\n                        accum.append('&').append(map.get(c)).append(';');\n                    else\n                        accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n            }\n        } else {\n            final String c = new String(Character.toChars(codePoint));\n            if (encoder.canEncode(c)) // uses fallback encoder for simplicity\n                accum.append(c);\n            else\n                accum.append(\"&#x\").append(Integer.toHexString(codePoint)).append(';');\n        }\n    }\n}"
    elif bug_id == '82':
        masked_code = "public final Object computeValue(EvalContext context) {\n<FILL_ME>\n}"
    elif bug_id == '91':
        masked_code = "public StrBuilder appendFixedWidthPadRight(Object obj, int width, char padChar) {\n    if (width > 0) {\n        ensureCapacity(size + width);\n        String str = (obj == null ? getNullText() : obj.toString());\n        int strLen = str.length();\n        if (strLen >= width) {\n<FILL_ME>\n        } else {\n            int padLen = width - strLen;\n            str.getChars(0, strLen, buffer, size);\n            for (int i = 0; i < padLen; i++) {\n                buffer[size + strLen + i] = padChar;\n            }\n        }\n        size += width;\n    }\n    return this;\n}"
    elif bug_id == '93':
        masked_code = "public Complex reciprocal() {\n    if (isNaN) {\n        return NaN;\n    }\n\n    if (real == 0.0 && imaginary == 0.0) {\n<FILL_ME>\n    }\n\n    if (isInfinite) {\n        return ZERO;\n    }\n\n    if (FastMath.abs(real) < FastMath.abs(imaginary)) {\n        double q = real / imaginary;\n        double scale = 1. / (real * q + imaginary);\n        return createComplex(scale * q, -scale);\n    } else {\n        double q = imaginary / real;\n        double scale = 1. / (imaginary * q + real);\n        return createComplex(scale, -scale * q);\n    }\n}"
    elif bug_id == '110':
        masked_code = "public boolean equals(Object other) {\n    boolean ret;\n\n    if (this == other) {\n        ret = true;\n    } else if (other == null) {\n        ret = false;\n    } else {\n        try {\n            Complex rhs = (Complex) other;\n            if (rhs.isNaN()) {\n                ret = this.isNaN();\n            } else {\n<FILL_ME>\n            }\n        } catch (ClassCastException ex) {\n            // ignore exception\n            ret = false;\n        }\n    }\n\n    return ret;\n}"
    else:
        masked_code = mask_code(buggy_code, buggy_line_content)
    return masked_code


def label_code(buggy_code: str, buggy_line_content: str):
    buggy_line_content_strip = buggy_line_content.strip(" ")
    buggy_code_split = buggy_code.split(buggy_line_content_strip)
    assert len(buggy_code_split) == 2
    buggy_code_indent = buggy_code_split[0][len(buggy_code_split[0].strip(" ")):]
    labeled_code = (buggy_code_split[0] + f"{BUG_LABEL_TOKEN}\n" + buggy_code_indent + buggy_line_content_strip + "\n" +
                    buggy_code_indent + f"{BUG_LABEL_TOKEN}" + buggy_code_split[1])
    return labeled_code, buggy_code_indent


def mask_code(buggy_code: str, buggy_line_content: str):
    buggy_line_content_strip = buggy_line_content.strip(" ")
    masked_code = buggy_code.split(buggy_line_content_strip)[0].strip(" ") + BUG_MASK_TOKEN + \
                  buggy_code.split(buggy_line_content_strip)[1]
    return masked_code
