from json import load
from os.path import exists


def get_settings(filepath: str) -> dict[str, str]:
    """Open a .json file to load the setting values

    Args:
        filepath (str): JSON file with the configuration of variables

    Raises:
        ImportError: File does not exit

    Returns:
        dict[str, str]: JSON file converted to dict
    """
    # Test the filepath to sure it exists
    if not exists(filepath):
        raise ImportError(f"{filepath} path does not exist")

    # Open the file and get the information from file
    with open(filepath, "r") as file:
        settings = load(file)

    return settings
