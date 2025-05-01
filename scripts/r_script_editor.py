import argparse


def edit_r_script(r_script_path, edited_r_script_path, fakearg_path="../scripts/FakeArg.R", json_file_name="out.json"):
    with open(r_script_path,  'r' ) as fh:
        input = fh.read()

    new_input = """source("%s")\ntool_params = function (){\n"""%(fakearg_path) 
    new_input += input.replace('ArgumentParser', "FakeArgumentParser")

    lines_to_append = """
        write_json(args_list, path = "./%s", pretty = TRUE, auto_unbox = TRUE)
        }

    tool_params()
    """%(json_file_name)
    new_input += lines_to_append

    with open(edited_r_script_path,  'w' ) as fh:
        fh.write(new_input)

if __name__=='__main__':

    parser = argparse.ArgumentParser()
    
    parser.add_argument("--r_script_path","-r", type=str, required=True)
    parser.add_argument("--edited_rscript", "-o", type=str, required=True)
    parser.add_argument("--json_file", "-j", type=str,required=False)
    parser.add_argument("--fakearg_r_script", "-f", default='./FakeArg.r', type=str,required=False)
    args = parser.parse_args()

    edit_r_script(args.r_script_path, args.edited_rscript, args.fakearg_r_script, args.json_file)



