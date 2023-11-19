using UnityEngine;
using UnityEngine.UI;

public class ReloadButton : MonoBehaviour
{
    public Button button;  // Drag your Button component here

    // Dynamically get the targetPlayer from GlobalPlayerChoice
    private GamePlayer targetPlayer 
    {
        get 
        {
            return GlobalPlayerChoice.Instance.currentPlayer;
        }
    }

    void Start()
    {
        // Add a click event to the button
        button.onClick.AddListener(ReloadBullets);
    }

    void ReloadBullets()
    {
        if (targetPlayer != null)
        {
            targetPlayer.ReloadBullets();
        }
        else
        {
            Debug.LogWarning("targetPlayer is not set.");
        }
    }
}
