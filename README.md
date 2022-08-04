# megadetector
Docker container for MegaDetector

The following environment variables are supported for configuration:

| variable | default | description |
------------------------------------
| INPUT_DIR | "/images/" | A mounted volume containing images to process |
| MD_MODEL | "md_v4.1.0.pb" | The MegaDetector model file (can be overridden under /code) |
| IMG_FILE | "" | A specific image filename to process. Empty means process entire directory |
| MD_FILE | "md_out.json" | MegaDetector output file, will write to INPUT_DIR |
| RECURSIVE | True | Recursive processing |
| RELATIVE_FILENAMES | True | Use relative filenames |
| THRESHOLD | 0.01 | MegaDetector threshold |
| CHECKPOINT_FREQ | 100 | Checkpoint frequency |
| CHECKPOINT_FILE | None | File to resume checkpointing from under INPUT_DIR |
| NCORES | None | Number of CPU cores if GPU processing is unavailable |
