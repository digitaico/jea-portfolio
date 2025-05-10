import os

def get_project_root_path(current_file_path=None):
    """
    Walks up the directory tree from current_file_path to find the project root.
    Assumes the project root is the directory containing both a 'config' and a 'src' subdirectory.
    If current_file_path is None, uses the path of this file (file_utils.py).
    """
    if current_file_path is None:
        # Use the path of the current file (file_utils.py) as a starting point
        start_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        start_dir = os.path.dirname(os.path.abspath(current_file_path))

    current_dir = start_dir
    while True:
        # Check if the current directory contains the 'config' and 'src' subdirectories
        if os.path.exists(os.path.join(current_dir, 'config')) and \
           os.path.exists(os.path.join(current_dir, 'src')):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir: # Reached filesystem root or infinite loop
            raise Exception(
                f"Project root not found. Looked up from {start_dir}. "
                "'config' and 'src' directories not found in parent directories."
            )
        current_dir = parent_dir

def get_config_filepath(config_filename):
    """
    Constructs the absolute path to a configuration file within the 'config' directory
    located at the project root. This function assumes it's called from within the 'src' directory.
    """
    # Use the path of the calling module to find the project root
    # In this case, if called from config.py in src, it will use config.py's path
    # to determine the root.
    project_root = get_project_root_path()
    config_dir = os.path.join(project_root, 'config')
    return os.path.join(config_dir, config_filename)