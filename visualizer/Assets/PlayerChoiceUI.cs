using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class PlayerChoiceUI : MonoBehaviour
{
    public Button player1Button;
    public Button player2Button;
    public PlayerManager playerManager;

    public TMP_Text playerDisplayText;


    private void Start()
    {
        player1Button.onClick.AddListener(OnPlayer1ButtonPressed);
        player2Button.onClick.AddListener(OnPlayer2ButtonPressed);
        playerDisplayText.text = "Unselected";
    }

    private void OnPlayer1ButtonPressed()
    {
        GlobalPlayerChoice.Instance.currentPlayer = playerManager.player1;
        playerDisplayText.text = "Player 1";
        HideUI(); // Hide the choice UI after the selection is made
    }

    private void OnPlayer2ButtonPressed()
    {
        GlobalPlayerChoice.Instance.currentPlayer = playerManager.player2;
        playerDisplayText.text = "Player 2";
        HideUI(); // Hide the choice UI after the selection is made
    }

    private void HideUI()
    {
        gameObject.SetActive(false); // Hide the player choice UI
    }
}
