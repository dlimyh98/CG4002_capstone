using UnityEngine;
using UnityEngine.UI;

public class FistButton : MonoBehaviour
{
    public Button button;
    public FistManager fistManager;

    void Start()
    {
        button.onClick.AddListener(OnButtonClick);
    }

    void OnButtonClick()
    {
        fistManager.PerformAction();
    }
}
