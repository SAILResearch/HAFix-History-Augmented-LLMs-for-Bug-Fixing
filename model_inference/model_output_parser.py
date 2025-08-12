def parse_output_deepseek_coder(model_output: str, language: str):
    try:
        case1 = f"```{language.lower()}\r\n" if model_output.startswith(f"```{language.lower()}\r\n") else f"```{language.lower()}\n"
        start_expected = "```\n"
        # if the case1 is not found, it will return the original string
        model_output_temp = model_output.replace(case1, start_expected)
        mid = "\n```"
        result = ''.join(model_output_temp.split(start_expected)[1].split(mid)[0])
        while result.endswith("\n"):
            result = result.removesuffix("\n")
        # also found it sometimes output such symbol
        # 7: The fix
        result = result.split('# The', 1)[0]
    except:
        result = extract_first_function_block(model_output)
    return result


def parse_output_codellama_instruct(model_output: str, language: str):
    try:
        case1 = f"```{language.lower()}\r\n" if model_output.startswith(f"```{language.lower()}\r\n") else f"```{language.lower()}\n"
        start_expected = "```\n"
        # if the case1 is not found, it will return the original string
        model_output_temp = model_output.replace(case1, start_expected)
        mid = "\n```"
        result = ''.join(model_output_temp.split(start_expected)[1].split(mid)[0])
        while result.endswith("\n"):
            result = result.removesuffix("\n")
        # also found it sometimes output such symbol
        # 7: The fix
        result = result.split('# The', 1)[0]
    except:
        result = extract_first_function_block(model_output)
    return result


def extract_first_function_block(model_output: str) -> str:
    lines = model_output.splitlines()
    func_lines = []
    in_function = False
    base_indent = None

    for i, line in enumerate(lines):
        # Start of function
        if line.strip().startswith("def ") and not in_function:
            in_function = True
            base_indent = len(line) - len(line.lstrip())
            func_lines.append(line)
            continue

        if in_function:
            # Allow docstring, code, or blank lines with proper indent
            if line.strip() == "":
                func_lines.append(line)
            else:
                current_indent = len(line) - len(line.lstrip())
                if current_indent > base_indent:
                    func_lines.append(line)
                else:
                    break  # end of function block

    return "\n".join(func_lines)


def parse_output_codellama_34b_python(model_output: str):
    if model_output.startswith("def") or model_output.startswith("@"):
        # based on observation found these 2 words
        result = model_output.split('# The', 1)[0]
        result = result.split('# Explanation', 1)[0]
        return result
    else:
        return ""


def parse_output_codellama_70b_instruct(model_output: str):
    case1 = "```python\n"
    start_expected = "```\n"
    # if the case1 is not found, it will return the original string
    model_output = model_output.replace(case1, start_expected)
    mid = "\n```"
    result = ''.join(model_output.split(start_expected)[1].split(mid)[0])
    while result.endswith("\n"):
        result = result.removesuffix("\n")
    # 59: The commit
    result = result.split('# The', 1)[0]
    return result


def parse_output_codellama_70b_python(model_output: str):
    if model_output.startswith("def") or model_output.startswith("@"):
        # based on observation found these 2 words
        result = model_output.split('# The', 1)[0]
        result = result.split('# Explanation', 1)[0]
        result = result.split('# Please', 1)[0]
        return result
    else:
        return ""


def parse_output_infill(model_output: str, language: str):
    if model_output.startswith(f" ```{language.lower()}") or model_output.startswith(f"```{language.lower()}"):
        return model_output.splitlines()[1]
    else:
        return model_output.splitlines()[0]
