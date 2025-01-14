from enum import Enum

bugs_fail_ground_test = [
    '1', '12', '13', '14', '15', '40', '55', '56', '57', '58', '59', '62', '63', '64', '65'
]

bugs_all_51_ids = [
    '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25',
    '26', '27', '28', '29', '30', '31', '32', '33', '35', '36', '37', '38', '41', '42', '43', '44', '45', '46', '47',
    '48', '49', '50', '51', '52', '53', '54', '60', '61', '66', '67', '68'
]

class HistoryCategory(Enum):
    baseline = '1'

    # blame commit
    baseline_co_evolved_functions_name_modified_file_blame = '2'
    baseline_co_evolved_functions_name_all_files_blame = '3'  # 1

    baseline_all_functions_name_modified_file_blame = '4'
    baseline_all_functions_name_all_files_blame = '5'  # 2

    baseline_all_co_evolved_files_name_blame = '6'

    baseline_function_code_pair_blame = '7'
    baseline_file_code_patch_blame = '8'  # 3

    pure_infill = '9'

    # the latest one from recursive blames
    co_evolved_functions_name_modified_file_blame_recursive = '21'
    co_evolved_functions_name_all_files_blame_recursive = '31'
    all_functions_name_modified_file_blame_recursive = '41'
    all_functions_name_all_files_blame_recursive = '51'
    all_co_evolved_files_name_blame_recursive = '61'
    function_code_pair_blame_recursive = '71'
    file_code_patch_blame_recursive = '81'

    hafix_3_6 = '36'
    hafix_3_6_2 = '362'
    hafix_3_6_2_5 = '3625'
    hafix_3_6_2_5_8 = '36258'
    hafix_3_6_2_5_8_7 = '362587'

    hafix_3_6_2_5_7 = '36257'