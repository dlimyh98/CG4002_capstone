using UnityEngine;
using UnityEngine.UI;

public class AmmoButton : MonoBehaviour
{
    public Button button;  // Drag your Button component here
    public BulletManager bulletManager;  // Drag your GrenadeManager GameObject here

    void Start()
    {
        // Add a click event to the button
        button.onClick.AddListener(OnButtonClick);
    }

    void OnButtonClick()
    {
        // Call the PerformAction method from the BulletManager script
        bulletManager.PerformAction();
    }
}
