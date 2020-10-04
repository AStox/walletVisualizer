import sys
import json
import datetime
import re
from dateutil.parser import parse

contracts = json.load(open("contracts.json", "r"))
in_data = sys.argv[1]
token = re.search(r"/([a-zA-Z]+).txt", sys.argv[1]).group(1).upper()

out_json = {}
with open("prices.json") as json_file:
    out_json = json.load(json_file)
    if not contracts["address"].get(token):
        sys.exit(
            "Token doesn't exist in contracts.json. First add token address and abi"
        )

with open(in_data) as file:
    contents = file.read()
    f = contents.split("\n")
    for i in [j * 13 for j in range(0, int(len(f) / 13), 1)]:
        line = [val for val in f[i : i + 13] if val != "\t"]
        line[0] = int(datetime.datetime.strptime(line[0], "%b %d, %Y").timestamp())
        if out_json.get(str(line[0])):
            out_json[str(line[0])][token] = line[4].replace(",", "")
        else:
            out_json[str(line[0])] = {token: line[4].replace(",", "")}

with open("prices.json", "w") as out_file:
    json.dump(out_json, out_file)