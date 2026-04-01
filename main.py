from generate import generate
import json

with open("config.json") as f:
    config = json.load(f)
    generate(config)

