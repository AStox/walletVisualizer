import sys
import json
import datetime
from dateutil.parser import parse

in_data = sys.argv[1]
token = sys.argv[2]

print(token)
print(datetime.datetime.strptime("Oct 1, 2020", "%b %d, %Y").timestamp())
out_json = {}
with open("prices.json") as json_file:
    out_json = json.load(json_file)
    if not out_json[list(out_json.keys())[0]].get(token):
        sys.exit("Token doesn't exist in prices.json")

with open(in_data) as file:
    contents = file.read()
    f = contents.split("\n")
    for i in [j * 13 for j in range(0, int(len(f) / 13), 1)]:
        line = [val for val in f[i : i + 13] if val != "\t"]
        line[0] = int(datetime.datetime.strptime(line[0], "%b %d, %Y").timestamp())
        out_json[line[0]] = {token: line[4]}

with open("prices.json", "w") as out_file:
    json.dump(out_json, out_file)