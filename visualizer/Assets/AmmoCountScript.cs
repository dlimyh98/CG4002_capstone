using UnityEngine;
using TMPro;

public class AmmoCountScript : MonoBehaviour
{
    public TextMeshProUGUI ammoText;

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
        UpdateAmmoCount();
    }

    void Update()
    {
        UpdateAmmoCount();  // Update the ammo count display each frame
    }

    private void UpdateAmmoCount()
    {
        if (gamePlayer != null)  // Check that the GamePlayer reference has been set
        {
            ammoText.text = $"Ammo: {gamePlayer.currentBullets}/{gamePlayer.maxBullets}";
        }
    }
}
