import threading
import queue
import json
import logging
import asyncio
import json

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

        action = "gun"
        while True:
            if not self.gun_input_queue.empty():
                # this message should be a tuple
                # can catch exception if not tuple
                player_id = self.gun_input_queue.get()
                # temporary workaround
                if player_id == 4:
                    player_id = 1
                print(f"[GameEngine] gun packet: {player_id}")

                try:
                    # wait for a packet from the vest queue
                    # this will time out after 20ms and raise a queue.Empty exception
                    vest_message = self.vest_input_queue.get(block=True, timeout=0.02)
                    print(f"[GameEngine] vest packet: {vest_message}")
                    # deduct target player HP, reduce bullet count
                    self.handle_shot(player_id, True)

                    # send packet to visualizer to say hit
                    # construct visualizer packet
                    gun_visualizer_message = self.construct_visualizer_action_packet(player_id, action)
                    self.visualizer_client_output_queue.put(gun_visualizer_message)

                    # update hardware
                    tuples_to_relay_node = self.extract_game_engine_info()
                    # for tuple in tuples_to_relay_node:
                    #     logging.info(f"[GameEngine] gun_vest_thread HIT: tuple sent: {tuple}")
                    #     self.relay_node_server_output_queue.put(str(tuple))
                    logging.info(f"[GameEngine] gun_vest_thread HIT: tuple sent: {tuple}")
                    self.relay_node_server_output_queue.put(str(tuples_to_relay_node))                    


                    # send updated game state + action to eval client
                    self.eval_client_output_queue.put(self.convert_game_engine_state_to_eval_client(action))


                except queue.Empty:
                    # classify as miss
                    self.handle_shot(player_id, False)

                    # update hardware
                    tuples_to_relay_node = self.extract_game_engine_info()
                    # for tuple in tuples_to_relay_node:
                    #     logging.info(f"[GameEngine] gun_vest_thread MISS: tuple sent: {tuple}")
                    #     self.relay_node_server_output_queue.put(str(tuple))
                    logging.info(f"[GameEngine] gun_vest_thread MISS: tuple sent: {tuple}")
                    self.relay_node_server_output_queue.put(str(tuples_to_relay_node))                      

                    # send updated game state + action to eval client
                    self.eval_client_output_queue.put(self.convert_game_engine_state_to_eval_client(action))

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
                # action = "shield"

                if action in possible_actions:

                    if action in utility_actions:
                    # if utility, update game state, send to visualizer
                        self.handle_utility(player_id, action)

                    # else, send a packet to visualizer and wait for confirmation
                    elif action in special_actions:

                        # construct visualizer packet and send to visualizer
                        dummy_visualizer_packet = self.construct_visualizer_action_packet(player_id, action)
                        self.visualizer_client_output_queue.put(dummy_visualizer_packet)

                        # wait for visualizer_client_input_queue with timeout
                        try:
                            confirmation_packet = self.visualizer_client_input_queue.get(block=True, timeout=0.02)
                            self.handle_visualizer_confirmation_packet(confirmation_packet)
                        except queue.Empty:
                            logging.info("[GameEngine] action_processing_thread: TIMEOUT")

                # send game state + action to eval client and visualizer
                self.visualizer_client_output_queue.put(self.construct_visualizer_game_state_packet())
                self.eval_client_output_queue.put(self.convert_game_engine_state_to_eval_client(action))
        
        
    # Thread 3: waiting for a message from eval client
    def game_state_processing_thread(self):
        """
        Handles incoming game state from Eval Client (from Eval Server).

        Update the game state and extract relevant information to send to Relay Node Server.
        """
        while True:
            if not self.eval_client_input_queue.empty():
                game_state = self.eval_client_input_queue.get()

                game_state_dict = json.loads(game_state)

                # update game state
                self.update_game_state(game_state_dict)
                # send back player HP and bullet count back to Relay Node server
                # break down tuple here
                tuples_to_relay_node = self.extract_eval_client_game_state_info(game_state_dict)
                # for tuple in tuples_to_relay_node:
                #     logging.info(f"[GameEngine] game_state_thread UPDATE: tuple sent: {tuple}")
                #     self.relay_node_server_output_queue.put(str(tuple))
                logging.info(f"[GameEngine] gun_state_thread UPDATE: tuple sent: {tuple}")
                self.relay_node_server_output_queue.put(str(tuples_to_relay_node))  

    
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

#########################(Added by your favourite boy Shawn, probably full of bugs. Needs testing)#############################

    # Construct visualizer game_state packet and returns it as a string
    def construct_visualizer_game_state_packet(self):
        """
        Construct visualizer game_state packet and returns it as a string.
        
        Example:
        {
            "type": "game_state", 
            "player1": {
                "currentHealth": 70, 
                "currentShield": 0, 
                "currentBullets": 6, 
                "currentShields": 3, 
                "currentGrenades": 1, 
                "deaths": 0, 
                "isShieldActive": false
            }, 
            "player2": {
                "currentHealth": 60, 
                "currentShield": 0, 
                "currentBullets": 5, 
                "currentShields": 3, 
                "currentGrenades": 2, 
                "deaths": 0, 
                "isShieldActive": false
            }
        }
        """
        player1 = self.player1
        player2 = self.player2

        packet = {
            "type": "game_state",
            "player1": {
                "currentHealth": player1.currentHealth,
                "currentShield": player1.currentShield,
                "currentBullets": player1.currentBullets,
                "currentShields": player1.currentShields,
                "currentGrenades": player1.currentGrenades,
                "deaths": player1.deaths,
                "isShieldActive": player1.isShieldActive
            },
            "player2": {
                "currentHealth": player2.currentHealth,
                "currentShield": player2.currentShield,
                "currentBullets": player2.currentBullets,
                "currentShields": player2.currentShields,
                "currentGrenades": player2.currentGrenades,
                "deaths": player2.deaths,
                "isShieldActive": player2.isShieldActive
            }
        }
        
        return json.dumps(packet)
    
    # Construct visualizer action packet and returns it as a string, player_id is either "1" or "2"
    def construct_visualizer_action_packet(self, player_id, action):
        """
        Construct visualizer action packet and returns it as a string.
        
        Example:
        {
            "type":"action",
            "player_id":"player2",
            "action_type":"shoot",
            "target_id":"player1"
        }
        """
        player_id = "player1" if player_id == 1 else "player2"
        target_id = "player1" if player_id == 2 else "player2"
        
        packet = {
            "type": "action",
            "player_id": player_id,
            "action_type": action,
            "target_id": target_id
        }
        
        return json.dumps(packet)    

    # Construct visualizer action packet and returns it as a string, player_id is either "1" or "2"
    def construct_visualizer_utility_packet(self, player_id, utility_action):
        """
        Construct visualizer utility packet and returns it as a string.
        
        Example:
        {
            "type":"utility",
            "player_id":"player2",
            "utility_type":"shield"
        }
        """
        player_id_str = "player1" if player_id == 1 else "player2"
        packet = {
            "type": "utility",
            "player_id": player_id_str,
            "utility_type": utility_action  
        }
        
        return json.dumps(packet)

    def handle_visualizer_confirmation_packet(self, visualizer_confirmation_packet):
        """
        Handle the visualizer confirmation packet.

        Example packet:
        {
            "type": "confirmation",
            "player_id": "player1",
            "action_type": "grenade",
            "target_id": "player2",
            "hit": true
        }
        """
        # Extract the necessary information from the packet
        logging.info(f"[XXX]: packet: {visualizer_confirmation_packet}")
        visualizer_confirmation_packet = json.loads(visualizer_confirmation_packet)
        player_id_str = visualizer_confirmation_packet['player_id']
        player_id = 1 if player_id_str == 'player1' else 2
        action_type = visualizer_confirmation_packet['action_type']
        hit = visualizer_confirmation_packet['hit']

        # Pass the extracted information to the handle_actions method
        self.handle_actions(player_id, action_type, hit)                

#########################(Added by your favourite boy Shawn, probably full of bugs. Needs testing)#############################  

    def convert_game_engine_state_to_eval_client(self, action):
        def player_transform(player_data):
            return {
                "hp": player_data.currentHealth,
                "bullets": player_data.currentBullets,
                "grenades": player_data.currentGrenades,
                "shield_hp": player_data.currentShield,
                "deaths": player_data.deaths,
                "shields": player_data.currentShields
            }  

        transformed_data = {
                "player_id": 1,
                "action": action,
                "game_state": {
                    "p1": player_transform(self.player1),
                    "p2": player_transform(self.player2)
                }
            }
        return json.dumps(transformed_data)

    def extract_game_engine_info(self):
        p1_bullets_tuple = ('b', 1, self.player1.currentBullets)
        p1_hp_tuple = ('h', 1, self.player1.currentHealth)
        p2_bullets_tuple = ('b', 2, self.player2.currentBullets)
        p2_hp_tuple = ('h', 2, self.player2.currentHealth)
        logging.info(f"[GameEngine] extract_game_engine_info: {p1_bullets_tuple}, {p1_hp_tuple}, {p2_bullets_tuple}, {p2_hp_tuple}")
        return p1_bullets_tuple
        # return p1_bullets_tuple, p1_hp_tuple, p2_bullets_tuple, p2_hp_tuple      

    def extract_eval_client_game_state_info(self, eval_client_data):
        """
        Extract p1 and p2's bullet counts and HP.

        Return four tuples to be sent back to the relay node server.
        """
        p1_bullets = eval_client_data['p1']['bullets']
        p1_hp = eval_client_data['p1']['hp']
        p2_bullets = eval_client_data['p2']['bullets']
        p2_hp = eval_client_data['p2']['hp']

        p1_bullets_tuple = ('b', 1, p1_bullets)
        p1_hp_tuple = ('h', 1, p1_hp)

        p2_bullets_tuple = ('b', 2, p2_bullets)
        p2_hp_tuple = ('h', 2, p2_hp)
        logging.info(f"[GameEngine] extract_eval_client_game_state_info: {p1_bullets_tuple}, {p1_hp_tuple}, {p2_bullets_tuple}, {p2_hp_tuple}")
        return p1_bullets_tuple # in the top function, just remove the for loop
        # return p1_bullets_tuple, p1_hp_tuple, p2_bullets_tuple, p2_hp_tuple
        

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
            action_processing = threading.Thread(target=self.action_processing_thread)
            gun_vest_processing = threading.Thread(target=self.gun_vest_processing_thread)
            game_state_processing = threading.Thread(target=self.game_state_processing_thread)

            # Start threads
            action_processing.start()
            gun_vest_processing.start()
            game_state_processing.start()

            logging.info("Game Engine started.")
            print("Game Engine started.")
        except KeyboardInterrupt:
            pass

    async def async_start(self):
        self.loop = asyncio.get_event_loop()
        await self.loop.run_in_executor(None, self.start)
