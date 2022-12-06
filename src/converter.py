import glob, re, os

# Configuration
template = "../components/test-01/my-component.astro"
template = "../components/test-01/simple-compo-01.astro"
# template = "../components/test-01/*.astro"
convert_html_comments_to_twig = True
use_only_for_twig_parameters = True
astro_components_alias = "@components"
twig_components_alias = "_components"

# Attributes that will be replaced
common_attributes_replacements = {
    "classes": "class",
}

cwd = os.path.dirname(os.path.realpath(__file__)) + os.sep

####


def split_frontmatter_lines(text):
    lines = text.split("\n")
    return list(filter(lambda x: x != "", lines))


def replace_common_attributes(attribute_name):
    for key, value in common_attributes_replacements.items():
        attribute_name = attribute_name.replace(key, value)
    return attribute_name


def extract_frontmatter_components(lines):
    components = []
    import_template = r'import\s+(\w+)\s+from\s+("%s[^"]+")' % (astro_components_alias)
    for line in lines:
        result = re.match(import_template, line)
        if result != None:
            file = re.sub(r'(astro)"$', "twig", result.group(2))
            file = re.sub(
                r'^"(%s)' % (astro_components_alias), twig_components_alias, file
            )
            compo = {"name": result.group(1), "file": file}
            components.append(compo)
    return components


def convert_comments(body):
    if convert_html_comments_to_twig:
        body = re.sub(r"<!--(.*?)-->", r"{# -- \1 -- #}", body)
    return body


def attributes_to_twig_params(match):
    attribute_name = ""
    attribute_value = ""
    if match.group(4):
        attribute_value = match.group(4)
    if match.group(2):
        attribute_name = match.group(2)
    return "%s: %s," % (attribute_name, attribute_value)


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
    params = ""
    statement = ""
    if match.group(1) is not None:
        params_template = (
            "with { _PARAMS_ } only"
            if use_only_for_twig_parameters
            else "with { _PARAMS_ }"
        )
        statement = '{%% include "%s" %s %%}' % (compo["file"], params_template)
    if match.group(2) is not None:
        group = match.group(2)
        # print('match.group(2) -> ', group)
        parts = []
        html_attributes_pattern = r'([^=]+=".*"+)'
        dynamic_attributes_pattern = r"(([^\s]+)=({([^{}]+)}))+"
        # dynamic attributes
        if re.match(dynamic_attributes_pattern, group):
            twig_params = (
                re.sub(dynamic_attributes_pattern, attributes_to_twig_params, group)
                .rstrip()
                .rstrip(",")
            )
            parts.append(twig_params)
        # plain html attributes
        elif re.match(html_attributes_pattern, group):
            attributes = re.split(r'([^=]+=".*"+)', group)
            attributes = list(filter(lambda x: x != "", attributes))
            for attribute in attributes:
                result = re.match(r'^([^=]+)=(".*"+)$', attribute.strip())
                if result is not None:
                    attribute_name = replace_common_attributes(result.group(1))
                    parts.append(": ".join([attribute_name, result.group(2)]))
        params = ", ".join(parts)
    statement = statement.replace("_PARAMS_", params)
    return statement


def attributes_to_twig(match):
    attribute_name = ""
    attribute_value = ""
    if match.group(4):
        attribute_value = "{{ %s }}" % (match.group(4))
    if match.group(2):
        attribute_name = match.group(2)
    return ' %s="%s"' % (attribute_name, attribute_value)


def content_to_twig_output(match):
    if (
        match.group(1) is not None
        and match.group(3) is not None
        and match.group(4) is not None
    ):
        return "%s{{ %s }}%s" % (match.group(1), match.group(3), match.group(4))
    return match.group(0)


def common_attributes_as_content(match):
    if match.group(2) is not None:
        content = replace_common_attributes(match.group(2))
        if match.group(2) != content:
            return "{{ %s }}" % (content)
    return match.group(0)


def convert_body(body, components):
    # Convert content inside html tags to twig output statement: {foo} -> {{ foo }}
    body = re.sub(r"(?<=>)(\s*)({([^<]+)})(\s*)", content_to_twig_output, body)

    # Convert html comments to twig
    body = convert_comments(body)

    # Parse components
    for compo in components:
        pattern = rf'(<{compo["name"]})\s+([^\/>]*)\s*\/>'
        body = re.sub(
            pattern,
            lambda match, compo=compo: auto_closing_astro_tag_to_twig_include(
                match, compo
            ),
            body,
        )

    # Convert dynamic attributes to twig: foo={bar} -> foo="{{ bar }}"
    body = re.sub(r"\s+(([^\s]+)=({([^{}]+)}))+", attributes_to_twig, body)

    # Convert content that matches common attributes. Example: {{ classes }} -> {{ class }}
    body = re.sub(r"{{(\s*)(.*)(\s+)}}", common_attributes_as_content, body)

    return body


for fileName in glob.glob(cwd + template):
    # Read the .astro file
    astroFile = open(fileName, "r", encoding="utf8")
    # Write .twig file
    twigFile = open(fileName.replace(".astro", ".twig"), "w", encoding="utf8")

    print("Converting file %s" % twigFile.name)

    # split frontmatter and content
    parts = re.split(r"---", astroFile.read())

    if len(parts) == 3:
        frontmatter = split_frontmatter_lines(parts[1])
        # print(frontmatter)
        components = extract_frontmatter_components(frontmatter)

        body = parts[2]
        body = convert_body(body, components)
        # print(body)

        twigFile.write(body)
