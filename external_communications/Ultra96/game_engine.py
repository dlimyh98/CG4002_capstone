import threading
import queue
import json
import time
import logging
import asyncio

# constants for received messages
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

# Initialize the logging
# uncomment below when running standalone
# logging.basicConfig(filename=r'C:\Users\Admin\OneDrive\Documents\repos\CG4002_Vuforia/game_log2.log', level=logging.INFO, format='%(asctime)s %(message)s')


class GameEngine:
    def __init__(self):
        self.data_input_queue = queue.Queue()
        self.data_output_queue = queue.Queue()
        self.eval_client_output_queue = queue.Queue()
        self.player1 = Player()
        self.player2 = Player()
        self.lock = threading.Lock()
        self.loop = None

    def game_processing_thread(self):
        while True:
            if not self.data_input_queue.empty():
                raw_message = self.data_input_queue.get()
                logging.info(f"[GameEngine]: Raw Message: {raw_message}")

                # unpack relay node server packet/AI packet here
                message = self.process_message(raw_message)
                #print(f"[GameEngine]: process_message output: {message}")

                action = self.process_action(message)

                #message = json.dumps(message)
                
                msg_type = message.get('type')
                
                if msg_type == 'action':
                    self.handle_action(message)
                    if action != "gun":
                        self.send_entire_state(action)

                elif msg_type == 'utility':
                    self.handle_utility(message)
                    self.send_entire_state(action)
                    
                elif msg_type == 'confirmation':
                    self.handle_confirmation(message)
                    if action == 'gun':
                        self.send_entire_state(action)
                
                elif msg_type == 'eval_game_state':
                    self.handle_eval_game_state(message)
                    self.send_eval_server_game_state()
                                          
    # process incoming messages:
    # 1. AI
    # 2. Eval Client
    # 3. Viz Client
    def process_message(self, message):
        if isinstance(message, str):
            # construct action message
            action = message
            logging.info(f"[GameEngine]: process_message message: {message}")
            
            # AI
            if action in possible_actions:
                logging.info("[GameEngine] process_messsage: Incoming from AI")
                if action == "shield" or action == "reload" or action == "logout":
                    action_message = {
                        "type": "utility",
                        "player_id": "player1",
                        "action_type": action
                    }
                else:
                    action_message = {
                        "type": "action",
                        "player_id": "player1",
                        "action_type": action,
                        "target_id": "player2"
                    }
                # return json.dumps(action_message)
                return action_message
            # message from viz client
            elif 'type' in message:
                logging.info("[GameEngine] process_messsage: Incoming from VizClient")
                # return json.dumps(message)
                # self.log_message_format(message)
                return json.loads(message)
            # message is from eval client
            else:
                logging.info("[GameEngine] process_messsage: Incoming from EvalClient")
                try:
                    game_state_message = self.convert_state_for_game_engine(json.loads(message))
                    return game_state_message
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                # Handle the error accordingly (e.g., log it, return an error message, etc.)

                # return json.dumps(game_state_message)
                
        
        if isinstance(message, tuple):
            logging.info("[GameEngine]: IS TUPLE")
            logging.info(f"[GameEngine]: message[0]: {message[0]}")
            # check message[0]
            # if gun, construct action (shoot) message
            # if vest, construct confirmation (hit/miss) message
            if message[0] == GUN:
                if message[2] == 1:
                    logging.info("[GameEngine]: GUN FIRED")
                    action_message = {
                        "type": "action",
                        "player_id": "player1",
                        "action_type": "gun",
                        "target_id": "player2"
                    }
                    # return json.dumps(action_message)
                    return action_message
            
            if message[0] == VEST:
                hit_var = False
                if message[1] == 1:
                    hit_var = True
                    action_data = {
                        "type": "confirmation",
                        "player_id": "player1",
                        "action_type": "gun",
                        "target_id": "player2",
                        "hit": hit_var
                    }
                    # action_message = json.dumps(action_data)
                    logging.info("[GameEngine]: VEST HIT")
                    return action_data
                else:
                    action_data = {
                        "type": "confirmation",
                        "player_id": "player1",
                        "action_type": "gun",
                        "target_id": "player2",
                        "hit": hit_var
                    }
                    logging.info("[GameEngine]: VEST FALSE")
                    action_message = action_data
                    logging.info(f"[GameEngine] Vest action_message: {action_message}")
                    return action_message

        
    def process_action(self, message):
        json_message = message
        logging.info(f"[GameEngine: process_action]: {json_message}")
        # self.log_message_format(json_message)
        return json_message.get('action_type')

    def handle_action(self, action_data):
        action_type = action_data['action_type']
        player_id = action_data['player_id']

        acting_player = self.player1 if player_id == "player1" else self.player2

        if action_type == 'grenade':
            if acting_player.currentGrenades > 0:
                acting_player.currentGrenades -= 1

        elif action_type == 'shoot':
            if acting_player.currentBullets > 0:
                acting_player.currentBullets -= 1

    def handle_utility(self, utility_data):
        utility_type = utility_data['type']
        player_id = utility_data['player_id']

        acting_player = self.player1 if player_id == "player1" else self.player2

        if utility_type == 'reload':
            acting_player.currentBullets = Player.maxBullets

        elif utility_type == 'shield':
            if acting_player.currentShields > 0:
                acting_player.isShieldActive = True
                acting_player.currentShield = Player.maxShield
                acting_player.currentShields -= 1

    def handle_eval_game_state(self, game_state_data):
        player1_data = game_state_data['player1']
        player2_data = game_state_data['player2']

        for attr, value in player1_data.items():
            setattr(self.player1, attr, value)

        for attr, value in player2_data.items():
            setattr(self.player2, attr, value) 
        
        logging.info("[GameEngine]: Game state updated.")
                
    def handle_confirmation(self, confirmation_data):
        #print("handle_confirmation is called")
        action_type = confirmation_data['action_type']
        target_id = confirmation_data['target_id']
        hit = confirmation_data['hit']

        target_player = self.player1 if target_id == "player1" else self.player2

        damage = 0  

        if action_type == 'grenade':
            damage = 30 if hit else 0

        elif action_type == 'shoot':
            damage = 10 if hit else 0

        elif action_type in ['fist', 'spiderweb', 'portal', 'spear', 'hammer']:
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

    def convert_state_for_eval_client(self, action, game_engine_state):
        def player_transform(player_data):
            return {
                "hp": player_data["currentHealth"],
                "bullets": player_data["currentBullets"],
                "grenades": player_data["currentGrenades"],
                "shield_hp": player_data["currentShield"],
                "deaths": player_data["deaths"],
                "shields": player_data["currentShields"]
            } 

        transformed_data = {
                "player_id": 1,
                "action": action,
                "game_state": {
                    "p1": player_transform(game_engine_state["player1"]),
                    "p2": player_transform(game_engine_state["player2"])
                }
            }
        return transformed_data
    
    def convert_state_for_game_engine(self, eval_client_state):
        # Extract player information
        # print(f"EVALCLIENT STATE: {eval_client_state}")
        p1 = eval_client_state["p1"]
        p2 = eval_client_state["p2"]

        p1_is_shield_active = False
        p1_shield_hp = eval_client_state["p1"]["shield_hp"]
        if p1_shield_hp > 0:
            p1_is_shield_active = True

        p2_is_shield_active = False
        p2_shield_hp = eval_client_state["p2"]["shield_hp"]
        if p2_shield_hp > 0:
            p2_is_shield_active = True

        # Create the game engine packet
        game_engine_packet = {
            "type": "game_state",
            "player1": {
                "currentHealth": p1["hp"],
                "currentShield": p1["shield_hp"],
                "currentBullets": p1["bullets"],
                "currentShields": p1["shields"],
                "currentGrenades": p1["grenades"],
                "deaths": p1["deaths"],
                "isShieldActive": p1_is_shield_active
            },
            "player2": {
                "currentHealth": p2["hp"],
                "currentShield": p2["shield_hp"],
                "currentBullets": p2["bullets"],
                "currentShields": p2["shields"],
                "currentGrenades": p2["grenades"],
                "deaths": p2["deaths"],
                "isShieldActive": p2_is_shield_active
            }
        }

        return game_engine_packet
    
    def send_entire_state(self, action):
        state = {
            "type": "game_state",
            "player1": vars(self.player1),
            "player2": vars(self.player2)
        }
        eval_client_state = self.convert_state_for_eval_client(action, state)
        self.eval_client_output_queue.put(json.dumps(eval_client_state))
        self.data_output_queue.put(json.dumps(state))

    def send_eval_server_game_state(self):
        state = {
            "type": "game_state",
            "player1": vars(self.player1),
            "player2": vars(self.player2)
        }
        self.eval_client_output_queue.put(json.dumps(state))

    # def data_output_thread(self):
    #     while True:
    #         with self.lock:
    #             if not self.data_output_queue.empty():
    #                 data = self.data_output_queue.get()
    #                 #print(f"Sending data to Unity: {data}")
    #                 logging.info(f"Sending data to Unity: {data}")
    #         time.sleep(1)

    def start(self):
        try:
            # Create threads
            game_processing = threading.Thread(target=self.game_processing_thread)

            # Start threads
            game_processing.start()
            logging.info("Game Engine started.")
            print("Game Engine started.")
        except KeyboardInterrupt:
            pass

    async def async_start(self):
        self.loop = asyncio.get_event_loop()
        await self.loop.run_in_executor(None, self.start)
