using UnityEngine;
using UnityEngine.UI;

public class RespawnPlayerButton : MonoBehaviour
{
    public Button button;  // Drag your Button component here
    public GamePlayer targetPlayer; // Drag your GamePlayer GameObject here

    void Start()
    {
        // Add a click event to the button
        button.onClick.AddListener(RespawnPlayer);
    }

    void RespawnPlayer()
    {
        if (targetPlayer != null)
        {
            targetPlayer.Respawn();
        }
        else
        {
            Debug.LogWarning("targetPlayer is not set.");
        }
    }
}
