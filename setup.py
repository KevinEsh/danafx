import json
import os
from ktrader import KTrader


# Function to import settings from settings.json
def get_settings(filepath: str) -> dict[str, str]:
    # Test the filepath to sure it exists
    if not os.path.exists(filepath):
        raise ImportError(f"{filepath} path does not exist")

    # Open the file and get the information from file
    with open(filepath, "r") as file:
        project_settings = json.load(file)

    return project_settings


# Main function
if __name__ == '__main__':
    # Import project settings
    login_settings = get_settings("settings/demo/login.json")
    trading_settings = get_settings("settings/demo/trading.json")

    trader = KTrader()

    # Start MT5
    trader.start_session(login_settings)
