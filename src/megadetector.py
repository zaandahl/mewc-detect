import os
import yaml
import detection.run_tf_detector_batch as run_tf_detector_batch

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

config = read_yaml('config.yaml')
for conf_key in config.keys():
    if conf_key in os.environ:
        config[conf_key] = os.environ[conf_key]

if(config["RECURSIVE"]): recursive_str = "--recursive"
else: recursive_str = ""
if(config["RELATIVE_FILENAMES"]): rel_filename_str = "--output_relative_filenames"
else: rel_filename_str = ""
threshold_str = " --threshold=" + str(config["THRESHOLD"])
checkpoint_freq_str = " --checkpoint_frequency=" + str(config["CHECKPOINT_FREQ"])
if(config["CHECKPOINT_FILE"] is not None): res_checkpoint_str = "--resume_from_checkpoint " + config["CHECKPOINT_FILE"]
else: res_checkpoint_str = ""
if(config["NCORES"] is not None): ncores_str = "--ncores " + config["NCORES"]

detector_file_str = " /code/" + str(config["MD_MODEL"]) + " "
image_file_str = str(config["INPUT_DIR"]) + "/" + str(config["IMG_FILE"]) + " "
output_file_str = str(config["INPUT_DIR"]) + "/" + str(config["MD_FILE"])

md_cmd = "python /code/cameratraps/detection/run_tf_detector_batch.py " + \
recursive_str + \
rel_filename_str + \
threshold_str + \
checkpoint_freq_str + \
res_checkpoint_str + \
ncores_str + \
detector_file_str + \
image_file_str + \
output_file_str

os.system(md_cmd)