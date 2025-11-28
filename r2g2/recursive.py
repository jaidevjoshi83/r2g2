import xml.etree.ElementTree as ET
import re

def clean_arg_name(arg: str) -> str:
    """Remove leading '-' but preserve internal dashes/underscores."""
    return re.sub(r"^[-]+", "", arg).replace("-", "_")

def param_xml_gen(param_name, param_type="text", label=None):
    """Return a Galaxy <param> element as an Element."""
    if label is None:
        label = param_name
    return ET.Element("param", {
        "name": clean_arg_name(param_name),
        "type": param_type,
        "label": label
    })

def format_block(condition, inner, level):
    """Helper to wrap inner block in a properly indented ##if block."""
    indent = "    " * level
    return (
        f"{indent}#if {condition}\n"
        f"{inner}\n"
        f"{indent}#end if"
    )

def clean_arg_name( arg: str) -> str:
    """Remove only leading '-' or '--' but preserve internal dashes/underscores."""
    return re.sub(r"^[-]+", "", arg).replace("-", "_")

def dict_to_xml_and_command(spec, parent=None, subparser_name=None,
                            first=True, full_name=None, level=0):
    """
    Convert argparse-like dict into:
      1. Galaxy XML <param>/<conditional> structure
      2. Command template with proper indentation
    Returns (xml_element, command_str).
    """
    cmd_parts = []

    if first:
        # Top-level subparser selector
        cond = ET.Element("conditional", name="top_subparser")
        param = ET.SubElement(cond, "param", name="subparser_selector",
                              type="select", label="Select analysis type")
        for sp in spec.get("subparsers", {}):
            ET.SubElement(param, "option", value=sp).text = sp

        for sp, sp_spec in spec.get("subparsers", {}).items():
            when = ET.SubElement(cond, "when", value=sp)

            # Recurse
            xml_child, cmd_child = dict_to_xml_and_command(
                sp_spec, parent=when, subparser_name=sp,
                first=False, full_name="top_subparser",
                level=1
            )

            if xml_child is not None:
                when.append(xml_child)

            cmd_parts.append(
                format_block(f"'${'top_subparser.subparser_selector'}' == '{sp}'",
                             cmd_child, 0)
            )

        return cond, "\n".join(cmd_parts)

    # -------- Recursive case --------

    # Add mutually exclusive groups
    for group_name, opts in spec.get("mutually_exclusive_groups", {}).items():
        cond2 = ET.Element("conditional",
                           name=f"{subparser_name}__mut_{group_name}")
        
        param2 = ET.SubElement(cond2, "param",
                               name=f"{group_name}_selector",
                               type="select",
                               label=f"Choose {group_name}")
        
        inner_lavels = level*"    "
        
        mut_cond_command = f"\n{inner_lavels}#if '${full_name}.{subparser_name}__mut_{group_name}.{group_name}_selector' == '%s'\n%s\n{inner_lavels}#end if\n"

        for o in opts:
            ET.SubElement(param2, "option", value=o).text = o
        
        mut_cond_list = []
        for o in opts:
            when2 = ET.SubElement(cond2, "when", value=o)

            mut_cond_list.append(mut_cond_command%(clean_arg_name(o), f"{inner_lavels}    '${full_name}.{subparser_name}__mut_{group_name}.{clean_arg_name(o)}'"))

            when2.append(param_xml_gen(o, "boolean", o))
        parent.append(cond2)    
        cmd_parts.append("    " * level + f"{ "\n    ".join(mut_cond_list)}\n\n")
        
    # Normal params
    for opt in spec.get("groups", {}).get("options", []):
        if opt != "--help":
            parent.append(param_xml_gen(opt, "text", opt))

            cmd_parts.append("    " * level + f"'${full_name}.{clean_arg_name(opt)}'\n")

    # Nested subparsers
    if spec.get("subparsers"):
        cond_nested = ET.Element("conditional",
                                 name=f"{subparser_name}_subparser")
        param_nested = ET.SubElement(cond_nested, "param",
            name=f"{subparser_name}_subparser",
            type="select",
            label=f"Choose {subparser_name} option"
        )
        for sp in spec["subparsers"]:
            ET.SubElement(param_nested, "option", value=sp).text = sp

        inner_cmds = []
        for sp, sp_spec in spec["subparsers"].items():
            when_nested = ET.SubElement(cond_nested, "when", value=sp)
            xml_child, cmd_child = dict_to_xml_and_command(
                sp_spec, parent=when_nested, subparser_name=sp,
                first=False,
                full_name=f"{full_name}.{subparser_name}_subparser",
                level=level+1
            )

            if xml_child is not None:
                when_nested.append(xml_child)
            inner_cmds.append(
                format_block(
                    f"'${{{full_name}.{subparser_name}_subparser.{subparser_name}_subparser_selector}}' == '{sp}'",
                    cmd_child, level+1
                )
            )

        parent.append(cond_nested)
        cmd_parts.append("\n".join(inner_cmds))

    return None, "\n".join(cmd_parts)


# ----------------------------
# Example usage
# ----------------------------

spec = {
    'subparsers': {
        'LFQ': {
            'subparsers': {
                'Normalize': {
                    'subparsers': {
                        'MethodA': {
                            'mutually_exclusive_groups': {
                                'mode_group': ['--fast', '--accurate']
                            },
                            'groups': {
                                'options': ['--method', '--reference']
                            }
                        },
                        'MethodB': {
                            'subparsers': {},
                            'mutually_exclusive_groups': {},
                            'groups': {
                                'options': ['--strategy', '--baseline']
                            }
                        }
                    },
                    'mutually_exclusive_groups': {},
                    'groups': {
                        'options': ['--normalize_flag']
                    }
                },
                'Filter': {
                    'subparsers': {},
                    'mutually_exclusive_groups': {
                        'filter_group': ['--pvalue', '--fdr']
                    },
                    'groups': {
                        'options': ['--threshold', '--min_count']
                    }
                }
            },
            'mutually_exclusive_groups': {
                'group0': ['--impute-minprob', '--impute-man', '--impute-knn']
            },
            'groups': {
                'options': ['--input', '--design', '--control',
                            '--alpha', '--lfc']
            }
        },
        'TMT': {
            'subparsers': {},
            'mutually_exclusive_groups': {},
            'groups': {
                'options': ['--input_file', '--exp_design', '--control_name',
                            '--alpha_value', '--lfc_value']
            }
        }
    },
    'mutually_exclusive_groups': {
        'global_group': ['--minprob', '--man', '--knn']
    },
    'groups': {
        'options': ['--test', '--test_1']
    }
}

if __name__ == "__main__":
    xml_inputs, cmd = dict_to_xml_and_command(spec)

    print("XML <inputs> section:")
    # print(ET.tostring(xml_inputs, encoding="unicode"))

    print("\nCommand template:")
    print(cmd)
