using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class ShieldBar : MonoBehaviour
{
    public bool isForCurrentPlayer = true; // Toggle this in the editor to determine which player this shield bar is for

    private GamePlayer gamePlayer
    {
        get
        {
            return isForCurrentPlayer ? GlobalPlayerChoice.Instance.currentPlayer : GlobalPlayerChoice.Instance.opponent;
        }
    }

    public Image shieldBarFill;
    public TextMeshProUGUI shieldText;

    void Update()
    {
        UpdateShieldBar(); // Update the shield bar each frame
    }

    private void UpdateShieldBar()
    {
        if (gamePlayer != null) // Make sure the GamePlayer reference is set
        {
            float shieldRatio = (float)gamePlayer.currentShield / (float)gamePlayer.maxShield;
            shieldBarFill.fillAmount = shieldRatio;
            shieldText.text = $"{gamePlayer.currentShield} / {gamePlayer.maxShield}";
            // Customize the color based on the shield ratio or keep it constant
            // shieldBarFill.color = Color.blue;
        }
    }
}
