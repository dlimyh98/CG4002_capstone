using UnityEngine;
using UnityEngine.UI;

public class PortalButton : MonoBehaviour
{
    public Button button;
    public PortalManager portalManager;

    void Start()
    {
        button.onClick.AddListener(OnButtonClick);
    }

    void OnButtonClick()
    {
        portalManager.PerformAction();
    }
}
