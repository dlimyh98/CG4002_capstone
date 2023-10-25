import threading
import queue
import json
import logging
import asyncio

# constants for received messages
# this should expand to player 1 and 2 later
VEST = 4
GUN = 5

possible_actions = ["gun", "shield", "reload", "web", "grenade",
                    "portal", "punch", "hammer", "spear", "logout"]


class Player:
    maxHealth = 100
    maxShield = 30
    maxBullets = 6
    maxShields = 3
    maxGrenades = 2

    def __init__(self):
        self.currentHealth = self.maxHealth
        self.currentShield = 0
        self.currentBullets = self.maxBullets
        self.currentShields = self.maxShields
        self.currentGrenades = self.maxGrenades
        self.deaths = 0
        self.isShieldActive = False

    def respawn(self):
        self.currentHealth = self.maxHealth
        self.currentShield = 0
        self.currentBullets = self.maxBullets
        self.currentShields = self.maxShields
        self.currentGrenades = self.maxGrenades
        self.isShieldActive = False

class GameEngine:
    def __init__(self):
        # input queues
        self.gun_input_queue = queue.Queue() # data from gun
        self.vest_input_queue = queue.Queue() # data from vest
        self.action_input_queue = queue.Queue() # data from AI
        self.eval_client_input_queue = queue.Queue() # data from eval client

        # output queues
        self.eval_client_output_queue = queue.Queue()
        self.relay_node_server_output_queue = queue.Queue() 

        self.player1 = Player()
        self.player2 = Player()

        self.loop = None

    # Thread 1: for gun + vest confirmation
    # gun and vest should have different queue
    def gun_vest_processing_thread(self):
        """
        Handles incoming gun and vest packets. When a gun packet is received, wait for a vest packet.

        Update game state according to hit or miss, and send data to Visualizer + Eval Client
        """
        while True:
            if not self.gun_input_queue.empty():
                # this message should be a tuple
                # can catch exception if not tuple
                gun_message = self.gun_input_queue.get()

                try:
                    # wait for a packet from the vest queue
                    vest_message = self.vest_input_queue.get(block=True, timeout=0.02)

                    # deduct target player HP, reduce bullet count

                    # send packet to visualizer to say hit
                    # send updated game state + action to eval client

                except queue.Empty:
                    # classify as miss
                    # send packet to visualizer to say miss
                    # send updated game state + action to eval client
                    return

                # clear both queues?

    
    # Thread 2: for incoming action from AI
    def action_processing_thread(self):
        """
        Handles incoming action from AI. Depending on action, wait for a confirmation from the Visualizer, or
        directly update the game state and send to Eval Client.
        """
        while True:
            if not self.action_input_queue.empty():
                action = self.action_input_queue.get()
                if action in possible_actions:
                    # if utility, update game state

                    # else, send a packet to visualizer and wait for confirmation

                # send game state + action to eval client
        
                    return
        
    # Thread 3: waiting for a message from eval client
    def game_state_processing_thread(self):
        """
        Handles incoming game state from Eval Client (from Eval Server).

        Update the game state and extract relevant information to send to Relay Node Server.
        """
        while True:
            if not self.eval_client_input_queue.empty():
                game_state = self.eval_client_input_queue.get()

                # update game state

                # send back player HP and bullet count back to Relay Node server

    
    # insert all utility functions here
    # should we follow GameState.py's implementation, or week 9 game engine?
    def handle_shot(self, player_id):
        """
        Handle when the gun is fired. This should be called regardless of a hit or miss.
        """
        acting_player = self.player1 if player_id == 1 else self.player2

        if acting_player.currentBullets <= 0:
            logging.info(f"[GameEngine]: Player {acting_player} has no bullets.")
            return
        acting_player.currentBullets -= 1

    def update_game_state(self, game_state_data):
        """
        Update game state.

        This method assumes game_state_data follows the Eval Server packet format.
        """
        player1_data = game_state_data['p1']
        player2_data = game_state_data['p2']

        for attr, value in player1_data.items():
            setattr(self.player1, attr, value)

        for attr, value in player2_data.items():
            setattr(self.player2, attr, value) 

        logging.info("[GameEngine]: Game state updated.")
                

    def start(self):
        try:
            # Create threads


            # Start threads

            logging.info("Game Engine started.")
            print("Game Engine started.")
        except KeyboardInterrupt:
            pass

    async def async_start(self):
        self.loop = asyncio.get_event_loop()
        await self.loop.run_in_executor(None, self.start)
