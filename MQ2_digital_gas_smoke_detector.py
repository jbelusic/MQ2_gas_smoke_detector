from machine import ADC, Pin
import time

print("wait 20 seconds...", end=" ")
for i in range(20, 0, -1):
  print(i, end=",")
  time.sleep(1)

print("start")

gas = Pin(12, Pin.IN) 
while True:
  gas_value = gas.value()
  if gas_value == 1:
    #print("No GAS",gas_value)
    pass                                                                
  else:
    print("Gas!!!!")
  time.sleep(5)
    
print("end")
