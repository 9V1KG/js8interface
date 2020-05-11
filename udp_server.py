"""
    Modul to interface with JS8call program using
    UDP server on port 2237
    Author: 9V1KG, Klaus D. Goepel
"""
import socket
import json
import sys
import select
import queue


SERVER = socket.gethostbyname("localhost")
PORT = 2237  # used by JS8 and WSJTX
ADDR = (SERVER, PORT)
BUFFER = 1024

seq = 0  # message sequence number


def process_kbd_in(line_in: str) -> bytes:
    """
    Process keyboard input line
    :param line_in: keyboard input
    :return: byte string to be sent to UDP client
    """
    global seq
    print(f"Keyboard: {line_in}")
    if "send" in line_in:
        msg_to = input("To (call sign): ")
        # todo check call sign
        msg_to = msg_to.ljust(9)
        msg_txt = input("Message: ")
        # todo check length
        seq += 1
        aprs_msg = f"@APRSIS CMD :{msg_to}:{msg_txt}" \
                   + "{" + format(seq, '02d') + "}"
        # type TX.SET_TEXT and TX.SEND_MESSAGE
        msg_js = {
            "params": {},
            "type": "TX.SEND_MESSAGE",
            "value": aprs_msg
        }
        byts = bytes(repr(msg_js).replace("'", "\""), "utf-8")
        return byts
    return b''


# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind(ADDR)  # Bind to address and ip - use try
print(f"UDP server up and listening on {ADDR}")

inputs = [sys.stdin, UDPServerSocket]  # Sockets from which we expect to read
outputs = [UDPServerSocket]  # Sockets to which we expect to write
message_queues = {}  # Outgoing message queues (socket:Queue)
address = None, None

while inputs:
    while sys.stdin in select.select(inputs, outputs, [], 0)[0]:
        line = sys.stdin.readline()
        if line and "send" in line:
            b_str = process_kbd_in(line)
            if len(b_str) > 0:
                UDPServerSocket.sendto(b_str, address)

    while UDPServerSocket in select.select(inputs, outputs, [], 0)[0]:
        message, address = UDPServerSocket.recvfrom(BUFFER)

        clientMsg = message.decode("utf-8")
        clientIP = f"Client IP Address:{address}"

        msg = json.loads(clientMsg)
        if msg['type'] != "PING" and msg['type'] != "TX.FRAME":
            print(clientIP)
            print(json.dumps(msg, indent=4))
