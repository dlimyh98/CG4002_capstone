using System.Collections;
using UnityEngine;
using Vuforia;
using System.Collections.Generic;

public class GrenadeManager : ActionManager
{
    public GameObject grenadePrefabOverride;
    public float speedOverride;
    public GameObject explosionPrefabOverride;
    public int explosionDamageOverride;

    public override GameObject actionPrefab => grenadePrefabOverride;
    public override float actionSpeed => speedOverride;
    public override GameObject effectPrefab => explosionPrefabOverride;
    public override int actionDamage => explosionDamageOverride;

    private string CurrentPlayerName => GlobalPlayerChoice.Instance.GetPlayerName(CurrentPlayer);
    private string OpponentName => GlobalPlayerChoice.Instance.GetPlayerName(Opponent);

    public override void PerformAction()
    {
        Debug.Log("PerformAction called in GrenadeManager");
        
        if (CurrentPlayer.currentGrenades <= 0)
        {
            // SkipAction("No grenades left.");
            return;
        }

        base.PerformAction();  // Call the base class's PerformAction method
        
        //Commenting this out after individual component testing
        //CurrentPlayer.UseGrenade();  // Decrement grenade count after using grenade
    }

    public override void HandleSpecificMessage(M2MqttUnity.CG4002.GameAction gameAction)
    {
        Debug.Log("HandleSpecificMessage called in GrenadeManager");

        if (gameAction.action_type == "grenade" && gameAction.player_id == CurrentPlayerName && gameAction.target_id == OpponentName)
        {
            PerformAction();
        }
    }

    public override void PublishSpecificAction(bool hit)
    {
        PublishAction("grenade", CurrentPlayerName, OpponentName, hit);
    }

    public override void SkipAction(string reason)
    {
        // Child-specific logic
        base.SkipAction(reason);  // Call the base class's SkipAction method
    }
}
