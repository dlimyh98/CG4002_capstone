using UnityEngine;
using TMPro;

public class GrenadeCountScript : MonoBehaviour
{
    public TextMeshProUGUI grenadeText;

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
        UpdateGrenadeCount(); // Initialize the grenade count display
    }

    void Update()
    {
        UpdateGrenadeCount(); // Update the grenade count display each frame
    }

    private void UpdateGrenadeCount()
    {
        if (gamePlayer != null) // Check to make sure the GamePlayer reference has been set
        {
            grenadeText.text = $"Nades: {gamePlayer.currentGrenades}";
        }
    }
}
