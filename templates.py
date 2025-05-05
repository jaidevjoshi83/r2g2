# The tool template
TOOL_TEMPLATE = """<tool id="{{id}}" name="{{name}}" version="{{version}}"{{tool_type}}{{profile}}>
{%- if description %}
    <description>{{ description }}</description>
{%- endif %}
{%- if macros %}
    <macros>
        <import>macros.xml</import>
    </macros>
    <expand macro="requirements" />
    <expand macro="stdio" />
{%- if version_command %}
    <expand macro="version_command" />
{%- endif %}
{%- else %}
    <requirements>
{%- for requirement in requirements %}
        {{ requirement }}
{%- endfor %}
{%- for container in containers %}
        {{ container }}
{%- endfor %}
    </requirements>
{%- if realtime %}
    <entry_points>
{%- for ep in realtime %}
        <entry_point name="{{ ep['name'] }}" requires_domain="true">
            <port>{{ ep.get('port', DEFAULT_INTERACTIVE_PORT) }}</port>
            {%- if 'url' in ep and ep['url']%}
            <url><![CDATA[{{ ep['url'] }}]]></url>
            {%- endif %}
        </entry_point>
{%- endfor %}
    </entry_points>
{%- endif %}
    <stdio>
        <exit_code range="1:" />
    </stdio>
{%- if version_command %}
    <version_command>{{ version_command }}</version_command>
{%- endif %}
{%- endif %}
    <command><![CDATA[
{%- if command %}
        {{ command }}
{%- else %}
        TODO: Fill in command template.
{%- endif %}
    ]]></command>
    <inputs>
{%- for input in inputs %}
        {{ input }}
{%- endfor %}
    </inputs>
    <outputs>
{%- for output in outputs %}
        {{ output }}
{%- endfor %}
    </outputs>
{%- if tests %}
    <tests>
{%- for test in tests %}
        <test>
{%- for param in test.params %}
            <param name="{{ param[0]}}" value="{{ param[1] }}"/>
{%- endfor %}
{%- for output in test.outputs %}
            <output name="{{ output[0] }}" file="{{ output[1] }}"/>
{%- endfor %}
        </test>
{%- endfor %}
    </tests>
{%- endif %}
    <help><![CDATA[
{%- if help %}
{{ help }}
{%- else %}
        TODO: Fill in help.
{%- endif %}
    ]]></help>
{%- if macros %}
    <expand macro="citations" />
{%- else %}
{%- if doi or bibtex_citations %}
    <citations>
{%- for single_doi in doi %}
        <citation type="doi">{{ single_doi }}</citation>
{%- endfor %}
{%- for bibtex_citation in bibtex_citations %}
        <citation type="bibtex">{{ bibtex_citation }}</citation>
{%- endfor %}
    </citations>
{%- endif %}
{%- endif %}
</tool>
"""

MACROS_TEMPLATE = """<macros>
    <xml name="requirements">
        <requirements>
{%- for requirement in requirements %}
        {{ requirement }}
{%- endfor %}
            <yield/>
{%- for container in containers %}
        {{ container }}
{%- endfor %}
        </requirements>
    </xml>
    <xml name="stdio">
        <stdio>
            <exit_code range="1:" />
        </stdio>
    </xml>
    <xml name="citations">
        <citations>
{%- for single_doi in doi %}
            <citation type="doi">{{ single_doi }}</citation>
{%- endfor %}
{%- for bibtex_citation in bibtex_citations %}
            <citation type="bibtex">{{ bibtex_citation }}</citation>
{%- endfor %}
            <yield />
        </citations>
    </xml>
{%- if version_command %}
    <xml name="version_command">
        <version_command>{{ version_command }}</version_command>
    </xml>
{%- endif %}
</macros>
"""

SHED_YML ="""name: anvio
owner: blankenberglab
description: "Anvi’o: an advanced analysis and visualization platform for ‘omics data"
homepage_url: https://github.com/merenlab/anvio
long_description: |
    Anvi’o is an analysis and visualization platform for ‘omics data. 
    It brings together many aspects of today’s cutting-edge genomic, metagenomic, and metatranscriptomic analysis practices to address a wide array of needs.
remote_repository_url: https://github.com/blankenberglab/tool-generator-anvio
type: unrestricted
categories:
- Metagenomics
auto_tool_repositories:
  name_template: "{{ tool_id }}"
  description_template: "Wrapper for the Anvi'o tool suite: {{ tool_name }}"
suite:
  name: "suite_anvio"
  description: "Anvi’o: an advanced analysis and visualization platform for ‘omics data"
  long_description: |
    Anvi’o is an analysis and visualization platform for ‘omics data. 
    It brings together many aspects of today’s cutting-edge genomic, metagenomic, and metatranscriptomic analysis practices to address a wide array of needs.
"""

galaxy_tool_citation ='''@ARTICLE{Blankenberg21-anvio,
   author = {Daniel Blankenberg Lab, et al},
   title = {In preparation..},
   }'''
