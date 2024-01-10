from os import write
from crawler import find_files          # find_files matching a regexp from a root
from crawler import modify_puml_files   # Adjust PUML files
from crawler import classify_apis       # classify APIs in a PUML file
from crawler import classify_schema     # classify schemas in a PUML file
from crawler import generate_diagrams   # generate SVG files from PUML files
from crawler import make_index          # generate an index.htm starter page
from crawler import join_db             # correlate schemas with APIs
from crawler import write_json          # write a JSON to file
from crawler import generate_api_files  # generate PUML files for APIs
import json

root = "../Open_API_And_Data_Model-4.0-Sprint-2020-03"

api_db = classify_apis(root+ '/apis')
write_json(f'api_db.json', api_db)

schema_db = classify_schema(root+ '/schemas')
write_json(f'schema_db.json', schema_db)

joined_db = join_db(api_db, schema_db)
#print(f'main: {json.dumps(schema_db, indent=2)}]')

# print(f'api_details: [{json.dumps(schema_details, indent=2)}]')
modify_puml_files(root+ '/apis', '..\\puml', joined_db)
generate_api_files('..\\puml', joined_db)

generate_diagrams('..\\puml', '..\\svg')
make_index('..\\svg', joined_db)