import threading
import queue
import json
import time
import logging
import asyncio

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
# logging.basicConfig(filename='game_log.log', level=logging.INFO, format='%(asctime)s %(message)s')


class GameEngine:
    def __init__(self):
        self.data_input_queue = queue.Queue()
        self.data_output_queue = queue.Queue()
        self.player1 = Player()
        self.player2 = Player()
        self.lock = threading.Lock()
        self.loop = None

    def data_collection_thread(self):
        while True:
            try:
                raw_data_action = input("Enter action JSON: ") 
                data_action = json.loads(raw_data_action)
                with self.lock:
                    self.data_input_queue.put(data_action)
            except json.JSONDecodeError:
                print("Invalid JSON format.")
            except Exception as e:
                print(f"An error occurred: {e}")

            time.sleep(1)

    def game_processing_thread(self):
        while True:
            with self.lock:
                if not self.data_input_queue.empty():
                    message = self.data_input_queue.get()
                    msg_type = message.get('type')
                    
                    if msg_type == 'action':
                        self.handle_action(message)

                    elif msg_type == 'utility':
                        self.handle_utility(message)
                        
                    elif msg_type == 'confirmation':
                        self.handle_confirmation(message)
                        
            self.send_entire_state()
            time.sleep(2)

    def handle_action(self, action_data):
        action_type = action_data['action_type']
        player_id = action_data['player_id']

        acting_player = self.player1 if player_id == "player1" else self.player2

        if action_type == 'grenade':
            if acting_player.currentGrenades > 0:
                acting_player.currentGrenades -= 1

        elif action_type == 'shot':
            if acting_player.currentBullets > 0:
                acting_player.currentBullets -= 1

    def handle_utility(self, utility_data):
        utility_type = utility_data['utility_type']
        player_id = utility_data['player_id']

        acting_player = self.player1 if player_id == "player1" else self.player2

        if utility_type == 'reload':
            acting_player.currentBullets = Player.maxBullets

        elif utility_type == 'shield':
            if acting_player.currentShields > 0:
                acting_player.isShieldActive = True
                acting_player.currentShield = Player.maxShield
                acting_player.currentShields -= 1
                
    def handle_confirmation(self, confirmation_data):
        print("handle_confirmation is called")
        action_type = confirmation_data['action_type']
        target_id = confirmation_data['target_id']
        hit = confirmation_data['hit']

        target_player = self.player1 if target_id == "player1" else self.player2

        damage = 0  

        if action_type == 'grenade':
            damage = 30 if hit else 0

        elif action_type == 'shot':
            damage = 10 if hit else 0

        elif action_type in ['fist', 'spiderweb', 'portal', 'spear', 'hammer']:
            damage = 10 if hit else 0  

        self.apply_damage(target_player, damage)

    def apply_damage(self, target_player, damage):
        print(f"Inside apply_damage, applying {damage} damage to {target_player}")
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

    def send_entire_state(self):
        state = {
            "type": "game_state",
            "player1": vars(self.player1),
            "player2": vars(self.player2)
        }
        with self.lock:
            self.data_output_queue.put(json.dumps(state))

    def data_output_thread(self):
        while True:
            with self.lock:
                if not self.data_output_queue.empty():
                    data = self.data_output_queue.get()
                    #print(f"Sending data to Unity: {data}")
                    logging.info(f"Sending data to Unity: {data}")
            time.sleep(1)

    def start(self):
        try:
            # Create threads
            # data_collection = threading.Thread(target=self.data_collection_thread)
            game_processing = threading.Thread(target=self.game_processing_thread)
            data_output = threading.Thread(target=self.data_output_thread)

            # Start threads
            # data_collection.start()
            game_processing.start()
            data_output.start()

            print("Game Engine started.")
        except KeyboardInterrupt:
            pass

    async def async_start(self):
        self.loop = asyncio.get_event_loop()
        await self.loop.run_in_executor(None, self.start)

# if __name__ == "__main__":
#     game_engine = GameEngine()

#     # Create threads
#     data_collection = threading.Thread(target=game_engine.data_collection_thread)
#     game_processing = threading.Thread(target=game_engine.game_processing_thread)
#     data_output = threading.Thread(target=game_engine.data_output_thread)

#     # Start threads
#     data_collection.start()
#     game_processing.start()
#     data_output.start()