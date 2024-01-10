from msilib import schema
import os           # Filesystem
import re           # Regular Expressions
import subprocess
from sys import api_version
from urllib.parse import scheme_chars   # Ability to exec Java for PlantUML generator
import yaml         # Ability to read YAML files
import json         # Ability to read JSON files
import textwrap     # Ability to wrap text
import datetime     # Ability to embed the current date

PLANT_JAR='./plantuml-mit-1.2023.13.jar'
DOT_EXE='C://Program Files/Graphviz/bin/dot.exe'

def write_json(path: str, root: dict):
    """Dump JSON {root} into {path}"""
    with open(path, 'w') as f:
        json.dump(root, f, indent=2)

def find_files(path: str, regexp: str) -> list:
    """Return a list of fully-qualified filenames matching {regexp} under {path}"""

    # Sanity check on {root}
    if not os.path.exists(path):
        raise Exception(f'Root directory [{path}] does not exist')

    files_found: list[str] = []
    try:
        exp = re.compile(regexp)
    except Exception as e:
        raise Exception(f'Invalid regexp [{regexp}]: [{e}]')
    
    for root, dirs, files in os.walk(path):
        for name in files:
            full_path = os.path.join(root, name)
            if exp.search(name):
                # print(f'{full_path} matches {regexp}')
                files_found.append(full_path)

    return files_found

def modify_puml_files(root : str, out_dir: str, db):
    PUML = 'Resource_.*\.puml$'

    # Sanity check on {out_dir}
    if not os.path.exists(out_dir):
        raise Exception(f'modify_puml_files: Output directory [{out_dir}] does not exist')
    if not os.path.isdir(out_dir):
        raise Exception(f'modify_puml_files: Output directory [{out_dir}] exists, but is not a directory')

    puml_files = find_files(root, PUML)
    print(f'Found {len(puml_files)} PUML files')

    for file in puml_files:
        modify_puml(file, out_dir, db)


def modify_puml(puml_path: str, out_dir: str, db):
    """Modify the PUML files in {puml_path} to add hyperlinks, descriptions etc, then write to {out_dir} directory"""
    # Sanity check on {puml_path}
    if not os.path.exists(puml_path):
        raise Exception(f'PlantUML file [{puml_path}] does not exist')

    # Sanity check on location of the PlantUML generator
    if not os.path.exists(PLANT_JAR):
        raise Exception(f'PlantUML JAR file [{PLANT_JAR}] does not exist')

    # print(f'Reading PlantUML file [{puml_path}]')
    with open(puml_path, 'r') as puml_handle:
        # removing the newline characters
        puml_lines = [line.rstrip() for line in puml_handle]

    REF = "<<Ref>>"
    PIVOT = "<<Pivot>>"
    RELATED = "Related"
    REFORVALUE = "RefOrValue"
    #HOST="http://localhost:8000/"
    HOST=""
    class_definition = re.compile(f'^class\s+(\w+)\s+({REF}|{PIVOT})')
    related_ref_or_value = re.compile(f'^class\s+((Related)?(.*)(?:RefOrValue))')

    # Open a PUML file for wriing into the modifed directory
    in_filename = os.path.basename(puml_path)
    in_filename = re.sub('^Resource_', '', in_filename)
    out_filename = os.path.join(out_dir, in_filename)
    if os.path.exists(out_filename):
        os.remove(out_filename)

    modified_puml = open(out_filename, "x")

    api_db = db['api']
    schema_db = db['schema']

    for line in puml_lines:
        if re.search('^@startuml', line):
            # A bit early in the file, but inject a title
            line += f'\ntitle TMF Schema Class Diagram\n'
            line += f'\nlegend\n[[index.htm Go to API Catalog]]\nend legend\n'
            line += f'header Diagram generated on {datetime.datetime.now().strftime("%x")}\n\n'
        if re.search('^class\s+', line):
            # {line} is a class definition, looking closer...
            match = re.search(class_definition, line)
            if match != None:
                class_name = match.group(1)
                class_type = match.group(2)
                # Match [{match.group(0)}] has Class name [{class_name}] and stereotype [{class_type}]
                if class_type == PIVOT:
                    # [{line}] describes the primary resource of this file
                    if class_name in schema_db:
                        schema_detail = schema_db[class_name]
                        # [{class_name}] is found in the schema_db: [{schema_detail}]
                        if 'api' in schema_detail:
                            api_name = api_version = ''
                            id = schema_detail['api']
                            # print(f'* modify_puml: Found [{class_name}] in api_db related to TMF [{id}]: ')
                            # Need to extract name, operations and notifications from that API detail
                            if id in api_db:
                                api_detail = api_db[id]
                                # Found TMF-API [{id}] related to schema [{class_name}] in api_db: [{api_detail}]
                                if 'version' in api_detail:
                                    # Found TMF-API [{id}] related to schema [{class_name}] in api_db with version [{api_version}]
                                    api_version = api_detail['version']
                                if 'name' in api_detail:
                                    # Found TMF-API [{id}] related to schema [{class_name}] in api_db with name [{api_name}]
                                    api_name = api_detail['name']

                                if 'operations' in api_detail:
                                    methods = f'\n   {api_detail["operations"]}\n  ..'
                                else:
                                    methods = ""

                                if 'notifications' in api_detail:
                                    notifications = api_detail['notifications']
                                    # print(f'Found [{class_name}] in api_details with notifications: [{notifications}], type [{type(notifications)}], length [{len(notifications)}]')
                                    if type(notifications) is str:
                                        # If there are no spaces, the csv are taken as a single value string
                                        notifications = notifications.split(',')
                                    notification_label = "\n  .."
                                    for notification in notifications:
                                        notification_label = f'\n  {notification}{notification_label}'
                                else:
                                    notification_label = ""
                                if 'description' in schema_detail:
                                    description = schema_detail["description"]
                                    # Wrap this description to 80 character width - to make a wide resource box
                                    description = textwrap.fill(description, 45, break_long_words=False, replace_whitespace=True)
                                    description = re.sub('\n', '\n<font size=9><i>', description)
                                    description = f'\n  <font size=9><i>{description}\n  ..'
                                else:
                                    # print(f'* Found [{class_name}] in api_details but it has no description: [{schema_detail}]')
                                    description = ""

                                class_title = f'\"{class_name}\\n(<font size=9><i>from [[{HOST}TMF{id}.svg TMF{id}-{api_name}]] v{api_version}</i>)\" as {class_name} {PIVOT} {{'
                                # Rewriting the line:\n    {line}\n    as:\n    class {class_title}
                                line = f'class {class_title}{description}{methods}{notification_label}'
#                            else:
#                                print(f'* Found [{class_name}] in api_db but it is not in api_db: [{schema_detail}]')
#                        else:
#                            print(f'* Found [{class_name}] is in schema_db but has no TMF API ("api" attribute): [{schema_detail}]')
#                    else:
#                        print(f'* [{class_name}] from PUML file is not directly mentioned in any API rules file')

                elif class_type == REF:
                    # Found "<Entity>Ref"
                    entity = re.sub('Ref$', '', class_name)
                    # Rewriting the line
                    line = f'class \"[[{HOST}{entity}.svg {entity}]]Ref\" as {class_name} {REF} {{'
#                else:
#                    print(f'* The line:[{line}]\n  * With a class name [{class_name}] is not a {PIVOT} or {REF}')
            else:
                # print(f'[{line}] is not a <Ref> or a <Pivot> - so looking for (Related)ThingRefOrValue')
                match = re.search(related_ref_or_value, line)
                if match != None:
                    # Found "(Related)<Entity>RefOrValue"
                    related = match.group(2) or ""
                    entity = match.group(3) or ""
                    # print(f'* Match [{match.group(0)}] is a (Related)Entity(RefOrValue) with a Class name [{entity}]')
                    # print(f'* Groups [{match.groups()}]')
                    line = f'class \"{related}[[{HOST}{entity}.svg {entity}]]RefOrValue\" as {related}{entity}RefOrValue {{'
#                else:
#                    print(f'* No match for line [{line}]')
#        print(f'Writing line: [{line}]')
        modified_puml.write(line + '\n')
    modified_puml.close()


def generate_diagrams(puml_path: str, svg_dir: str):
    """Take a directory of PlantUML files and generate an output directory of SVG files

    Args:
        puml_path (puml_dir): _Directory of PlantUML files_
        out_dir (svg_dir): _Output directory of SVG files_
    """
    puml_files = find_files(puml_path, f'.*\.puml$')

    for file in puml_files:
        # -nbthread auto
        cmd = f'java -jar {PLANT_JAR} -graphvizdot \"{DOT_EXE}\" \"{file}\" -output \"{svg_dir}\" -Djava.awt.headless=true -nometadata -tsvg -v'
        print(f'Generating diagram from PlantUML [{file}]:\n  {cmd}')
        subprocess.run(cmd)


def classify_schema(root: str):
    """Extract details (domain) from all schema files. Correlate with known API resources"""
    SCHEMA= '.*\.schema\.json$'
    schema_files = find_files(root, SCHEMA)

    schema_db = {}

    for schema_path in schema_files:
        filename = os.path.basename(schema_path)
        schema_regex = re.match('(\w+)\.schema\.json$', filename)
        if schema_regex:
            schema_name = schema_regex.group(1)
            # Get the directory as a proxy to the schema 'domain'
            domain_name = os.path.basename(os.path.dirname(schema_path))
            # Add this schema to the schema database
            if schema_name not in schema_db:
                node = f'{{"name": "{schema_name}", "domain": "{domain_name}" }}'
                schema_db[schema_name] = json.loads(node)
#           else:
#               print(f'Schema [{schema_name}] in [{domain_name}] is already in the schema database from: [{schema_db[schema_name]["domain"]}]')
            schema_entry = schema_db[schema_name]

            # Read the schema file to get the description
            try:
                lines = open(schema_path, 'r').readlines()
                schema = json.loads(''.join(lines))
                if 'definitions' in schema:
                    definitions = schema['definitions']
                    if schema_name in definitions:
                        item = definitions[schema_name]
                        if 'description' in item:
                            description = item['description']
                            schema_entry['description'] = description
#                    else:
#                        print(f'Malformed Schema [{schema_name}] in [{domain_name}]: The name is not in the definitions section: [{definitions}]')
            except Exception as e:
                print(f'Unable to read schema file [{schema_path}]:\n * [{e}]')
                continue
        else:
#            print(f'No schema name found in [{filename}]')
            schema_name = None
    return schema_db


def join_db(api_db, schema_db):

    # Correlate this schema with any known API resources:
    # * Add the API's TMF-ID into the schema from which it is referenced
    # * Add the schema's domain into the API which references it
    for api in api_db:
        api_details = api_db[api]
        if 'resources' in api_details:
            for resource in api_details['resources']:
                if resource in schema_db:
                    # Resource [{resource}] in the api_db (API [{api}]) is found in the schema_db
                    schema_details = schema_db[resource]
                    # Copy some attributes from the API to the Schema DB and visa-versa
                    schema_details['api'] = api_details['id']
                    api_details['domain'] = schema_details['domain']

    joined_db = { 'api': api_db, 'schema': schema_db }
    return joined_db


def classify_apis(root: str):
    """Extract key details (API version, operations) about the main resources from all API rules files"""
    RULES = '.*\.rules\.yaml$'

    database = {}
    rules_files = find_files(root, RULES)
    print(f'classify_apis: Found {len(rules_files)} files that fit [{RULES}]')

    for file in rules_files:
        try:
            new_detail = analyse_rules_file(file)
            database.update(new_detail)
        except Exception as e:
            # Ignore this rules file and carry on
            print(f'classify_apis: Unable to analyse rules file [{file}]:\n * [{e}]')
            continue
    return database


def generate_api_files(out_dir: str, db: dict):
    """Generate a PUML file (TMFxxx.puml) for each API in the API database"""
    api_db = db['api']
    schema_db = db['schema']

    for id in api_db:
        api_detail = api_db[id]
        api_name = api_detail.get('name')
        api_version = api_detail.get('version')
        api_basePath = api_detail.get('basePath')
        if 'description' in api_detail:
            api_description = api_detail.get('description')
            # Wrap this description to 45 character width - to fit in the class diagram box
            # Strip certain redundant lines if present: Copyright, Release etc
            api_description = re.sub('Copyright.*\n', '', api_description)
            api_description = re.sub('[\s#*]+\s\n', '', api_description)
            api_description = textwrap.fill(api_description, 80, break_long_words=False, replace_whitespace=True)
            api_description = api_description + ';\n'
        else:
            print(f'generate_api_files: No description for API [{api_name}]')
            api_description = ';\n'

#        print(f'Making PUML for TMF[{id}]: [{api_name}] [v{api_version}]')

        puml = f'@startmindmap\n'
        puml += '<style>\nnode {\n  Padding 10\n  Margin 3\n  LineThickness 0.5\n  RoundCorner 20\n    Shadowing 1\n}\n'
        puml += 'arrow {\n  LineStyle 4\n  LineThickness 1\n  LineColor gray\n}\n</style>\n'
        puml += f'legend\n[[index.htm Go to API Catalog]]\nend legend\n'
        puml += f'header Diagram generated on {datetime.datetime.now().strftime("%x")}\n\n'

        puml += f'*[#ff9999]:<b>TMF{id}-{api_name}</b> (v{api_version})\n'
        puml += f'....\n<code>\n{api_basePath}\n</code>\n....\n'
        puml += f'{api_description}\n'

        puml += f'title <b>TMF{id}-{api_name}</b> (v{api_version}) API Layout\n'

        for resource in api_detail['resources']:
            resource_detail = api_detail['resources'][resource]
            # Found resource [{resource}] in [{api_name}] with details: [{resource_detail}]
            # Write out a PUML class for each resource
            puml += f'\n**[#99ff99]:<b>[[{resource}.svg {resource}]]'
            if resource in schema_db:
                # Wrap this description to 80 character width - to make a wide resource box
                description = schema_db[resource].get("description")
                if description:
                    puml += '\n....\n'
                    description = textwrap.fill(description, 100, break_long_words=False, replace_whitespace=True)
                    puml += f'{description}'
                    
            else:
                print(f'generate_api_files: No schema_db entry for resource [{resource}]')
            
            if 'operations' in resource_detail:
                puml += '\n....'
                puml += f'\n{resource_detail.get("operations")}'
            if 'notifications' in resource_detail:
                puml += '\n....'
                for notification in resource_detail['notifications']:
                    puml += f'\n{notification}'
            puml += f';\n'


        # Write out a PUML file for the API overall (TMFxxx.puml)
        out_filename = f'{out_dir}\\TMF{id}.puml'
        print(f'Writing API PUML file [{out_filename}]')
        api_puml = open(out_filename, 'w')
        api_puml.write(puml)
        api_puml.write('@endmindmap')
        api_puml.close()


def analyse_rules_file(rules_path: str):
    """Extract key details (API version, operations) from an individual rules file"""

    # Pull out the TMF-ID and API name from the rules file name
    match = re.search('TMF(\d+)_(\w+)', rules_path)
    if match != None:
        id = match.group(1)
        name = match.group(2).replace('_', ' ')
    else:
#        print(f'analyse_rules_file: Not processing rules file [{rules_path}] - No TMF ID found (file ignored)')
        return {}

    try:
        # Load the Rules YAML file
        yml = yaml.safe_load(open(rules_path, 'r'))
    except Exception as e:
        raise Exception(f'Unable to read YAML file [{rules_path}]:\n * [{e}]')    

    root = next(iter(yml.values()))
    api = {}
    api[id] = {
        'id': id,
        'name': name,
        'version': root['version'],
        'description': root['doc'],
        'basePath': root['basePath']
    }
    api_resource_list = api[id]['resources'] = {}

    # Get the list of resources defined in this rules file
    resources = root.get('resources')
    for resource in resources:
        rules = root.get(f'rules {resource}')
        if rules:
            operations = rules.get('operations')
            if operations and operations != 'NOOPERATION':
                api_resource_list[resource] = { 'operations': operations }
                notifications = rules.get('notifications')
                if notifications != None:
                    # Is this a list of strings or a single string?
                    # "x,y" in a rules file is a string. "x, y" is a list of strings.
                    if isinstance(notifications, str):
                        notifications = [notifications]                    
                    api_resource_list[resource]['notifications'] = notifications
    return api

def make_index(out_dir: str, db):
    """Take previous extracted data and generate a HTML index page across all APIs"""

    DOMAINS = ( "EngagedParty", "Customer", "Product", "Service", "Resource", "Common" )
    domain_index = {}
    api_db = db['api']

    for api in api_db:
        api_detail = api_db[api]
        api_name = api_detail['name']
        if 'domain' in api_detail:
            api_domain = api_detail['domain']
            if api_domain in DOMAINS:
                # Indexing APIs by Domain, so put the API name inside the detail
                domain_index[api_domain] = domain_index.get(api_domain, []) + [api_detail]
            else:
                print(f'* API [{api_name}] is NOT in a known/useful domain [{api_domain}]')
        else:
            print(f'* No API domain found for [{api_name}]: {json.dumps(api_detail, indent=2)}')

#    print(f'domain_index: [{json.dumps(domain_index, indent=4, sort_keys=True)}]')

    index_file = open(f'{out_dir}\\index.htm', 'w')
    index_file.write('<html>\n<head>\n<link rel=\'stylesheet\' type=\'text/css\' href=\'domains.css\'>\n<title>TMF APIs</title>\n</head>\n<body>\n')
    for domain in DOMAINS:
        # Sort the schemas within each domain alphabetically by schema name
        domain_index[domain] = sorted(domain_index.get(domain, []), key=lambda x: x['name'])
        if domain in domain_index:
            index_file.write(f'<br/>\n')
            index_file.write(f'<div class="grid-container"><div id=\'domain-title\'>{domain}</div>\n')
            for api in domain_index[domain]:
                name = api['name'] if 'name' in api else 'NO-NAME'
                version = api['version'] if 'version' in api else 'NO-VERSION'
                id = api['id'] if 'id' in api else 'NO-ID'
                # Need to figure out how to left-justrify the version number)
                index_file.write(f'  <div id="api-box"><div class="number">TMF{id}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;v{version}</div><div class="title"><a href="TMF{id}.svg">{name}</a></div></div>\n')
            index_file.write(f'</div>\n')
    
    index_file.write('</body>\n</html>')
    index_file.close()
    return domain_index