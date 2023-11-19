using UnityEngine;
using UnityEngine.UI;

public class ShieldButton : MonoBehaviour
{
    public Button button; // Drag your Button component here
    public bool isForCurrentPlayer = true; // Toggle this in the editor

    private GamePlayer targetPlayer
    {
        get
        {
            return isForCurrentPlayer ? GlobalPlayerChoice.Instance.currentPlayer : GlobalPlayerChoice.Instance.opponent;
        }
    }

    void Start()
    {
        // Add a click event to the button
        button.onClick.AddListener(ActivateShield);
    }

    void ActivateShield()
    {
        if (targetPlayer != null)
        {
            targetPlayer.ActivateShield();
        }
        else
        {
            Debug.LogWarning("targetPlayer is not set.");
        }
    }
}
