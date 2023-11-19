using UnityEngine;
using M2MqttUnity.CG4002;

public class PlayerManager : MonoBehaviour
{
    public GamePlayer player1;
    public GamePlayer player2;
    public CG4002Mqtt mqttClient;

    public LogoutUI logoutUI;

    void Start()
    {
        // Register the MQTT GameState event callback
        if (mqttClient != null)
        {
            mqttClient.OnGameStateMessage += HandleGameStateMessage;
            mqttClient.OnUtilityMessage += HandleUtilityMessage;
        }
        else
        {
            Debug.LogWarning("MQTT Client reference not set in PlayerManager.");
        }
    }

    private void OnDestroy()
    {
        // Unregister the MQTT GameState event callback
        if (mqttClient != null)
        {
            mqttClient.OnGameStateMessage -= HandleGameStateMessage;
            mqttClient.OnUtilityMessage -= HandleUtilityMessage;
        }
    }

    void HandleUtilityMessage(UtilityAction utilityAction)
    {
        Debug.Log("Entered HandleUtilityMessage");
        if (utilityAction.type == "utility")
        {
            if (utilityAction.utility_type == "reload")
            {
                if (utilityAction.player_id == "player1")
                {
                    player1.ReloadBullets();
                }
                else if (utilityAction.player_id == "player2")
                {
                    player2.ReloadBullets();
                }
            }

            else if (utilityAction.utility_type == "shield")
            {
                if (utilityAction.player_id == "player1")
                {
                    player1.ActivateShield();
                }
                else if (utilityAction.player_id == "player2")
                {
                    player2.ActivateShield();
                }
            }      

            else if (utilityAction.utility_type == "logout")
            {
                if (utilityAction.player_id == "player1")
                {
                    logoutUI.Display("Player 1 logged out");
                }
                else if (utilityAction.player_id == "player2")
                {
                    logoutUI.Display("Player 2 logged out");
                }
            }
        }
    }

    void HandleGameStateMessage(M2MqttUnity.CG4002.GameState gameState)
    {
        Debug.Log("Entered HandleGameStateMessage");
        if (gameState.type == "game_state")
        {
            UpdatePlayerStats(player1, gameState.player1);
            UpdatePlayerStats(player2, gameState.player2);
        }
    }    

    void UpdatePlayerStats(GamePlayer player, M2MqttUnity.CG4002.PlayerInfo state)
    {
        player.currentHealth = state.currentHealth;
        player.currentShield = state.currentShield;
        player.currentBullets = state.currentBullets;
        player.currentShields = state.currentShields;
        player.currentGrenades = state.currentGrenades;
        player.deaths = state.deaths;
        player.isShieldActive = state.isShieldActive;
    }
}
