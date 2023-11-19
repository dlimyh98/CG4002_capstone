using UnityEngine;
using UnityEngine.UI;

public class GrenadeButton : MonoBehaviour
{
    public Button button;  // Drag your Button component here
    public GrenadeManager grenadeManager;  // Drag your GrenadeManager GameObject here

    void Start()
    {
        // Add a click event to the button
        button.onClick.AddListener(OnButtonClick);
    }

    void OnButtonClick()
    {
        // Call the PerformAction method from the GrenadeManager script
        grenadeManager.PerformAction();
    }
}
