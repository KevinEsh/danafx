import json
import os
import mt5_interface
import strategy
import time


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
    login_settings = get_settings(".settings/demo/login_settings.json")
    trading_settings = get_settings(".settings/demo/trading_settings.json")
    # Start MT5
    mt5_interface.start_mt5(login_settings)
    # Initialize symbols
    mt5_interface.initialize_symbols(trading_settings)
    # Select symbol to run strategy on
    symbol_for_strategy = project_settings['symbols'][0]
    # Set up a previous time variable
    previous_time = 0
    # Set up a current time variable
    current_time = 0
    # Start a while loop to poll MT5
    while True:
        # Retrieve the current candle data
        candle_data = mt5_interface.query_historic_data(
            symbol=symbol_for_strategy,
            timeframe=project_settings['timeframe'], 
            number_of_candles=1
            )
        # Extract the timedata
        current_time = candle_data[0][0]
        # Compare against previous time
        if current_time != previous_time:
            # Notify user
            print("New Candle")
            # Update previous time
            previous_time = current_time
            # Retrieve previous orders
            orders = mt5_interface.get_open_orders()
            # Cancel orders
            for order in orders:
                mt5_interface.cancel_order(order)
            # Start strategy one on selected symbol
            strategy.strategy_one(symbol=symbol_for_strategy, timeframe=project_settings['timeframe'],
                                  pip_size=project_settings['pip_size'])
        else:
            # Get positions
            positions = mt5_interface.get_open_positions()
            # Pass positions to update_trailing_stop
            for position in positions:
                strategy.update_trailing_stop(order=position, trailing_stop_pips=10,
                                              pip_size=project_settings['pip_size'])
        time.sleep(0.1)
