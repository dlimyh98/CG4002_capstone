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

utility_actions = ["shield", "reload", "logout"]

special_actions = ["gun", "web", "grenade", "portal", "punch", "hammer", "spear"]


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
        self.visualizer_client_input_queue = queue.Queue() # data from visualizer (confirmation)
        self.eval_client_input_queue = queue.Queue() # data from eval client

        # output queues
        self.visualizer_client_output_queue = queue.Queue()
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
                player_id = self.gun_input_queue.get()

                try:
                    # wait for a packet from the vest queue
                    # this will time out after 20ms and raise a queue.Empty exception
                    vest_message = self.vest_input_queue.get(block=True, timeout=0.02)

                    # deduct target player HP, reduce bullet count
                    self.handle_shot(player_id, True)

                    # send packet to visualizer to say hit
                    # construct visualizer packet

                    # send updated game state + action to eval client
                    dummy_game_state = None
                    self.eval_client_output_queue.put(dummy_game_state)


                except queue.Empty:
                    # classify as miss
                    self.handle_shot(player_id, False)
                    # send packet to visualizer to say miss
                    # construct visualizer packet

                    # send updated game state + action to eval client
                    dummy_game_state = None
                    self.eval_client_output_queue.put(dummy_game_state)
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
                # for 2 player game, this action should contain both player id and action
                # i.e. (1, shield) or (2, reload)
                action = self.action_input_queue.get()
                
                # obtain player id and action
                player_id = 1
                action = "shield"

                if action in possible_actions:

                    if action in utility_actions:
                    # if utility, update game state, send to visualizer
                        self.handle_utility(player_id, action)

                    # else, send a packet to visualizer and wait for confirmation
                    elif action in special_actions:

                        # construct visualizer packet and send to visualizer
                        dummy_visualizer_packet = None
                        self.visualizer_client_output_queue.put(dummy_visualizer_packet)

                        # wait for visualizer_client_input_queue with timeout
                        hit = False
                        try:
                            self.visualizer_client_input_queue.get(block=True, timeout=0.02)
                            hit = True
                        except queue.Empty:
                            # update game state
                            hit = False

                        # update game state
                        self.handle_actions(player_id, action, hit)

                # send game state + action to eval client
                dummy_game_state = None
                self.eval_client_output_queue.put(dummy_game_state)
        
        
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
                # break down tuple here
                dummy_tuple = (1, 2)
                self.relay_node_server_output_queue.put(dummy_tuple)

    
    # insert all utility functions here
    # should we follow GameState.py's implementation, or week 9 game engine?
    def handle_shot(self, player_id, hit):
        """
        Handle when the gun is fired.

        If hit is True, deduct the HP. If player has 0 bullets, exit.
        """
        acting_player = self.player1 if player_id == 1 else self.player2
        target_player = self.player2 if player_id == 1 else self.player1

        if acting_player.currentBullets <= 0:
            logging.info(f"[GameEngine]: Player {acting_player} has no bullets.")
            return
        acting_player.currentBullets -= 1

        if hit:
            self.apply_damage(target_player, 10)

    def handle_utility(self, player_id, utility_action):
        """
        Handle reload, shield and logout actions.

        These actions do not require a confirmation from the Visualizer.
        """
        acting_player = self.player1 if player_id == "player1" else self.player2

        if utility_action == 'reload':
            acting_player.currentBullets = Player.maxBullets

        elif utility_action == 'shield':
            if acting_player.currentShields > 0:
                acting_player.isShieldActive = True
                acting_player.currentShield = Player.maxShield
                acting_player.currentShields -= 1

        elif utility_action == 'logout':
            #TODO  
            return   

    def handle_actions(self, player_id, special_action, hit):
        """
        Handle actions (non-utility).

        Hit variable will be determined from visualizer client's response.
        """  
        acting_player = self.player1 if player_id == 1 else self.player2
        target_player = self.player2 if player_id == 1 else self.player1

        if special_action == 'grenade':
            if acting_player.currentGrenades > 0:
                acting_player.currentGrenades -= 1

            damage = 30 if hit else 0

        elif special_action in ['punch', 'web', 'portal', 'spear', 'hammer']:
            damage = 10 if hit else 0  

        self.apply_damage(target_player, damage)

    
    def apply_damage(self, target_player, damage):
        #print(f"Inside apply_damage, applying {damage} damage to {target_player}")
        if target_player.isShieldActive:
            remaining_shield = target_player.currentShield - damage
            if remaining_shield >= 0:
                target_player.currentShield = remaining_shield
            else:
                target_player.currentHealth += remaining_shield if remaining_shield < 0 else 0
                target_player.isShieldActive = False
                target_player.currentShield = 0
        else:
            target_player.currentHealth -= damage
            if target_player.currentHealth <= 0:
                target_player.deaths += 1
                target_player.respawn()

    def construct_visualizer_packet(self, action):
        return


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
