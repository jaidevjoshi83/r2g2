import re

def readFile(r_script_path):
    with open(r_script_path) as rScript:
        return rScript.read()

def extract_argument_lines(r_script_text):
    # Use regex to find all argument definitions
    pattern = r'parser\$add_argument\(.*?\)(?=\s*$|\s*parser|\s*#|\s*args)'
    
    # re.DOTALL flag makes the dot match newlines as well
    arguments = re.findall(pattern, r_script_text, re.DOTALL | re.MULTILINE)
    
    # Clean up the matches by removing extra whitespace
    cleaned_arguments = []
    for arg in arguments:
        cleaned_arg = re.sub(r'\s+', ' ', arg.strip())
        cleaned_arguments.append(cleaned_arg)
    
    return cleaned_arguments

def extract_inner_args(parser_line):
    # Pattern to match content between parser$add_argument( and the closing )
    pattern = r'parser\$add_argument\((.*)\)'
    match = re.search(pattern, parser_line)
    
    if match:
        return match.group(1)
    else:
        return "No arguments found"

def returnArgLines():

    
    raw_r = readFile()
    with open('test.r' ) as out:
        raw_r  = out.read()
    # Extract and print the argument lines
        argument_lines = extract_argument_lines(raw_r)

    arg_lines = []

    for i, line in enumerate(argument_lines, 1):
        arg_lines.append(extract_inner_args(line))

def c(*args):
    return list(args) 

def clean_formating(text):
    updated_text = re.sub(r'"\%\((.*?)\)s"\]', ']', text)
    return updated_text

def convert_R_args_to_dictionary(*args, **kwargs):
    return [args, kwargs]

def returnCleanedParams(r_script_path):

    cleaned_arguments = []
    param_list = []

    raw_lines = readFile(r_script_path)
    raw_arguments = extract_argument_lines(raw_lines)

    for i in raw_arguments:
        cleaned_arguments.append(extract_inner_args(i))

    for n, i in enumerate (cleaned_arguments):
        i = i.replace('TRUE', 'True')
        param_list.append(eval('convert_R_args_to_dictionary('+i+')'))

    return param_list

# print (returnCleanedParams('test.r'))
