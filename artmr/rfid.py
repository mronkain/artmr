import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from datetime import datetime
import logging
import threading

def rfid_handler(controller, screen):
    # logging.setLevel(logging.CRITICAL)
    logging.basicConfig(filename='rfid.log',level=logging.INFO)    
    last_id = 0
    reader = SimpleMFRC522()
    logging.getLogger('mfrc522Logger').setLevel(logging.CRITICAL)
    identifier = str(controller.get_current_competition().id) + controller.get_current_competition().name[:10]
    # logging.warning("starting")
    queue = controller.get_queue()

    try:
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            id, text = reader.read()

            if controller.get_current_competition().startTime == None:
                if not queue.empty():
                    competitor = queue.get_nowait()
                    reader.write(identifier + str(competitor))
                    controller.beep()
                else:
                    controller.read_tag(text[len(identifier):])
            elif id != last_id and text.startswith(identifier):
                competitor = text[len(identifier):]
                split = datetime.now()
                split_id = controller.add_split_competitor(split, competitor)
                if split_id != None: 
                    screen.force_update()
                    last_id = id
            else:
                last_id = None
    finally:
        GPIO.cleanup()

    # logging.warning("stopping")


# if __name__ == '__main__':
#     parent_conn, child_conn = Pipe()
#     identifier = "asdf"
#     p = Process(target=rfid_handler, args=(child_conn,identifier,))
#     p.start()
    
#     while True:
#         print "x to exit, w to write"
#         choice = raw_input("> ")
#         choice = choice.lower() #Convert input to "lowercase"

#         if choice == 'x':
#             print("Good bye.")
#             break

#         if choice == 'w':            
#             print("type name")
#             name = raw_input("> ")
#             parent_conn.send(name)


#         if parent_conn.poll():
#             data = parent_conn.recv()
#             print data
#             #print "%d: %s %s" % data[:id], data[:text], data[:time]

#     p.join()