def main():
    # Define your sets with case IDs
    instruct_baseline = {'3', '5', '6', '7', '8', '9', '23', '24', '26', '27', '28', '36', '37', '38', '42', '48', '49', '54', '66', '67'}
    instruct_combine = {'2', '3', '5', '6', '7', '8', '9', '10', '17', '23', '24', '26', '27', '28', '29', '32', '36', '37', '38', '42', '46', '47', '48', '49', '53', '54', '60', '66', '67'}

    create_2_set_venn_percentage(instruct_baseline, instruct_combine, 'Baseline', 'HAFix-Agg', 'instruct_1_HAFix_percentage')

    instruct_6 = {'2', '3', '5', '6', '7', '8', '9', '10', '17', '23', '24', '26', '27', '29', '32', '36', '38', '42', '48', '49', '54', '66'}
    create_2_set_venn_percentage(instruct_baseline, instruct_6, 'baseline', 'FLN-all', 'instruct_6_FLN-all_percentage')























    create_2_set_venn(instruct_baseline, instruct_combine, 'baseline', 'aggregation', 'instruct')

    instruct_label_baseline = {'3', '5', '6', '7', '8', '9', '23', '24', '26', '27', '28', '32', '36', '37', '41', '42', '44', '49', '54', '67'}
    instruct_label_combine = {'3', '6', '7', '8', '9', '10', '23', '24', '26', '27', '28', '32', '36', '37', '41', '42', '44', '46', '49', '53', '54', '60', '67'}
    create_2_set_venn(instruct_label_baseline, instruct_label_combine, 'baseline', 'aggregation', 'instruct_label')
    create_2_set_venn_percentage(instruct_label_baseline, instruct_label_combine, 'baseline', 'aggregation', 'instruct_label_percentage')


    infill_baseline = {'2', '23', '24', '26', '47', '48', '49'}
    infill_combine = {'2', '5', '23', '26', '41', '47', '48', '49'}
    create_2_set_venn(infill_baseline, infill_combine, 'baseline', 'aggregation', 'infill')
    create_2_set_venn_percentage(infill_baseline, infill_combine, 'baseline', 'aggregation', 'infill_percentage')


    union_baseline = {'2', '3', '5', '6', '7', '8', '9', '23', '24', '26', '27', '28', '32', '36', '37', '38', '41', '42', '44', '47', '48', '49', '54', '66', '67'}
    union_aggregation = {'2', '3', '5', '6', '7', '8', '9', '10', '17', '23', '24', '26', '27', '28', '29', '32', '36', '37', '38', '41', '42', '44', '46', '47', '48', '49', '53', '54', '60', '66', '67'}
    create_2_set_venn(union_baseline, union_aggregation, 'baseline', 'aggregation', 'union')
    create_2_set_venn_percentage(union_baseline, union_aggregation, 'baseline', 'aggregation', 'union_percentage')



def create_2_set_venn(set1, set2, set1_label, set2_label, picture_name):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2, venn2_circles

    def format_label_text(numbers):
        """Format the list of numbers into a multi-line string with a dynamic number of items per line."""
        sorted_numbers = sorted(numbers, key=int)
        lines = []
        line_length = 1
        i = 0

        while i < len(sorted_numbers):
            line = ", ".join(sorted_numbers[i:i + line_length])
            lines.append(line)
            i += line_length
            line_length += 1  # Gradually increase the number of items per line

        return "\n".join(lines)

    # Create the Venn diagram
    venn = venn2([set1, set2], (set1_label, set2_label))

    # Customize the labels inside the circles
    venn.get_label_by_id('10').set_text(format_label_text(set1 - set2))
    venn.get_label_by_id('01').set_text(format_label_text(set2 - set1))
    venn.get_label_by_id('11').set_text(format_label_text(set1 & set2))

    # Optionally set the font size for better readability
    for subset in ['10', '01', '11']:
        venn.get_label_by_id(subset).set_fontsize(8)

    plt.savefig(f'{picture_name}.png', bbox_inches='tight')
    plt.close()


def create_2_set_venn_percentage(set1, set2, set1_label, set2_label, picture_name):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2, venn2_circles

    def calculate_percentage(subset, total):
        """Calculate the percentage of the subset relative to the total."""
        return len(subset) / total * 100

    total_elements = len(set1 | set2)

    # Calculate percentages for each subset
    only_set1 = calculate_percentage(set1 - set2, total_elements)
    only_set2 = calculate_percentage(set2 - set1, total_elements)
    intersection = calculate_percentage(set1 & set2, total_elements)
    # Create the Venn diagram
    venn = venn2([set1, set2], (set1_label, set2_label))

    # Customize the labels inside the circles with percentages
    if len(set1 - set2) != 0:
        venn.get_label_by_id('10').set_text(f'{len(set1 - set2)}\n\n{only_set1:.2f}%')
    else:
        venn.get_label_by_id('10').set_text(f'')
    venn.get_label_by_id('01').set_text(f'{len(set2 - set1)}\n\n{only_set2:.2f}%')
    venn.get_label_by_id('11').set_text(f'{len(set1 & set2)}\n\n{intersection:.2f}%')


    # Optionally set the font size for better readability
    for subset in ['10', '01', '11']:
        venn.get_label_by_id(subset).set_fontsize(8)

    # Change the colors of the circle areas if needed
    # venn_patches = venn.patches
    # venn_patches[0].set_facecolor('red')
    # venn_patches[1].set_facecolor('blue')
    # venn_patches[2].set_facecolor('purple')  # Overlapping area color if needed

    plt.savefig(f'{picture_name}.png', bbox_inches='tight')
    plt.close()


def create_3_set_venn():
    # import matplotlib.pyplot as plt
    # from matplotlib_venn import venn3
    #
    # # Define your sets with case IDs
    # set1 = {'ID1', 'ID2', 'ID3', 'ID4'}
    # set2 = {'ID3', 'ID4', 'ID5', 'ID6'}
    # set3 = {'ID4', 'ID6', 'ID7', 'ID8'}
    #
    # # Create the Venn diagram
    # venn = venn3([set1, set2, set3], ('Set1', 'Set2', 'Set3'))
    #
    # # Customize the labels inside the circles
    # venn.get_label_by_id('100').set_text('\n'.join(set1 - set2 - set3))
    # venn.get_label_by_id('010').set_text('\n'.join(set2 - set1 - set3))
    # venn.get_label_by_id('001').set_text('\n'.join(set3 - set1 - set2))
    # venn.get_label_by_id('110').set_text('\n'.join(set1 & set2 - set3))
    # venn.get_label_by_id('101').set_text('\n'.join(set1 & set3 - set2))
    # venn.get_label_by_id('011').set_text('\n'.join(set2 & set3 - set1))
    # venn.get_label_by_id('111').set_text('\n'.join(set1 & set2 & set3))
    #
    # # Optionally set the font size for better readability
    # for subset in ['100', '010', '001', '110', '101', '011', '111']:
    #     venn.get_label_by_id(subset).set_fontsize(8)
    #
    #
    # # Display the plot
    # plt.savefig('venn3.png', bbox_inches='tight')
    # # Display the plot
    # plt.show()
    # plt.close()
    pass


if __name__ == '__main__':
    main()