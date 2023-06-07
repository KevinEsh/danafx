from time import sleep
from numpy import ones
from datetime import datetime as dt

today = dt.now().strftime('%Y-%M-%d')


print("Hello world")
print(ones(10))

with open(f'logs/{today}.log', "w") as file:
    print("writting")
    file.write(dt.now().isoformat())

sleep(5)

# C: \Users\grung\Desktop\kpltrader\traderbot.py >=