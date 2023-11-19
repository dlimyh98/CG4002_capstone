using UnityEngine;
using UnityEngine.UI;

public class SelfDamageButton : MonoBehaviour
{
    public Button button; // Drag your Button component here

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
        button.onClick.AddListener(InflictDamage);
    }

    void InflictDamage()
    {
        if (targetPlayer != null)
        {
            targetPlayer.TakeDamage(10);
        }
        else
        {
            Debug.LogWarning("targetPlayer is not set.");
        }
    }
}
