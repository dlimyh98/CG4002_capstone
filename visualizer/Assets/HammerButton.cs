using UnityEngine;
using UnityEngine.UI;

public class HammerButton : MonoBehaviour
{
    public Button button;
    public HammerManager hammerManager;

    void Start()
    {
        button.onClick.AddListener(OnButtonClick);
    }

    void OnButtonClick()
    {
        hammerManager.PerformAction();
    }
}
