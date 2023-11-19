using UnityEngine;

public class ShieldManager : MonoBehaviour
{
    public GameObject shieldPrefab;  // Assign your Shield prefab in the Unity editor
    public Transform imageTarget;  // Assign your image target here

    private GamePlayer targetPlayer 
    {
        get 
        {
            return GlobalPlayerChoice.Instance.opponent;
        }
    }

    private GameObject activeShield;  // To keep track of the instantiated shield

    // Function to toggle the shield on or off based on the player's shield status
    public void UpdateShieldStatus()
    {
        // Check if targetPlayer is not null
        if (targetPlayer == null) return;

        // Destroy the shield if it's active but the player's shield is not
        if (activeShield != null && !targetPlayer.isShieldActive)
        {
            Destroy(activeShield);
            activeShield = null;
            return;
        }

        // Create a shield if there's none and the player's shield is active
        if (activeShield == null && targetPlayer.isShieldActive)
        {
            activeShield = Instantiate(shieldPrefab, imageTarget.position, Quaternion.identity);

            // Optionally parent the shield to the image target, so it moves with the target
            activeShield.transform.SetParent(imageTarget);
        }
    }


    void Start()
    {
        // Initial shield status update
        UpdateShieldStatus();
    }

    void Update()
    {
        // Update the shield status each frame
        UpdateShieldStatus();
    }
}
