using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class HealthBar : MonoBehaviour
{
    public bool isForCurrentPlayer = true; // Toggle this in the editor to determine which player this health bar is for

    private GamePlayer gamePlayer
    {
        get
        {
            return isForCurrentPlayer ? GlobalPlayerChoice.Instance.currentPlayer : GlobalPlayerChoice.Instance.opponent;
        }
    }

    public Image healthBarFill;
    public TextMeshProUGUI healthText;

    void Update()
    {
        UpdateHealthBar(); // Update the health bar each frame
    }

    private void UpdateHealthBar()
    {
        if (gamePlayer != null) // Make sure the GamePlayer reference is set
        {
            float healthRatio = (float)gamePlayer.currentHealth / (float)gamePlayer.maxHealth;
            healthBarFill.fillAmount = healthRatio;
            healthText.text = $"{gamePlayer.currentHealth} / {gamePlayer.maxHealth}";
            healthBarFill.color = Color.red;
        }
    }
}
