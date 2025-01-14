def parse_output_codellama_34b_instruct(model_output: str):
    case1 = "```python\n"
    start_expected = "```\n"
    # if the case1 is not found, it will return the original string
    model_output = model_output.replace(case1, start_expected)
    mid = "\n```"
    result = ''.join(model_output.split(start_expected)[1].split(mid)[0])
    while result.endswith("\n"):
        result = result.removesuffix("\n")
    # also found it sometimes output such symbol
    # 7: The fix
    result = result.split('# The', 1)[0]
    return result


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


def parse_output_infill(model_output: str):
    return model_output.splitlines()[0]
