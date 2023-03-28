from time import sleep
from numpy import ones
from datetime import datetime as dt

print("Hello world")
print(ones(10))

with open(r'C:/Users/grung/Desktop/kpltrader/session.log', "w") as file:
    print("writting")
    file.write(dt.now().isoformat())

sleep(5)

# C: \Users\grung\Desktop\kpltrader\traderbot.py
