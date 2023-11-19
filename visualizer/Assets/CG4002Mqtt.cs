using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using uPLibrary.Networking.M2Mqtt;
using uPLibrary.Networking.M2Mqtt.Messages;
using M2MqttUnity;
using TMPro;    
using System.Text.RegularExpressions;

namespace M2MqttUnity.CG4002
{

    [Serializable]
    public class GameState
    {
        public string type;
        public PlayerInfo player1;
        public PlayerInfo player2;
    }

    [Serializable]
    public class PlayerInfo
    {
        public int currentHealth;
        public int currentShield;
        public int currentBullets;
        public int currentShields;
        public int currentGrenades;
        public int deaths;
        public bool isShieldActive;
    }

    [Serializable]
    public class GameAction
    {
        public string type;
        public string player_id;
        public string action_type;
        public string target_id;
    }

    [Serializable]
    public class UtilityAction
    {
        public string type;
        public string player_id;
        public string utility_type;
    }

    public class CG4002Mqtt : M2MqttUnityClient
    {
        public event Action<GameAction> OnActionMessage;
        public event Action<GameState> OnGameStateMessage;
        public event Action<UtilityAction> OnUtilityMessage;


        [Header("MQTT topics")]
        public string topicSubscribe = "#";
        public string topicPublish = "";
        public string messagePublish = "";

        public bool autoTest = false;

        public TextMeshProUGUI messageText;
        private List<string> eventMessages = new List<string>();

        private string m_msg;
        public string msg
        {
            get { return m_msg; }
            set
            {
                if (m_msg == value) return;
                m_msg = value;
                OnMessageArrived?.Invoke(m_msg);
            }
        }

        public event OnMessageArrivedDelegate OnMessageArrived;
        public delegate void OnMessageArrivedDelegate(string newMsg);

        private bool m_isConnected;
        public bool isConnected
        {
            get { return m_isConnected; }
            set
            {
                if (m_isConnected == value) return;
                m_isConnected = value;
                OnConnectionSucceeded?.Invoke(isConnected);
            }
        }
        public event OnConnectionSucceededDelegate OnConnectionSucceeded;
        public delegate void OnConnectionSucceededDelegate(bool isConnected);

        public void Publish()
        {
            client.Publish(topicPublish, System.Text.Encoding.UTF8.GetBytes(messagePublish), MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, false);
            Debug.Log("Message published");
        }

        protected override void OnConnecting()
        {
            base.OnConnecting();
            Debug.Log("Connecting...");
        }

        protected override void OnConnected()
        {
            base.OnConnected();
            isConnected = true;

            // Set the messageText to "Connected"
            if (messageText != null)
            {
                messageText.text = "Connected";
            }

            if (autoTest)
            {
                Publish();
            }
        }

        protected override void SubscribeTopics()
        {
            client.Subscribe(new string[] { topicSubscribe }, new byte[] { MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE });
        }

        protected override void UnsubscribeTopics()
        {
            client.Unsubscribe(new string[] { topicSubscribe });
        }

        protected override void OnConnectionFailed(string errorMessage)
        {
            Debug.Log("CONNECTION FAILED! " + errorMessage);
        }

        protected override void OnDisconnected()
        {
            Debug.Log("Disconnected.");
            isConnected = false;

            // Set the messageText to "Not Connected"
            if (messageText != null)
            {
                messageText.text = "Not Connected";
            }

            Connect();
        }

        protected override void OnConnectionLost()
        {
            Debug.Log("CONNECTION LOST!");

            // Set the messageText to "Not Connected"
            if (messageText != null)
            {
                messageText.text = "Not Connected";
            }

            Connect();
        }

        protected override void Start()
        {
            base.Start();
            // Removed the line that sets the message text when a new message arrives
            Connect();
        }

        void UpdateMessageText(string newMessage)
        {
            if (messageText != null)
            {
                messageText.text = newMessage;
            }
        }

        protected override void DecodeMessage(string topic, byte[] message)
        {
            string decodedMessage = System.Text.Encoding.UTF8.GetString(message);
            Debug.Log("Received: " + decodedMessage);

            OnMessageArrived?.Invoke(decodedMessage);

            try
            {
                if (decodedMessage.ToLower().Contains("game_state"))
                {
                    Debug.Log("Attempting to decode game_state message");
                    GameState gameState = JsonUtility.FromJson<GameState>(decodedMessage);
                    
                    if (gameState != null && gameState.type == "game_state")
                    {
                        Debug.Log("Successfully decoded game_state message");
                        OnGameStateMessage?.Invoke(gameState);                
                    }
                    else
                    {
                        Debug.LogWarning("Decoded game_state object is null or type is incorrect");
                    }
                }
                else if (Regex.IsMatch(decodedMessage, "\"type\"\\s*:\\s*\"action\""))
                {
                    Debug.Log("Attempting to decode action message");
                    GameAction gameAction = JsonUtility.FromJson<GameAction>(decodedMessage);
                    
                    if (gameAction != null && gameAction.type == "action")
                    {
                        Debug.Log("Successfully decoded action message");
                        OnActionMessage?.Invoke(gameAction);
                    }
                    else
                    {
                        Debug.LogWarning("Decoded action object is null or type is incorrect");
                    }
                }
                else if (Regex.IsMatch(decodedMessage, "\"type\"\\s*:\\s*\"utility\""))
                {
                    Debug.Log("Attempting to decode utility message");
                    UtilityAction utilityAction = JsonUtility.FromJson<UtilityAction>(decodedMessage);
                    
                    if (utilityAction != null && utilityAction.type == "utility")
                    {
                        Debug.Log("Successfully decoded utility message");
                        OnUtilityMessage?.Invoke(utilityAction);
                    }
                    else
                    {
                        Debug.LogWarning("Decoded utility object is null or type is incorrect");
                    }
                }
                else
                {
                    Debug.LogWarning("Message type not recognised");
                }
            }
            catch(Exception e)
            {
                Debug.LogError("Error during decoding: " + e.Message);
            }
        }

        protected override void Update()
        {
            base.Update();

            if (eventMessages.Count > 0)
            {
                foreach (string msg in eventMessages)
                {
                    OnMessageArrived?.Invoke(msg);
                }
                eventMessages.Clear();
            }
        }

        private void OnDestroy()
        {
            Disconnect();
        }
    }
}
