using UnityEngine;
using UnityEngine.UI;

public class SpiderWebButton : MonoBehaviour
{
    public Button button;
    public SpiderWebManager spiderWebManager;

    void Start()
    {
        button.onClick.AddListener(OnButtonClick);
    }

    void OnButtonClick()
    {
        spiderWebManager.PerformAction();
    }
}
