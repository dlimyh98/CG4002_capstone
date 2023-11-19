using UnityEngine;
using TMPro;

public class ScoreCountText : MonoBehaviour
{
    // Reference to the PlayerManager
    public PlayerManager playerManager;  // Make sure to link this in Unity Editor

    // Reference to the TextMeshPro text field
    public TextMeshProUGUI scoreText;

    void Start()
    {
        // Initial score update
        UpdateScoreCount();
    }

    void Update()
    {
        // Continuously update the score
        UpdateScoreCount();
    }

    // Update the score text
    public void UpdateScoreCount()
    {
        if (playerManager != null)
        {
            // Replace these with actual function calls to get the kills when implemented
            int player1Kills = playerManager.player2.GetDeaths();
            int player2Kills = playerManager.player1.GetDeaths();

            // Update the text field
            scoreText.text = $"Player 1: {player1Kills} / Player 2: {player2Kills}";
        }
        else
        {
            Debug.LogError("PlayerManager is not set");
        }
    }
}
