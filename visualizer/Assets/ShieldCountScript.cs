using UnityEngine;
using TMPro;

public class ShieldCountScript : MonoBehaviour
{
    public TextMeshProUGUI shieldText;

    // Dynamically get the gamePlayer from GlobalPlayerChoice
    private GamePlayer gamePlayer 
    {
        get 
        {
            return GlobalPlayerChoice.Instance.currentPlayer;
        }
    }

    void Start()
    {
        UpdateShieldCount(); // Initialize the shield count display
    }

    void Update()
    {
        UpdateShieldCount(); // Update the shield count display each frame
    }

    private void UpdateShieldCount()
    {
        if (gamePlayer != null) // Check to make sure the GamePlayer reference has been set
        {
            shieldText.text = $"Shield: {gamePlayer.currentShields}/{gamePlayer.maxShields}";
        }
    }
}
