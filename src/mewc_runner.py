"""Container entrypoint that preserves detector failures."""
import os
from pathlib import Path
import shlex
import subprocess
import sys
import yaml
from lib_command import create_command


def main(config_path=None):
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
    try:
        with open(config_path or Path(__file__).with_name('config.yaml'), encoding='utf-8') as stream:
            config = yaml.safe_load(stream)
        if not isinstance(config, dict):
            raise ValueError('Configuration must be a YAML mapping')
        config.update({key: os.environ[key] for key in config if key in os.environ})
        argv = create_command(config)
        print(shlex.join(argv), flush=True)
        returncode = subprocess.run(argv, check=False).returncode
        if returncode:
            print(f'MegaDetector failed with exit status {returncode}', file=sys.stderr)
        return returncode if returncode >= 0 else 128 - returncode
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        print(f'MegaDetector configuration/launch failed: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
