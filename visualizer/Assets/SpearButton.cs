using UnityEngine;
using UnityEngine.UI;

public class SpearButton : MonoBehaviour
{
    public Button button;
    public SpearManager spearManager;

    void Start()
    {
        button.onClick.AddListener(OnButtonClick);
    }

    void OnButtonClick()
    {
        spearManager.PerformAction();
    }
}
