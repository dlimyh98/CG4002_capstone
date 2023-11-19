using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GamePlayer : MonoBehaviour
{
    public int maxHealth = 100;
    public int currentHealth;

    public int maxShield = 30;
    public int currentShield;

    public int maxBullets = 6;
    public int currentBullets;

    public int maxShields = 3;
    public int currentShields;

    public int maxGrenades = 2;
    public int currentGrenades;

    public int deaths;

    public bool isShieldActive = false;

    public IconBreathing shieldIconBreathingCurrentPlayer;
    public IconBreathing reloadIconBreathingCurrentPlayer;
    public IconBreathing shieldIconBreathingOpponent;

    private IconBreathing ShieldIconBreathing
    {
        get
        {
            return this == GlobalPlayerChoice.Instance.currentPlayer ? shieldIconBreathingCurrentPlayer : shieldIconBreathingOpponent;
        }
    }

    void Start()
    {
        Respawn();
    }

    public void TakeDamage(int damage)
    {
        if (isShieldActive)
        {
            currentShield -= damage;
            if (currentShield <= 0)
            {
                damage = -currentShield;
                currentShield = 0;
                isShieldActive = false;
                ShieldIconBreathing.StopBreathing(); // Deactivate breathing effect
            }
            else
            {
                damage = 0;
            }
        }

        currentHealth -= damage;

        if (currentHealth <= 0)
        {
            deaths++;
            Respawn();
        }
    }

    public void ActivateShield()
    {
        if (currentShields > 0)
        {
            isShieldActive = true;
            currentShield = maxShield;
            currentShields--;
            ShieldIconBreathing.StartBreathing(); // Activate breathing effect
        }
    }   

    public void UseBullet()
    {
        if (currentBullets > 0)
        {
            currentBullets--;
        }
    }

    public void UseGrenade()
    {
        if (currentGrenades > 0)
        {
            currentGrenades--;
        }
    }


    public void ReloadBullets()
    {
        currentBullets = maxBullets;
        StartCoroutine(reloadIconBreathingCurrentPlayer.BreatheForSeconds(3f));
    }

    public int GetDeaths()
    {
        return deaths;
    }

    public void Respawn()
    {
        currentHealth = maxHealth;
        currentShield = 0;  // Reset to 0
        isShieldActive = false;  // Deactivate shield
        currentBullets = maxBullets;
        currentShields = maxShields;
        currentGrenades = maxGrenades;
        ShieldIconBreathing.StopBreathing();
    }

    private void NotifyAll()
    {
        // Uncomment these if you are using events
        // OnHealthChanged?.Invoke(currentHealth);
        // OnShieldChanged?.Invoke(currentShield);
        // OnBulletChanged?.Invoke(currentBullets);
        // OnShieldsChanged?.Invoke(currentShields);
    }
}
