def create_command(config):
    if(config["RECURSIVE"] == 'True'): recursive_str = " --recursive"
    else: recursive_str = ""
    if(config["RELATIVE_FILENAMES"] == 'True'): rel_filename_str = " --output_relative_filenames"
    else: rel_filename_str = ""
    if(config["QUIET"] == 'True'): quiet_str = " --quiet"
    else: quiet_str = ""
    if(config["IMAGE_QUEUE"] == 'True'): image_queue_str = " --use_image_queue"
    else: image_queue_str = ""
    threshold_str = " --threshold=" + str(config["THRESHOLD"])
    checkpoint_freq_str = " --checkpoint_frequency=" + str(config["CHECKPOINT_FREQ"])
    if(config["CHECKPOINT_FILE"] is not None): res_checkpoint_str = " --resume_from_checkpoint " + config["CHECKPOINT_FILE"]
    else: res_checkpoint_str = ""
    if(config["NCORES"] is not None): ncores_str = " --ncores " + config["NCORES"]
    else: ncores_str = ""
    detector_file_str = " /code/" + str(config["MD_MODEL"]) + " "
    if(config["IMG_FILE"] is not None): image_file_str = str(config["INPUT_DIR"]) + "/" + str(config["IMG_FILE"]) + " "
    else: image_file_str = str(config["INPUT_DIR"]) + " "
    output_file_str = str(config["INPUT_DIR"]) + "/" + str(config["MD_FILE"])

    md_cmd = "python /code/cameratraps/detection/run_detector_batch.py " + \
    recursive_str + \
    rel_filename_str + \
    quiet_str + \
    image_queue_str + \
    threshold_str + \
    checkpoint_freq_str + \
    res_checkpoint_str + \
    ncores_str + \
    detector_file_str + \
    image_file_str + \
    output_file_str
    return(md_cmd)