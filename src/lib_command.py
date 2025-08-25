import shlex


def as_bool(x):
    """Interpret booleans from YAML/env robustly.
    Accepts: true/false/1/0/yes/no (case-insensitive), bools, and ints.
    Any unrecognized value is treated as False.
    """
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    if isinstance(x, (int, float)):
        return bool(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"true", "t", "yes", "y", "1"}:
            return True
        if s in {"false", "f", "no", "n", "0"}:
            return False
        # Back-compat: explicit 'True'/'False' strings
        if s == "true":
            return True
        if s == "false":
            return False
    return False


def _is_unset(val):
    """Treat None or empty-string (after strip) as unset."""
    return val is None or (isinstance(val, str) and val.strip() == "")


def create_command(config):
    # Flags from booleans (support YAML/native bools and string env overrides)
    recursive_str = " --recursive" if as_bool(config.get("RECURSIVE")) else ""
    rel_filename_str = (
        " --output_relative_filenames" if as_bool(config.get("RELATIVE_FILENAMES")) else ""
    )
    quiet_str = " --quiet" if as_bool(config.get("QUIET")) else ""
    image_queue_str = " --use_image_queue" if as_bool(config.get("IMAGE_QUEUE")) else ""

    # Thresholds stay as floats; stringify without formatting changes
    threshold_str = " --threshold=" + str(config["THRESHOLD"])
    checkpoint_freq_str = " --checkpoint_frequency=" + str(config["CHECKPOINT_FREQ"])

    # Optional args: treat empty strings as unset
    if not _is_unset(config.get("CHECKPOINT_FILE")):
        res_checkpoint_str = " --resume_from_checkpoint " + shlex.quote(str(config["CHECKPOINT_FILE"]))
    else:
        res_checkpoint_str = ""

    if not _is_unset(config.get("NCORES")):
        ncores_str = " --ncores " + str(config["NCORES"])
    else:
        ncores_str = ""

    # Support model name (package-resolved) or explicit file path
    model = str(config["MD_MODEL"]) if config.get("MD_MODEL") is not None else ""

    # Short names to always treat as model names (never file paths)
    short_names = {
        "mdv5a",
        "mdv5b",
        "mdv1000-redwood",
        "mdv1000-cedar",
        "mdv1000-spruce",
    }

    lower_model = model.strip().lower()
    looks_like_file = (
        lower_model.endswith((".pt", ".pb")) or ("/" in model) or ("\\" in model)
    )
    treat_as_name = (lower_model in short_names) or not looks_like_file

    if treat_as_name:
        detector_file_str = " " + model.strip() + " "
    else:
        # Quote an explicit file path; legacy behavior expects under /code
        detector_file_str = " " + shlex.quote("/code/" + model.strip()) + " "

    # Input path: directory or a specific file under it
    input_dir = str(config["INPUT_DIR"]).rstrip("/\\")
    if not _is_unset(config.get("IMG_FILE")):
        img_file = str(config["IMG_FILE"]).lstrip("/\\")
        image_path = f"{input_dir}/{img_file}"
    else:
        image_path = input_dir
    image_file_str = " " + shlex.quote(image_path) + " "

    # Output path always under input dir
    output_file = f"{input_dir}/" + str(config["MD_FILE"]).lstrip("/\\")
    output_file_str = shlex.quote(output_file)

    md_cmd = (
        "python -m megadetector.detection.run_detector_batch"
        + recursive_str
        + rel_filename_str
        + quiet_str
        + image_queue_str
        + threshold_str
        + checkpoint_freq_str
        + res_checkpoint_str
        + ncores_str
        + detector_file_str
        + image_file_str
        + output_file_str
    )
    return md_cmd
