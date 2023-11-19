using UnityEngine;
using UnityEngine.UI;
using TMPro;    

public class LogoutUI : MonoBehaviour
{
    public GameObject logoutCanvas; // Reference to the canvas
    public TextMeshProUGUI logoutText; // Reference to the text component displaying which player logged out

    private void Start()
    {
        Hide(); // Hide the canvas initially
    }

    // Display the logout message
    public void Display(string message)
    {
        if (logoutCanvas != null && logoutText != null)
        {
            logoutText.text = message; // Set the displayed text
            logoutCanvas.SetActive(true); // Show the canvas
        }
    }

    // Function to hide the logout canvas
    public void Hide()
    {
        if (logoutCanvas != null)
        {
            logoutCanvas.SetActive(false); // Hide the canvas
        }
    }
}
