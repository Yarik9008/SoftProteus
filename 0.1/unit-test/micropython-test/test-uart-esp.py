<<<<<<< HEAD
from machine import UART

uart1 = UART(2, baudrate=9600, tx=17, rx=16)
uart1.write('hello')  # write 5 bytes
data = uart1.read(5)
print(data)  # read up to 5 byteson_options_press
=======
from machine import UART

uart1 = UART(2, baudrate=9600, tx=17, rx=16)
uart1.write('hello')  # write 5 bytes
data = uart1.read(5)
print(data)  # read up to 5 byteson_options_press
>>>>>>> 60636f8cf41ce6ed7954913253b849bfe73c69ce
