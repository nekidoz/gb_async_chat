import socket as sock
import argparse

import settings as sett
import jim

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('address', nargs='?', default=None)
parser.add_argument('port', nargs='?', default=None)
args = parser.parse_args()
server_address = args.address if args.address else sett.DEFAULT_SERVER_ADDRESS
server_port = int(args.port) if args.port else sett.DEFAULT_PORT
print(f"Connecting to {server_address if server_address else '(broadcast)'}:{server_port}")

socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
socket.connect((sett.DEFAULT_SERVER_ADDRESS, sett.DEFAULT_PORT))
message = jim.Message(action=jim.Actions.PRESENCE, type="status",
                      user={
                          "account_name": "test",
                          "status": "Online"
                      }
                      )
socket.send(message.json.encode(sett.DEFAULT_ENCODING))
response = jim.Response.from_str(socket.recv(jim.MAX_JIM_LEN).decode(sett.DEFAULT_ENCODING))
print(f'Сообщение от сервера: ', response.json)
if response.response == jim.Responses.OK:
    print("Message acknowledged")
else:
    print(f"Unexpected return code: {response.response}")
socket.close()
