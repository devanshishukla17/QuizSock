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
player_count = 0 
players = {}  
clients = [] 
correct_answers = 0  

def clientthread(conn, addr):
    global player_count, players, correct_answers

    # Increment the player count and assign a new player number
    player_count += 1
    player_id = player_count
    players[conn] = player_id
    clients.append(conn)  # Add this connection to the clients list

    # Send a welcome message to the player
    conn.send(f"Welcome Player {player_id}!\n".encode())
    conn.send("Hello Genius!!!\n".encode())
    conn.send("Welcome to this quiz! Answer any 5 questions correctly before your opponents do.\n".encode())
    conn.send("Press any key on the keyboard as a buzzer for the given question.\n".encode())

    # Original quiz logic: Iterate over questions
    question_index = 0  # Track which question to ask
    total_questions = len(Q)  # Number of questions available

    while question_index < total_questions:
        try:
            # Send the next question to all players (broadcast)
            question = Q[question_index]
            broadcast(f"Question {question_index + 1}: {question}\n")

            # Receive buzzer response from players
            buzzer = conn.recv(1024).decode()

            if buzzer:
                broadcast(f"Player {player_id} pressed the buzzer first!\n")

                # Ask for the player's answer
                conn.send("What's your answer?\n".encode())
                player_answer = conn.recv(1024).decode().strip()

                # Check the player's answer against the correct answer
                if player_answer.strip().lower() == A[question_index].strip().lower():
                    correct_answers += 1
                    conn.send("Correct answer!\n".encode())
                else:
                    conn.send("Wrong answer!\n".encode())

                # Move to the next question
                question_index += 1

                # Check if the player has won
                if correct_answers == 5:
                    broadcast(f"Player {player_id} has won the quiz!\n")
                    break
            else:
                remove(conn)  # Remove player if no buzzer input
        except:
            continue

    # End the quiz when all questions are answered
    if question_index == total_questions:
        broadcast("The quiz has ended!\n")


# Broadcast function to send messages to all connected players
def broadcast(message):
    for client in clients:
        try:
            client.send(message.encode())
        except:
            remove(client)

# Remove player from the game when they disconnect
def remove(conn):
    if conn in clients:
        clients.remove(conn)

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


