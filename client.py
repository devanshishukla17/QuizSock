import socket
import select
import sys
import threading
import time
import ssl

# Flag to control thread execution
running = True

# Function to send messages to the server
def send_messages(server_socket):
    global running
    try:
        while running:
            message = input()  # Read input from the user
            if message and running:
                try:
                    server_socket.send(message.encode())  # Send message to the server
                except:
                    print("Connection to server lost.")
                    running = False
                    break
    except:
        running = False

# Function to receive messages from the server
def receive_messages(server_socket):
    global running
    try:
        while running:
            try:
                print("Waiting to receive a message...")
                message = server_socket.recv(2048).decode()  # Receive messages from the server
                if not message:
                    print("Server disconnected.")
                    running = False
                    break
                else:
                    print(message)  # Print the message
            except:
                if running:
                    print("Connection to server lost.")
                    running = False
                break
    except:
        running = False

# Main function to handle connection and manage threads
def main():
    global running

    if len(sys.argv) != 3:
        print("Usage: python client.py <IP Address> <Port>")
        exit()

    IP_address = str(sys.argv[1])
    Port = int(sys.argv[2])

    try:
        # Create a raw socket
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Create an SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # For testing only

        # Wrap the socket with SSL
        server = context.wrap_socket(raw_socket, server_hostname=IP_address)

        # Connect to server
        server.settimeout(5)
        try:
            server.connect((IP_address, Port))
            print("Client connected, waiting for server message...")
            server.settimeout(None)  # Reset timeout after connection
        except socket.timeout:
            print("Connection timed out. Server may be unavailable.")
            return
        except ConnectionRefusedError:
            print("Connection refused. Server may not be running.")
            return
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return

        print(f"Connected securely to {IP_address}:{Port}")

        # Start threads
        send_thread = threading.Thread(target=send_messages, args=(server,))
        send_thread.daemon = True
        send_thread.start()

        receive_thread = threading.Thread(target=receive_messages, args=(server,))
        receive_thread.daemon = True
        receive_thread.start()

        # Main thread waits and monitors threads
        while running and (send_thread.is_alive() or receive_thread.is_alive()):
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        running = False
        try:
            server.close()
        except:
            pass

        print("Disconnected from server.")

if __name__ == "__main__":
    main()
