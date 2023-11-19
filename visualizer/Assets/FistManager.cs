using System.Collections;
using UnityEngine;
using Vuforia;
using System.Collections.Generic;

public class FistManager : ActionManager
{
    public GameObject fistPrefabOverride;
    public float speedOverride;
    public GameObject effectPrefabOverride;
    public int damageOverride;

    public override GameObject actionPrefab => fistPrefabOverride;
    public override float actionSpeed => speedOverride;
    public override GameObject effectPrefab => effectPrefabOverride;
    public override int actionDamage => damageOverride;

    private string CurrentPlayerName => GlobalPlayerChoice.Instance.GetPlayerName(CurrentPlayer);
    private string OpponentName => GlobalPlayerChoice.Instance.GetPlayerName(Opponent);

    public override void HandleSpecificMessage(M2MqttUnity.CG4002.GameAction gameAction)
    {
        if (gameAction.action_type == "punch" && gameAction.player_id == CurrentPlayerName && gameAction.target_id == OpponentName)
        {
            PerformAction();
        }
    }

    public override void PublishSpecificAction(bool hit)
    {
        PublishAction("punch", CurrentPlayer.name, Opponent.name, hit);
    }
}