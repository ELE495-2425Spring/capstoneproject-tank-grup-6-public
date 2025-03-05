from navtools import Navigator
from sigtools import SDRModule
from time import sleep
import logging
import numpy

logging.disable(logging.CRITICAL)

try:
	with SDRModule(gain=30) as sig:
		with Navigator() as nav:

			sig.start_monitoring(False, interval=0.01)

			while 1:
				powers = []

				for i in range(12):
					print(f"i: {i} {sig.latest_power_dbm}")
					if sig.latest_power_dbm > 3.563:
						raise KeyboardInterrupt
					powers.append(sig.latest_power_dbm)
					nav.rotate(20, 80, rotation = "Left")
				
				powers = numpy.array(powers)
				index = 11-powers.argmax()

				print(f"Max index at: {11-index}")

				if(index > 0):
					for i in range(index+1):
						nav.rotate(20, 80, rotation = "Right")

				nav.forward(2, 90)

				if powers.max() > 3.563:
					break


except KeyboardInterrupt:
	pass
finally:
	pass