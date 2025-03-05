import logging
import time
from .navigator import Navigator

if __name__ == "__main__":
    
    with Navigator() as nav:
        try:
            logging.info("Initializing test sequence...")
            time.sleep(1)

            logging.info("Rotating 360 degrees...")
            nav.rotate(360, speed=80)
            time.sleep(0.5)

            # Forward movement test sequence
            logging.info("Initializing forward movement test sequence...")
            time.sleep(1)
            logging.info("Moving forward with PID alignment...")
            nav.forward(duration=1, speed=100)
            time.sleep(0.5)
            logging.info("Rotating 180 degrees...")
            nav.rotate(180, speed=80)
            time.sleep(0.5)
            logging.info("Moving forward with PID alignment...")
            nav.forward(duration=1, speed=100)
            time.sleep(0.5)

            time.sleep(1)

            # Backward movement test sequence
            logging.info("Initializing backward movement test sequence...")
            time.sleep(1)
            logging.info("Rotating 360 degrees...")
            nav.rotate(360, speed=100)
            time.sleep(0.5)
            time.sleep(1)
            logging.info("Moving backward with PID alignment...")
            nav.backward(duration=1, speed=100)
            time.sleep(0.5)
            logging.info("Rotating 180 degrees...")
            nav.rotate(180, speed=80)
            time.sleep(0.5)
            logging.info("Moving backward with PID alignment...")
            nav.backward(duration=1, speed=100)
            time.sleep(0.5)

            time.sleep(1)
            logging.info("Test sequence completed!")
        
        except KeyboardInterrupt:
            logging.info("Test sequence ended by user")
        except Exception as ex:
            logging.error("Unexpected error: %s", ex)
