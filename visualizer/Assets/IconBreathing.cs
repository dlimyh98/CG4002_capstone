using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class IconBreathing : MonoBehaviour
{
    private RectTransform rectTransform;
    public float breatheSpeed = 1f;
    public float breatheAmount = 10f;
    private Vector2 initialSize;
    private bool isBreathing = false;

    void Start()
    {
        rectTransform = GetComponent<RectTransform>();
        initialSize = rectTransform.sizeDelta;
    }

    void Update()
    {
        if (isBreathing)
        {
            float pingPong = Mathf.PingPong(Time.time * breatheSpeed, 1);
            rectTransform.sizeDelta = Vector2.Lerp(initialSize, initialSize + new Vector2(breatheAmount, breatheAmount), pingPong);
        }
        else
        {
            rectTransform.sizeDelta = initialSize;  // Reset to initial size
        }
    }

    // Public methods to control breathing effect
    public void StartBreathing()
    {
        isBreathing = true;
    }

    public void StopBreathing()
    {
        isBreathing = false;
    }

    public IEnumerator BreatheForSeconds(float seconds)
    {
        StartBreathing();
        yield return new WaitForSeconds(seconds);
        StopBreathing();
    }
}
