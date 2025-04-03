import socket
import select
import threading
import sys
import time
import random

# Global Constants
BUFFER_SIZE = 2048
MIN_PLAYERS = 2
MAX_SCORE_TO_WIN = 5
QUESTION_DELAY = 2

# Game data
Q = [" 1.What is the Italian word for PIE? \n a.Mozarella b.Pasty c.Patty d.Pizza",
     " 2.Water boils at 212 Units at which scale? \n a.Fahrenheit b.Celsius c.Rankine d.Kelvin",
     " 3.Which sea creature has three hearts? \n a.Dolphin b.Octopus c.Walrus d.Seal",
     " 4.Who was the character famous in our childhood rhymes associated with a lamb? \n a.Mary b.Jack c.Johnny d.Mukesh",
     " 5.How many bones does an adult human have? \n a.206 b.208 c.201 d.196",
     " 6.How many wonders are there in the world? \n a.7 b.8 c.10 d.4",
     " 7.What element does not exist? \n a.Xf b.Re c.Si d.Pa",
    ]

A = ['d', 'a', 'b', 'a', 'a', 'a', 'a']

# Global variables
clients = []  # List of client connections
players = {}  # {socket: player_id}
player_scores = {}  # {socket: score}
player_count = 0
answered_questions = set()
current_question_index = -1
question_active = False
answering_player = None
game_started = False
game_lock = threading.Lock()

def clientthread(conn, addr):
    global player_count, players, current_question_index, answering_player, game_started, question_active
    
    with game_lock:
        # Register new player
        player_count += 1
        player_id = player_count
        players[conn] = player_id
        clients.append(conn)
        player_scores[conn] = 0
        
        # Send welcome messages
        try:
            conn.send(f"Welcome Player {player_id}!\n".encode())
            conn.send("Hello Genius!!!\n".encode())
            conn.send("Welcome to this quiz! Answer any 5 questions correctly before your opponents do.\n".encode())
            conn.send("Press any key on the keyboard as a buzzer for the given question.\n".encode())
        except:
            remove(conn)
            return
        
        # Start game if enough players
        if len(clients) >= MIN_PLAYERS and not game_started:
            game_started = True
            threading.Thread(target=start_game, daemon=True).start()
    
    # Main loop to handle client messages
    while True:
        try:
            # Wait for client message
            message = conn.recv(BUFFER_SIZE).decode().strip()
            
            if not message:
                # Client disconnected
                break
                
            with game_lock:
                # Only process if game is active and client is in players list
                if question_active and answering_player is None and conn in players:
                    # Register this player as the answering player
                    answering_player = conn
                    player_id = players[conn]
                    
                    # Notify all players
                    broadcast(f"Player {player_id} pressed the buzzer first!\n")
                    
                    # Ask for answer
                    conn.send("What's your answer? (a, b, c, or d)\n".encode())
                elif answering_player == conn and conn in players:
                    # This is the answer from the player who pressed the buzzer
                    answer = message.lower()
                    correct_answer = A[current_question_index].strip().lower()
                    player_id = players[conn]
                    
                    # Check answer
                    if answer == correct_answer:
                        player_scores[conn] += 1
                        broadcast(f"Player {player_id} answered correctly! Their score is now {player_scores[conn]}.\n")
                    else:
                        broadcast(f"Player {player_id} answered incorrectly! The correct answer was {correct_answer}.\n")
                    
                    # Mark question as answered
                    answered_questions.add(current_question_index)
                    
                    # Check if player won
                    if player_scores[conn] >= MAX_SCORE_TO_WIN:
                        broadcast(f"Game Over! Player {player_id} wins with {player_scores[conn]} correct answers!\n")
                        reset_game()
                    else:
                        # Reset state for next question
                        question_active = False
                        answering_player = None
                        
                        # Schedule next question with delay
                        threading.Thread(target=lambda: ask_next_question_with_delay(), daemon=True).start()
        except Exception as e:
            print(f"Error handling client: {e}")
            break
    
    # Client disconnected or error occurred
    remove(conn)

def start_game():
    time.sleep(1)
    broadcast("\nThe quiz is starting now!\n")
    time.sleep(1)
    ask_next_question()

def ask_next_question_with_delay():
    # Wait before asking next question
    time.sleep(QUESTION_DELAY)
    ask_next_question()

def ask_next_question():
    global current_question_index, question_active, answering_player
    
    with game_lock:
        # Reset answering player
        answering_player = None
        
        # Check if we have any clients
        if len(clients) == 0:
            return
            
        # Find available questions
        available_questions = [i for i in range(len(Q)) if i not in answered_questions]
        
        if available_questions:
            # Select random question
            current_question_index = random.choice(available_questions)
            question_text = Q[current_question_index]
            
            # Send question to all clients
            broadcast(f"\nNew Question: {question_text}\n")
            
            # Mark question as active
            question_active = True
        else:
            # All questions answered, determine winner
            determine_winner()

def determine_winner():
    # Find player with highest score
    max_score = -1
    winner = None
    
    for conn, score in player_scores.items():
        if conn in clients and score > max_score:
            max_score = score
            winner = conn
    
    if winner and winner in players:
        winner_id = players[winner]
        broadcast(f"All questions have been answered! Player {winner_id} wins with {max_score} points!\n")
    else:
        broadcast("Game ended with no clear winner.\n")
    
    reset_game()

def broadcast(message):
    # Send message to all connected clients
    disconnected_clients = []
    
    for client in list(clients):
        try:
            client.send(message.encode())
        except:
            disconnected_clients.append(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        remove(client)

def remove(conn):
    with game_lock:
        if conn in clients:
            clients.remove(conn)
            
            if conn in players:
                player_id = players[conn]
                broadcast(f"Player {player_id} has disconnected.\n")
                
                # Clean up player data
                del players[conn]
                if conn in player_scores:
                    del player_scores[conn]
                
                # Reset game state if this was answering player
                if answering_player == conn:
                    answering_player = None
                    question_active = False
                    # Ask next question if game still active
                    if game_started and len(clients) >= MIN_PLAYERS:
                        threading.Thread(target=lambda: ask_next_question_with_delay(), daemon=True).start()
            
            # Close connection
            try:
                conn.close()
            except:
                pass
            
            # Check if game should continue
            if len(clients) < MIN_PLAYERS and game_started:
                broadcast(f"Not enough players. Waiting for more players to join...\n")
                reset_game()

def reset_game():
    global game_started, current_question_index, question_active, answering_player, answered_questions
    
    with game_lock:
        game_started = len(clients) >= MIN_PLAYERS
        current_question_index = -1
        question_active = False
        answering_player = None
        answered_questions = set()

# Initialize server
if len(sys.argv) != 3:
    print("Usage: python server.py <IP address> <Port>")
    sys.exit(1)

IP_address = str(sys.argv[1])
Port = int(sys.argv[2])

# Setup socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server.bind((IP_address, Port))
    server.listen(100)
    print(f"Server started on {IP_address}:{Port}")
    print(f"Waiting for {MIN_PLAYERS} players to connect...")

    # Main server loop
    while True:
        try:
            conn, addr = server.accept()
            print(f"{addr[0]} connected")
            threading.Thread(target=clientthread, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nServer shutting down...")
            break
        except Exception as e:
            print(f"Error accepting connection: {e}")
            
except Exception as e:
    print(f"Error setting up server: {e}")
finally:
    # Clean up
    for client in clients[:]:
        try:
            client.close()
        except:
            pass
    server.close()
    print("Server shut down.")