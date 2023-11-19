using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Collections.Generic;

public class HammerManager : ActionManager
{
    public GameObject hammerPrefabOverride;
    public float speedOverride;
    public GameObject effectPrefabOverride;
    public int damageOverride;

    public override GameObject actionPrefab => hammerPrefabOverride;
    public override float actionSpeed => speedOverride;
    public override GameObject effectPrefab => effectPrefabOverride;
    public override int actionDamage => damageOverride;

    private string CurrentPlayerName => GlobalPlayerChoice.Instance.GetPlayerName(CurrentPlayer);
    private string OpponentName => GlobalPlayerChoice.Instance.GetPlayerName(Opponent);

    public override void HandleSpecificMessage(M2MqttUnity.CG4002.GameAction gameAction)
    {
        if (gameAction.action_type == "hammer" && gameAction.player_id == CurrentPlayerName && gameAction.target_id == OpponentName)
        {
            PerformAction();
        }
    }

    public override void PublishSpecificAction(bool hit)
    {
        PublishAction("hammer", CurrentPlayer.name, Opponent.name, hit);
    }
}