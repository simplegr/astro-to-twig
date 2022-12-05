import glob, re, os

# Configuration
template = "../components/test-01/my-component.astro"
convert_html_comments_to_twig = True
use_only_for_twig_parameters = True
astro_components_alias = '@components'
twig_components_alias = '_components'

# Attributes that will be replaced
common_attributes_replacements = {
    'classes': 'class',
}

cwd = os.path.dirname(os.path.realpath(__file__)) + os.sep

####

def split_frontmatter_lines(text):
    lines = text.split('\n')
    return list(filter(lambda x: x != '', lines))

def replace_common_attributes(attributeName):
    for key, value in common_attributes_replacements.items():
        attributeName = attributeName.replace(key, value)
    return attributeName

def extract_frontmatter_components(lines):
    components = []
    import_template = r'import\s+(\w+)\s+from\s+("%s[^"]+")' % (astro_components_alias)
    for line in lines:
        result = re.match(import_template, line)
        if result != None:
            file = re.sub(r'(astro)"$', 'twig', result.group(2))
            file = re.sub(r'^"(%s)' % (astro_components_alias), twig_components_alias, file)
            compo = {
                'name': result.group(1),
                'file': file
            }
            components.append(compo)
    return components

def convert_comments(body):
    if convert_html_comments_to_twig:
        body = re.sub(r'<!--(.*?)-->', r'{# -- \1 -- #}', body)
    return body

def auto_closing_astro_tag_to_twig_include(match, compo):
    """
    Converts auto closing Astro tags to Twig. Examples:

    // import MyComponent from "@components/my-component.astro"
    <MyComponent foo="bar" baz={something} /> to plain twig include like:

    {% include "_components/my-component.twig" with { foo: "bar", baz: something } %}

    Args:
        match (dictionary): re.sub's match object.
        compo (dictionary): matched component.

    Returns:
        string: _description_
    """
    params = ''
    statement = ''
    if match.group(1) is not None:
        params_template = 'with { _PARAMS_ } only' if use_only_for_twig_parameters else 'with { _PARAMS_ }'
        statement = '{%% include "%s" %s %%}' % (compo["file"], params_template)
    if match.group(2) is not None:
        parts = []
        attributes = re.split(r'([^=]+=".*"+)', match.group(2))
        attributes = list(filter(lambda x: x != '', attributes))
        for attribute in attributes:
            result = re.match(r'^([^=]+)=(".*"+)$', attribute.strip())
            if result is not None:
                attributeName = replace_common_attributes(result.group(1))
                parts.append(': '.join([attributeName, result.group(2)]))
        params = ', '.join(parts)
    statement = statement.replace('_PARAMS_', params)

    return statement

def convert_body(body, components):
    # Convert html comments to twig
    body = convert_comments(body)
    output = []
    for compo in components:
        pattern = rf'(<{compo["name"]})\s*(.*)\s*\/>'
        result = re.sub(pattern, lambda match, compo=compo: auto_closing_astro_tag_to_twig_include(match, compo), body)

        print(result)
        # if result != None:
        #     print(result.group(0))


for fileName in glob.glob(cwd + template):
    # Open the svg file
    astroFile = open(fileName, "r", encoding="utf8")
    # twigFile = open(fileName.replace(".astro", ".twig"), "w", encoding="utf8")

    # print("Converting file %s" % twigFile.name)

    parts = re.split(r'---', astroFile.read())

    if len(parts) == 3:
        frontmatter = split_frontmatter_lines(parts[1])
        components = extract_frontmatter_components(frontmatter)
        print(components)

        body = parts[2]
        # print(body)

        convert_body(body, components)
        # print(frontmatter)

