import glob, re, os
# from bs4 import BeautifulSoup

# Configuration
template = "../components/svg/*.astro"
template = "../components/test-01/*.astro"

cwd = os.path.dirname(os.path.realpath(__file__)) + os.sep

def split_frontmatter_lines(text):
    lines = text.split('\n')
    return list(filter(lambda x: x != '', lines))

def extract_frontmatter_components(lines):
    components = []
    for line in lines:
        result = re.match(r'import\s+(\w+)\s+from\s+("@components[^"]+")', line)
        if result != None:
            file = re.sub(r'(astro)"$', 'twig', result.group(2))
            file = re.sub(r'^"(@components)', '_components', file)
            compo = {
                "name": result.group(1),
                "file": file
            }
            components.append(compo)
    return components

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
        statement = '{%% include "%s" with { %s } %%}' % (compo["file"], '_PARAMS_')
    if match.group(2) is not None:
        parts = []
        attributes = re.split(r'([^=]+=".*"+)', match.group(2))
        attributes = list(filter(lambda x: x != '', attributes))
        for attribute in attributes:
            result = re.match(r'^([^=]+)=(".*"+)$', attribute.strip())
            if result is not None:
                parts.append(': '.join([result.group(1), result.group(2)]))
        params = ', '.join(parts)
    statement = statement.replace('_PARAMS_', params)

    return statement

def convert_body(body, components):
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

