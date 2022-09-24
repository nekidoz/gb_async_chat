import socket as sock
import argparse

import settings as sett
import jim

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-address', required=False)
parser.add_argument('-port', required=False)
args = parser.parse_args()
server_address = args.address if args.address else sett.DEFAULT_LISTEN_ADDRESS
server_port = int(args.port) if args.port else sett.DEFAULT_PORT
print(f"Listening on {server_address if server_address else '(all)'}:{server_port}")

# Create and bind a socket and listed to connections
socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
socket.bind((server_address, server_port))
socket.listen()

# Process client messages
while True:
    connection, address = socket.accept()
    message = jim.Message.from_str(connection.recv(jim.MAX_JIM_LEN).decode(sett.DEFAULT_ENCODING))
    print(f'Сообщение от {address}: ', message.json)
    if message.action == jim.Actions.PRESENCE:
        response = jim.Response(**jim.Responses.OK.response).json
    else:
        response = jim.Response(**jim.Responses.BAD_REQUEST.response).json
    connection.send(response.encode(sett.DEFAULT_ENCODING))
    connection.close()
