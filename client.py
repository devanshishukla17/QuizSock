import socket
import select
import sys
import threading

# Function to send messages to the server
def send_messages(server_socket):
    while True:
        message = sys.stdin.readline()  # Read input from the user
        server_socket.send(message.encode())  # Send message to the server
        sys.stdout.flush()  # Flush the output buffer

# Function to receive messages from the server
def receive_messages(server_socket):
    while True:
        message = server_socket.recv(2048).decode()  # Receive messages from the server
        if message:
            print(message)  # Print the message

# Initialize the socket connection
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if len(sys.argv) != 3:
    print("Usage: python client.py <IP Address> <Port>")
    exit()

IP_address = str(sys.argv[1])
Port = int(sys.argv[2])

server.connect((IP_address, Port))

# Start a thread to handle sending messages
send_thread = threading.Thread(target=send_messages, args=(server,))
send_thread.start()

# Start a thread to handle receiving messages
receive_thread = threading.Thread(target=receive_messages, args=(server,))
receive_thread.start()

# Wait for the threads to finish (they won't, but this prevents the main thread from exiting)
send_thread.join()
receive_thread.join()

server.close()
