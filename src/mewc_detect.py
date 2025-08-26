import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import yaml
import detection.run_detector_batch as run_detector_batch
from lib_common import read_yaml
from lib_command import create_command

config = read_yaml('config.yaml')
for conf_key in config.keys():
    if conf_key in os.environ:
        config[conf_key] = os.environ[conf_key]

md_cmd = create_command(config)
print(md_cmd)
os.system(md_cmd)