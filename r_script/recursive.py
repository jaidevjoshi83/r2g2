import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

def clean_arg_name(arg: str) -> str:
    """Remove only leading '-' or '--' but preserve internal dashes/underscores."""
    return re.sub(r"^[-]+", "", arg).replace("-", "_")



def param_xml_gen(param_name, param_type="text", label=None):
    """Return a Galaxy <param> element as a string."""
    if label is None:
        label = param_name
    return f'<param name="{param_name.lstrip("-")}" type="{param_type}" label="{label}" />'


def dict_to_xml(spec, parent=None, subparser_name=None, first=True, full_name=None, parent_sub_parser=None, level=None, subparser_command=None):
    """Convert argparse-like dict into Galaxy tool XML elements."""
    if first:

        template = """{indent}##if '${c_name}.subparser' == '{sp}'
{indent}{inner}
{indent}##end if"""

        level=0
        c_name = "subparser_cond"
        parent_subparser="subparser_cond"

        cond = ET.Element("conditional", name="subparser_cond")
        param = ET.SubElement(cond, "param", name="subparser_selector", type="select", label="Select analysis type")


        for sp in spec.get("subparsers", {}).keys():
            ET.SubElement(param, "option", value=sp).text = sp
        parent = cond

        # main loop for top-level subparsers
        for sp, sp_spec in spec.get("subparsers", {}).items():
            when = ET.SubElement(cond, "when", value=sp)    
            tmp = template.format( indent='    '*level, c_name=c_name, sp=sp, inner='{}')

            print(tmp)
            
            dict_to_xml(sp_spec, parent=when, subparser_name=sp, first=False, full_name=c_name, parent_sub_parser=parent_subparser, level=level, subparser_command=tmp)
        return cond

    # -------- Recursive case --------
    # add mutually exclusive groups
    for group_name, opts in spec.get("mutually_exclusive_groups", {}).items():
        cond2 = ET.Element("conditional", name=f"{subparser_name}_{group_name}_cond")    
        param2 = ET.SubElement(cond2, "param", name=f"{group_name}_selector", type="select", label=f"Choose {group_name}")
        
        for o in opts:
            ET.SubElement(param2, "option", value=o).text = o
        for o in opts:
            when2 = ET.SubElement(cond2, "when", value=o)            
            when2.append(ET.fromstring(param_xml_gen(o, "boolean", o)))
        parent.append(cond2)

    # add normal params
    for opt in spec.get("groups", {}).get("options", []):
        if opt != "--help":
            parent.append(ET.fromstring(param_xml_gen(opt, "text", opt)))

    # ✅ group all nested subparsers into ONE conditional
    if spec.get("subparsers"):
        cond_nested = ET.Element("conditional", name=subparser_name+"_cond")
        full_name  = full_name+"."+subparser_name
        parent_sub_parser = parent_sub_parser+"  "+subparser_name
        level =  level+1

        subparser_command= subparser_command

        inner_temp = """{indent}##if '${c_name}.subparser' == '{sp}'
{indent}{inner}
{indent}##end if"""
        param_nested = ET.SubElement(cond_nested, "param", name=f"{subparser_name}_subparser_selector", type="select", label=f"Choose {subparser_name} option")
        for sp in spec["subparsers"].keys():
            ET.SubElement(param_nested, "option", value=sp).text = sp

        for sp, sp_spec in spec["subparsers"].items():
            when_nested = ET.SubElement(cond_nested, "when", value=sp)

            inner_tmp=inner_temp.format(indent='    '*level, c_name=full_name, sp=sp, inner='{}')

            print(subparser_command.format( inner_tmp))

            
            dict_to_xml(sp_spec, parent=when_nested, subparser_name=sp, first=False, full_name=full_name, parent_sub_parser=parent_sub_parser, level=level,subparser_command=inner_tmp )

        parent.append(cond_nested)
    return parent 

def generate_galaxy_xml(spec=None, xml=None):
    if spec:
        root = dict_to_xml(spec, first=True)
        xml_str = ET.tostring(root, encoding="unicode")
    else:
        xml_str = ET.tostring(xml, encoding="unicode")
    return minidom.parseString(xml_str).toprettyxml(indent="  ")


def mutuall_conditonal(spec, subparser_name="root"):
    """Return a list of <conditional> elements for mutually exclusive groups."""
    conds = []
    for group_name, opts in spec.get("mutually_exclusive_groups", {}).items():
        cond2 = ET.Element("conditional", name=f"{subparser_name}")
        param2 = ET.SubElement(cond2, "param", name=f"{group_name}", type="select", label=f"Choose {group_name}")
        for o in opts:
            ET.SubElement(param2, "option", value=o).text = o
        for o in opts:
            when2 = ET.SubElement(cond2, "when", value=o)
            when2.append(ET.fromstring(param_xml_gen(o, "boolean", o)))
        conds.append(cond2)
    return conds


def groups_params(spec):
    """Return a list of <param> elements for normal group options."""
    params = []
    for k in spec["groups"].keys():
        for opt in spec["groups"][k]:  
            if opt != "--help":
                params.append(ET.fromstring(param_xml_gen(opt, "text", opt)))
        return params


# print("\n".join(generate_galaxy_xml(spec).split('\n')[1:]))


a = generate_galaxy_xml(spec)
# print(a)

# d = {'subparsers': {}, 'mutually_exclusive_groups': {}, 'groups': {'options': ['--help', '--verbose', '--quietly', '--count', '--generator', '--mean', '--sd', '--mode']}}
# # flat_params(d)
# # for i in param_list:
# #     print(i)

# spec['subparsers']['LFQ']['subparsers'].keys()