import logging
import textwrap
from typing import List
from pydriller import ModifiedFile
from pydriller.domain.commit import Method

logger = logging.getLogger(__name__)

defects4j_project_name_repository_map = {
    'Chart': 'jfreechart',
    'Cli': 'commons-cli',
    'Closure': 'closure-compiler',
    'Codec': 'commons-codec',
    'Collections': 'commons-collections',
    'Compress': 'commons-compress',
    'Csv': 'commons-csv',
    'Gson': 'gson',
    'JacksonCore': 'jackson-core',
    'JacksonDatabind': 'jackson-databind',
    'JacksonXml': 'jackson-dataformat-xml',
    'Jsoup': 'jsoup',
    'JxPath': 'commons-jxpath',
    'Lang': 'commons-lang',
    'Math': 'commons-math',
    'Mockito': 'mockito',
    'Time': 'joda-time'
}


defects4j_project_name_url_map = {
    'Chart': 'https://github.com/jfree/jfreechart.git',
    'Cli': 'https://github.com/apache/commons-cli.git',
    'Closure': 'https://github.com/google/closure-compiler.git',
    'Codec': 'https://github.com/apache/commons-codec.git',
    'Collections': 'https://github.com/apache/commons-collections.git',
    'Compress': 'https://github.com/apache/commons-compress.git',
    'Csv': 'https://github.com/apache/commons-csv.git',
    'Gson': 'https://github.com/google/gson.git',
    'JacksonCore': 'https://github.com/FasterXML/jackson-core.git',
    'JacksonDatabind': 'https://github.com/FasterXML/jackson-databind.git',
    'JacksonXml': 'https://github.com/FasterXML/jackson-dataformat-xml.git',
    'Jsoup': 'https://github.com/jhy/jsoup.git',
    'JxPath': 'https://github.com/apache/commons-jxpath.git',
    'Lang': 'https://github.com/apache/commons-lang.git',
    'Math': 'https://github.com/apache/commons-math.git',
    'Mockito': 'https://github.com/mockito/mockito.git',
    'Time': 'https://github.com/JodaOrg/joda-time.git'
}

# sourceforge 1, issues.apache/jira 7, storage.googleapis 1, github issue 8
defects4j_project_bug_description_example_map = {
    'Chart': 'https://sourceforge.net/p/jfreechart/bugs/983',
    'Cli': 'https://issues.apache.org/jira/browse/CLI-13',
    'Closure': 'https://storage.googleapis.com/google-code-archive/v2/code.google.com/closure-compiler/issues/issue-884.json',
    'Codec': 'https://issues.apache.org/jira/browse/CODEC-65',
    'Collections': 'https://issues.apache.org/jira/browse/COLLECTIONS-586',
    'Compress': 'https://issues.apache.org/jira/browse/COMPRESS-171',
    'Csv': 'https://issues.apache.org/jira/browse/CSV-224',
    'Gson': 'https://github.com/google/gson/issues/40',
    'JacksonCore': 'https://github.com/FasterXML/jackson-core/issues/531',
    'JacksonDatabind': 'https://github.com/FasterXML/jackson-core/issues/531',
    'JacksonXml': 'https://github.com/FasterXML/jackson-dataformat-xml/issues/204',
    'Jsoup': 'https://github.com/jhy/jsoup/issues/23',
    'JxPath': 'https://github.com/jhy/jsoup/issues/23',
    'Lang': 'https://issues.apache.org/jira/browse/LANG-747',
    'Math': 'https://issues.apache.org/jira/browse/MATH-934',
    'Mockito': 'https://github.com/mockito/mockito/issues/188',
    'Time': 'https://github.com/JodaOrg/joda-time/issues/21'
}


def get_accurate_function_code(file_source_code: str, function_start, function_end):
    lines = file_source_code.splitlines()
    # Convert to 0-based indices
    start_idx = function_start - 1
    end_idx = function_end
    func_lines = lines[start_idx:end_idx]
    return textwrap.dedent('\n'.join(func_lines))


def get_pydriller_method_by_long_name(methods: List[Method], name: str) -> Method | None:
    # The name here is already the long name
    candidate_list = list(filter(lambda method: method.long_name == name, methods))
    if len(candidate_list) == 0:
        return None
    else:
        return candidate_list[0]


def get_pydriller_method_by_changed_line(changed_line_location: int, modified_file: ModifiedFile) -> Method | None:
    candidate_list = list(filter(lambda changed_method:
                                 changed_method.start_line <= changed_line_location <= changed_method.end_line,
                                 modified_file.changed_methods)
                          )
    if len(candidate_list) == 1:
        return candidate_list[0]
    elif len(candidate_list) == 0:
        return None
    else:
        return sorted(candidate_list, key=lambda m: m.nloc)[0]
