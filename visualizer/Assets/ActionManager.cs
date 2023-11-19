using System.Collections;
using UnityEngine;
using Vuforia;
using Newtonsoft.Json;
using System.Collections.Generic;
using M2MqttUnity.CG4002;
using System;
using System.Collections.Concurrent;

public abstract class ActionManager : MonoBehaviour
{
    public abstract GameObject actionPrefab { get; }
    public abstract float actionSpeed { get; }
    public abstract GameObject effectPrefab { get; }
    public abstract int actionDamage { get; }
    public Transform target;
    public Camera mainCamera;
    public float spawnDistanceFromCamera;
    public Vector3 initialOrientationOffset = Vector3.zero;
    public GamePlayer player1;
    public GamePlayer player2; // Reference to the GamePlayer script for player 2
    public CG4002Mqtt mqttClient; // Reference to the MQTT client

    public DefaultObserverEventHandler observerEventHandler;  // Drag your DefaultObserverEventHandler component here in the editor
    protected bool isTargetFound = false;

    public GamePlayer CurrentPlayer 
    {
        get 
        {
            return GlobalPlayerChoice.Instance.currentPlayer;
        }
    }

    public GamePlayer Opponent
    {
        get
        {
            return CurrentPlayer == player1 ? player2 : player1;
        }
    }

    private void Start()
    {
        if (observerEventHandler != null)
        {
            observerEventHandler.OnTargetFound.AddListener(TargetFound);
            observerEventHandler.OnTargetLost.AddListener(TargetLost);
            mqttClient.OnActionMessage += HandleActionMessage;
        }
    }

    private void OnDestroy()
    {
        if (observerEventHandler != null)
        {
            observerEventHandler.OnTargetFound.RemoveListener(TargetFound);
            observerEventHandler.OnTargetLost.RemoveListener(TargetLost);
            mqttClient.OnActionMessage -= HandleActionMessage;
        }
    }

    public void TargetFound()
    {
        Debug.Log("Target Found!");
        isTargetFound = true;
    }

    public void TargetLost()
    {
        Debug.Log("Target Lost!");
        isTargetFound = false;
    }

    public virtual void PerformAction()
    {
        Debug.Log("PerformAction called in ActionManager");
        if (!isTargetFound)
        {
            Debug.LogWarning("Target not found. Cannot perform action.");
            PublishSpecificAction(false);
            return;
        }

        Vector3 spawnPosition = mainCamera.transform.position + mainCamera.transform.forward * spawnDistanceFromCamera;
        
        // Compute the direction from spawn position to target
        Vector3 directionToTarget = (target.position - spawnPosition).normalized;

        // Create a rotation that looks in the direction of the target
        Quaternion spawnRotation = Quaternion.LookRotation(directionToTarget);

        // Apply the initial orientation offset
        spawnRotation *= Quaternion.Euler(initialOrientationOffset);

        // Use the combined rotation for instantiation
        GameObject actionObject = Instantiate(actionPrefab, spawnPosition, spawnRotation);
        StartCoroutine(FlyAndActivate(actionObject, target, actionSpeed));

        PublishSpecificAction(true);
    }
    
    private IEnumerator FlyAndActivate(GameObject actionObject, Transform target, float speed)
    {
        Vector3 startPosition = actionObject.transform.position;
        Vector3 endPosition = target.position;
        float journeyLength = Vector3.Distance(startPosition, endPosition);
        float startTime = Time.time;

        float distanceCovered, fractionOfJourney;

        while (Vector3.Distance(actionObject.transform.position, endPosition) > 0.1f)
        {
            distanceCovered = (Time.time - startTime) * speed;
            fractionOfJourney = distanceCovered / journeyLength;
            actionObject.transform.position = Vector3.Lerp(startPosition, endPosition, fractionOfJourney);

            yield return null;
        }

        // Instantiate effect and destroy it after some time
        GameObject effect = Instantiate(effectPrefab, target.position, Quaternion.identity);
        Destroy(effect, 3f);

        Destroy(actionObject);

        // Apply damage, commenting this out after individual component
        //Opponent.TakeDamage(actionDamage);
    }

    private void HandleActionMessage(M2MqttUnity.CG4002.GameAction gameAction)
    {
        Debug.Log($"HandleActionMessage called in ActionManager. Action Type: {gameAction.action_type}");

        // Check if the target is the Opponent
        if (gameAction.target_id == GlobalPlayerChoice.Instance.GetPlayerName(Opponent))
        {
            HandleSpecificMessage(gameAction); // Delegate the handling to child classes
        }
    }

    // Publishes the action to MQTT
    public void PublishAction(string actionType, string playerId, string targetId, bool hit)
    {
        if (mqttClient == null)
        {
            Debug.LogWarning("MQTT client reference not set in ActionManager.");
            return;
        }

        var payload = new
        {
            type = "confirmation",
            player_id = playerId,
            action_type = actionType,
            target_id = targetId,
            hit = hit
        };

        string jsonPayload = JsonConvert.SerializeObject(payload);
        mqttClient.messagePublish = jsonPayload;
        mqttClient.Publish();
    }

    public virtual void SkipAction(string reason)
    {
        Debug.Log($"Action skipped: {reason}");
        // Publish the skip action with a reason to MQTT
        PublishSkipAction(reason);
    }

    public void PublishSkipAction(string reason)
    {
        if (mqttClient == null)
        {
            Debug.LogWarning("MQTT client reference not set in ActionManager.");
            return;
        }

        var payload = new
        {
            type = "action_skipped",
            player_id = GlobalPlayerChoice.Instance.GetPlayerName(CurrentPlayer),
            reason = reason
        };

        string jsonPayload = JsonConvert.SerializeObject(payload);
        mqttClient.messagePublish = jsonPayload;
        mqttClient.Publish();
    }


    public virtual void PublishSpecificAction(bool hit)
    {
        // This method will be overridden by each child class.
    }

    public virtual void HandleSpecificMessage(M2MqttUnity.CG4002.GameAction gameAction)
    {
        // This method will be overridden by each child class.
    }
}
