using System.Collections;
using UnityEngine;
using Vuforia;
using System.Collections.Generic;

public class BulletManager : ActionManager
{
    public GameObject bulletPrefabOverride;
    public float speedOverride;
    public GameObject hitEffectPrefabOverride;  // Assuming you have a hit effect for bullets
    public int bulletDamageOverride;

    public override GameObject actionPrefab => bulletPrefabOverride;
    public override float actionSpeed => speedOverride;
    public override GameObject effectPrefab => hitEffectPrefabOverride;
    public override int actionDamage => bulletDamageOverride;

    private string CurrentPlayerName => GlobalPlayerChoice.Instance.GetPlayerName(CurrentPlayer);
    private string OpponentName => GlobalPlayerChoice.Instance.GetPlayerName(Opponent);

    public override void PerformAction()
    {
        // Check if ammo count is > 0 before performing action
        if (CurrentPlayer.currentBullets <= 0)
        {
        //    SkipAction("No ammo left!");
            return;
        }

        base.PerformAction();  // Call the base class's PerformAction method

        // Decrement ammo count after firing bullet
        // Commenting this out after individual component testing
        // CurrentPlayer.UseBullet();
    }

    public override void HandleSpecificMessage(M2MqttUnity.CG4002.GameAction gameAction)
    {
        if (gameAction.action_type == "gun" && gameAction.player_id == CurrentPlayerName && gameAction.target_id == OpponentName)
        {
            PerformAction();
        }
    }

    public override void PublishSpecificAction(bool hit)
    {
       // PublishAction("bullet", CurrentPlayer.name, Opponent.name, hit);  // Assuming players are identified by their names
    }

    public override void SkipAction(string reason)
    {
        // Child-specific logic
        base.SkipAction(reason);  // Call the base class's SkipAction method
    }
}
