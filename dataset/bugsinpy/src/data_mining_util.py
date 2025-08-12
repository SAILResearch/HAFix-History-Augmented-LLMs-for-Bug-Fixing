import ast
import logging
from collections import OrderedDict
from code_diff.diff_utils import parse_hunks
from git import GitCommandError
from pydriller import Git, ModifiedFile, ModificationType
from pydriller.domain.commit import Method
from pydriller.domain.commit import Commit
from typing import Optional

logger = logging.getLogger(__name__)


def get_blame_line_commits(git_repo: Git, commit: Commit, modified_file: ModifiedFile, start_line, end_line,
                           hashes_to_ignore_path: Optional[str] = None) -> dict:
    blame_line_commits = {}
    path = modified_file.new_path
    if modified_file.change_type == ModificationType.RENAME or modified_file.change_type == ModificationType.DELETE:
        path = modified_file.old_path

    assert path is not None, "We could not find the path to the file"

    try:
        blames = _get_blame(git_repo.repo, commit.hash, path, start_line, end_line, hashes_to_ignore_path)
        for i, blame_line in enumerate(blames):
            # '^cb2d96ddfaae3056804e0052bf53807ffc822d3  1) # Copyright 2019 Ram Rachum.'
            line_index = int(start_line) + i
            commit_id = blame_line.split(' ')[0].replace('^', '')
            line_code = ''.join(list(blame_line)[blame_line.find(') ') + 2:])
            blame_line_commits[line_index] = {
                'commit_id': commit_id,
                'line_code': line_code
            }
        # update commit datetime and valid the code
        for line_num, commit_and_code in blame_line_commits.items():
            line_commit = git_repo.get_commit(commit_and_code['commit_id'])
            commit_and_code['commit_date'] = line_commit.committer_date.strftime("%Y-%m-%d %H:%M:%S")
            commit_and_code['valid'] = 0 if _is_useless_line(commit_and_code['line_code']) else 1

    except GitCommandError:
        logger.debug(
            f"Could not found file {modified_file.filename} in commit {commit.hash}. Probably a double rename!")
    return blame_line_commits


def _get_blame(repo, commit_hash: str, path: str, start_line, end_line, hashes_to_ignore_path: Optional[str] = None):
    # 20-38, 21-44 , '-L 20,38'
    # -l: Show long rev
    # -s: Suppress the author name and timestamp from the output
    # -w: Ignore whitespace when comparing the parent’s version and the child’s to find where the lines came from.
    args = ['-w', '-l', '-s', f'-L {start_line},{end_line}', commit_hash + '^']
    if hashes_to_ignore_path is not None:
        if repo.git.version_info >= (2, 23):
            args += ["--ignore-revs-file", hashes_to_ignore_path]
        else:
            logger.info("'--ignore-revs-file' is only available from git v2.23")
    return repo.git.blame(*args, '--', path).split('\n')


def _is_useless_line(line: str):
    # this covers comments in Java and Python, as well as empty lines.
    # More have to be added!
    return not line or not line.strip() or \
        line.startswith('//') or \
        line.startswith('#') or \
        line.startswith("/*") or \
        line.startswith("'''") or \
        line.startswith('"""') or \
        line.startswith("*")


def get_accurate_function_code(file_name: str, file_source_code: str, function_name: str, function_start, function_end):
    function_code_str = ""
    function_parent = ""
    try:
        ast_file = ast.parse(file_source_code)
    except:
        return function_parent, function_code_str

    for node in ast.walk(ast_file):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    for node in ast.walk(ast_file):
        if (isinstance(node, ast.FunctionDef)
                and node.name == function_name
                and node.lineno == function_start
                and node.end_lineno == function_end):
            if isinstance(node.parent, ast.ClassDef):
                function_parent = node.parent.name
            elif isinstance(node.parent, ast.Module):
                function_parent = file_name
            function_code_str = ast.unparse(node)
            break
    return function_parent, function_code_str


def get_superficial_function_code(file_source_code: str, function_name: str, function_parent: str):
    function_code_str = ""
    start_line = ""
    end_line = ""
    try:
        ast_file = ast.parse(file_source_code)
    except:
        return start_line, end_line, function_code_str

    for node in ast.walk(ast_file):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    for node in ast.walk(ast_file):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            if (isinstance(node.parent, ast.Module)
                    or (isinstance(node.parent, ast.ClassDef) and node.parent.name == function_parent)):
                function_code_str = ast.unparse(node)
                start_line = node.lineno
                end_line = node.end_lineno
                break
    # when cannot find a very strict one, try a superficial one
    if function_code_str == "":
        for node in ast.walk(ast_file):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                function_code_str = ast.unparse(node)
                start_line = node.lineno
                end_line = node.end_lineno
                break
    return start_line, end_line, function_code_str


def get_method_by_name(function_name: str, function_start_line, function_end_line,
                       method_lists: list[Method]) -> Method | None:
    filter_list = list(filter(lambda method: method.name == function_name
                                             and method.start_line == function_start_line
                                             and method.end_line == function_end_line,
                              method_lists)
                       )
    if len(filter_list) == 1:
        return filter_list[0]
    else:
        return None


def category_and_localize_single_line(parsed_diff, lang):
    added, rms = OrderedDict(parsed_diff["added"]), OrderedDict(parsed_diff["deleted"])

    common_lines = set.intersection(set(added.keys()), set(rms.keys()))

    if len(common_lines) == 0: return False

    # All non-common lines have to be comments!

    if not all_statements_common(added, common_lines, lang): return False
    if not all_statements_common(rms, common_lines, lang): return False

    for line_ix in common_lines:
        add_line, rm_line = added[line_ix], rms[line_ix]

        is_add_stmt = is_statement(add_line, lang)
        is_rm_stmt = is_statement(rm_line, lang)

        if not is_add_stmt and not is_rm_stmt: continue
        if is_add_stmt != is_rm_stmt: return False  # Here we uncomment things or remove a code (no code change)

        if has_diff(add_line, rm_line, lang):
            return line_ix, rm_line


def is_single_hunk_change(parsed_diff):
    added, deleted = OrderedDict(parsed_diff["added"]), OrderedDict(parsed_diff["deleted"])
    common_lines = set.intersection(set(added.keys()), set(deleted.keys()))
    if len(common_lines) == 0 and ((len(added) == 0) ^ (len(deleted) == 0)):
        return True
    if (len(common_lines) > 0
            and is_consecutive(list(added.keys()))
            and is_consecutive(list(added.keys()))):
        return True
    else:
        return False


def is_single_line(parsed_diff, lang):
    added, rms = OrderedDict(parsed_diff["added"]), OrderedDict(parsed_diff["deleted"])

    common_lines = set.intersection(set(added.keys()), set(rms.keys()))

    if len(common_lines) == 0: return False

    # All non-common lines have to be comments!

    if not all_statements_common(added, common_lines, lang): return False
    if not all_statements_common(rms, common_lines, lang): return False

    diff_lines = 0

    for line_ix in common_lines:
        add_line, rm_line = added[line_ix], rms[line_ix]

        is_add_stmt = is_statement(add_line, lang)
        is_rm_stmt = is_statement(rm_line, lang)

        if not is_add_stmt and not is_rm_stmt: continue
        if is_add_stmt != is_rm_stmt: return False  # Here we uncomment things or remove a code (no code change)

        if has_diff(add_line, rm_line, lang): diff_lines += 1
        if diff_lines > 1: break

    return diff_lines == 1


def is_consecutive(numbers: list):
    if len(numbers) > 0:
        for i in range(1, len(numbers)):
            if int(numbers[i]) - int(numbers[i - 1]) != 1:
                return False
    return True


def all_statements_common(lines, common_set, lang):
    for i, line in lines.items():
        if i in common_set: continue
        if is_statement(line, lang): return False
    return True


def is_statement(line, lang):
    if len(line) == 0: return False
    return any(tok_type != "comment" for _, tok_type in tokenize(line, lang))


def has_diff(A, B, lang="python"):
    Atok, Btok = list(tokenize(A, lang)), list(tokenize(B, lang))
    if len(Atok) != len(Btok): return True
    return any(Atok[i] != Btok[i] for i in range(len(Atok)))


def tokenize(text, lang="python"):
    if lang == "python":
        for tok in pytokenize_text(text): yield tok
        return
    raise ValueError("Unknown language: %s" % lang)


def pytokenize_text(line):
    import token
    import tokenize
    from io import StringIO
    try:
        for tok in tokenize.generate_tokens(StringIO(line).readline):
            yield tok.string, token.tok_name[tok.type]
    except Exception:
        yield "ERROR", "ERROR"


def single_token_mod(diff, lang):
    hunks = parse_hunks(diff)
    single_diff = None

    for hunk in hunks:
        new_lines, old_lines = list(iter_stmts(hunk.after)), list(iter_stmts(hunk.before))

        if len(new_lines) != len(old_lines): return "None"
        if len(new_lines) == 0: return "None"

        for i in range(len(new_lines)):
            diff = diff_tokens(new_lines[i], old_lines[i], lang)

            if len(diff) == 0: continue
            if len(diff) > 1: return "None"

            if single_diff is None:
                single_diff = diff[0][0][1]
            else:
                return "None"

    return single_diff if single_diff is not None else "None"


def diff_tokens(A, B, lang="python"):
    Atok, Btok = list(tokenize(A, lang)), list(tokenize(B, lang))

    limit = min(len(Atok), len(Btok))

    diffs = [(Atok[i], Btok[i]) for i in range(limit) if Atok[i] != Btok[i]]

    diffs.extend([(Atok[i], ("[NONE]", "None")) for i in range(limit, len(Atok))])
    diffs.extend([(("[NONE]", "None"), Btok[i]) for i in range(limit, len(Btok))])

    return diffs


def iter_stmts(text, lang="python"):
    if lang == "python":
        for stmt in pyiter_stmts(text): yield stmt
        return

    raise ValueError("Unknown language: %s" % lang)


def pyiter_stmts(text):
    start_ix = 0

    brackets = {"{": "}", "(": ")", "[": "]"}
    bcount = {b: 0 for b in brackets.values()}

    for i, c in enumerate(text):
        if c in brackets and not (c in bcount and bcount[c] > 0): bcount[brackets[c]] += 1; continue
        if c in bcount:   bcount[c] -= 1; continue

        should_split = False

        if c == ";": should_split = True
        if c == "\n": should_split = sum(bcount.values()) == 0

        if should_split:
            if i != start_ix: yield text[start_ix:i]
            start_ix = i + 1


def compute_edit_script_it(diff):
    # For efficiency, we do not compute the edit script for the full AST
    # While this works in most cases, there exists some corner cases where it fails.
    # However, we can detect when computation fails:
    # ghost nodes (i.e. nodes that do not appear in AST)
    # appear in the edit script.
    # If this is the case, we increase the AST context and recompute the edit script

    edit_script = None
    diff_level = 0

    while diff_level < 3:
        edit_script = diff.edit_script()

        if not _is_ghost_script(edit_script): return edit_script

        diff = _increase_ast_size(diff, diff_level)
        diff_level += 1

    return edit_script  # Return most precise edit script (even if it has ghost nodes)


def _increase_ast_size(diff, current_level):
    if current_level == 0:
        try:
            return diff.statement_diff()
        except Exception:
            return diff

    if current_level == 1:
        return diff.root_diff()

    if current_level > 1: return diff


def _is_ghost_script(script):
    if script is None: return True
    if len(script) == 0: return False

    return hasattr(script[0].target_node, "node_id")


def filter_modified_python_files(commit) -> list[ModifiedFile]:
    modified_files = commit.modified_files
    # 2. one commit only has 1 python file change
    modified_python_files = []
    for modified_file in modified_files:
        if (modified_file.filename.endswith('.py')
            and 'test' not in modified_file.filename
            and 'test' not in modified_file.new_path) \
                and modified_file.change_type == ModificationType.MODIFY:
            modified_python_files.append(modified_file)
    return modified_python_files
