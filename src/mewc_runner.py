import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import yaml
from lib_command import create_command

def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = read_yaml('config.yaml')
for conf_key in config.keys():
    if conf_key in os.environ:
        config[conf_key] = os.environ[conf_key]

md_cmd = create_command(config)
print(md_cmd)
os.system(md_cmd)
