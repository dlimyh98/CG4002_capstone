using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GlobalPlayerChoice : MonoBehaviour
{
    public static GlobalPlayerChoice Instance; // Singleton instance

    public GamePlayer player1;
    public GamePlayer player2;
    public GamePlayer currentPlayer;

    public GamePlayer opponent
    {
        get
        {
            if (currentPlayer == player1)
                return player2;
            else if (currentPlayer == player2)
                return player1;
            else
                return null; // This scenario should not occur, but is here just in case
        }
    }

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(this.gameObject); // Don't destroy this object when a new scene loads
        }
        else
        {
            Destroy(this.gameObject);
        }
    }

    public string GetPlayerName(GamePlayer player)
    {
        if (player == player1)
            return "player1";
        else if (player == player2)
            return "player2";
        else
            return null;  // This should ideally never be reached.
    }
}
