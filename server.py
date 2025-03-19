import socket
import select
import threading  # Use threading instead of thread
import sys
import time
import random

# AF_NET is the address of the socket
# SOL_SOCKET means the type of the socket
# SOCK_STREAM means that the data or characters are read in a flow
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Setting up the server details and checks whether proper size of arguments are given
if len(sys.argv) != 3:
    print("Print in the following order: script, IP address, port number")
    exit()

# Allots the first argument of the string as the IP Address
IP_address = str(sys.argv[1])
# Allocates the second argument as the port number
Port = int(sys.argv[2])

# These are the values that the client must be aware about
server.bind((IP_address, Port))
server.listen(100)

list_of_clients = []

Q = [" 1.What is the Italian word for PIE? \n a.Mozarella b.Pasty c.Patty d.Pizza",
     " 2.Water boils at 212 Units at which scale? \n a.Fahrenheit b.Celsius c.Rankine d.Kelvin",
     " 3.Which sea creature has three hearts? \n a.Dolphin b.Octopus c.Walrus d.Seal",
     " 4.Who was the character famous in our childhood rhymes associated with a lamb? \n a.Mary b.Jack c.Johnny d.Mukesh",
     " 5.How many bones does an adult human have? \n a.206 b.208 c.201 d.196",
     " 6.How many wonders are there in the world? \n a.7 b.8 c.10 d.4",
     " 7.What element does not exist? \n a.Xf b.Re c.Si d.Pa",
    ]

A = ['d', 'a', 'b', 'a', 'a', 'a', 'a',]

Count = []
client = ["address", -1]
bzr = [0, 0, 0]  # Buzzer List


def clientthread(conn, addr):
    conn.send(b"Hello Genius!!!\n Welcome to this quiz! Answer any 5 questions correctly before your opponents do\n Press any key on the keyboard as a buzzer for the given question\n")
    # Intro MSG
    while True:
        message = conn.recv(2048)
        if message:
            if bzr[0] == 0:
                client[0] = conn
                bzr[0] = 1
                i = 0
                while i < len(list_of_clients):
                    if list_of_clients[i] == client[0]:
                        break
                    i += 1
                client[1] = i

            elif bzr[0] == 1 and conn == client[0]:
                bol = message[0] == A[bzr[2]][0]
                print(A[bzr[2]][0])
                if bol:
                    broadcast(f"player {client[1] + 1} +1\n\n")
                    Count[i] += 1
                    if Count[i] == 5:
                        broadcast(f"player {client[1] + 1} WON\n")
                        end_quiz()
                        sys.exit()

                else:
                    broadcast(f"player {client[1] + 1} -1\n\n")
                    Count[i] -= 1
                bzr[0] = 0
                if len(Q) != 0:
                    Q.pop(bzr[2])
                    A.pop(bzr[2])
                if len(Q) == 0:
                    end_quiz()
                quiz()

            else:
                conn.send(f" player {client[1] + 1} pressed buzzer first\n\n".encode())
        else:
            remove(conn)





def broadcast(message):
    for clients in list_of_clients:
        try:
            clients.send(message.encode())
        except:
            clients.close()
            remove(clients)


def end_quiz():
    broadcast("Game Over\n")
    bzr[1] = 1
    # Find the player with the maximum score
    i = Count.index(max(Count))
    
    # Broadcast the winner to all players
    broadcast(f"Player {i + 1} wins by scoring {Count[i]} points!")

    # Notify all players of their scores and send a special message to the winner
    for x in range(len(list_of_clients)):
        if x == i:
            list_of_clients[x].send("You won!\n".encode())  # Notify the winning player
        else:
            list_of_clients[x].send(f"You scored {Count[x]} points.".encode())  # Notify the other players

    # Close the server after the game ends
    server.close()



def quiz():
    bzr[2] = random.randint(0, 10000) % len(Q)
    if len(Q) != 0:
        for connection in list_of_clients:
            connection.send(Q[bzr[2]].encode())


def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)


while True:
    conn, addr = server.accept()
    list_of_clients.append(conn)
    Count.append(0)
    print(addr[0] + " connected")
    threading.Thread(target=clientthread, args=(conn, addr)).start()  # Use threading.Thread
    if len(list_of_clients) == 3:
        quiz()

conn.close()
server.close()


