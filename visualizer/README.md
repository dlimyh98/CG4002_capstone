# CG4002 Capstone Project - AR Game Visualizer

## Overview

This repository contains the Unity-based assets for the augmented reality (AR) visualizer component of the CG4002 capstone project. The visualizer, developed using the Unity Framework and Vuforia Engine, is a crucial part of an AR gaming experience that integrates real-time game states into a user interface. This interface is displayed on a mobile device mounted on the game weapon, providing players with immediate feedback on various game elements like player resources, opponent information, and in-game actions.

## Contents

The repository includes a variety of scripts written in C# for Unity, each serving a specific function in the AR visualizer:

- **ActionManager.cs**: Manages in-game actions and animations.
- **AmmoButton.cs**, **AmmoCountScript.cs**: Handle ammunition display and interactions.
- **BulletManager.cs**: Manages bullet-related events.
- **CG4002Mqtt.cs**: Handles MQTT client connectivity for real-time communication.
- **FistButton.cs**, **FistManager.cs**: Related to the 'fist' action in the game.
- **GamePlayer.cs**: Core script for player-related data and actions.
- **GlobalPlayerChoice.cs**: Manages global player choices and settings.
- **Grenade.cs**, **GrenadeButton.cs**, **GrenadeCountScript.cs**, **GrenadeManager.cs**: Scripts related to grenade functionalities.
- **HammerButton.cs**, **HammerManager.cs**: Pertaining to the 'hammer' action.
- **HealthBar.cs**, **HitScreen.cs**: Manage the player's health bar and hit reactions.
- **IconBreathing.cs**: For UI animations.
- **LogoutUI.cs**: Manages the logout screen and related functionalities.
- **PlayerChoiceUI.cs**: Handles the UI for choosing to play as either Player 1 or Player 2.
- **PlayerManager.cs**: Central script for managing player data and states.
- **PortalButton.cs**, **PortalManager.cs**: Related to portal functionalities in the game.
- **ReloadButton.cs**: Manages the reload action.
- **RespawnPlayerButton.cs**: Handles player respawn actions.
- **ScoreCountText.cs**: Displays and updates the score count.
- **SelfDamageButton.cs**: Manages self-damage actions.
- **ShieldBar.cs**, **ShieldButton.cs**, **ShieldCountScript.cs**, **ShieldManager.cs**: Scripts for managing shield-related functionalities.
- **SpearButton.cs**, **SpearManager.cs**: Pertaining to the 'spear' action.
- **SpiderWebButton.cs**, **SpiderWebManager.cs**: Related to the 'spider web' action.

## Visualizer Features

- **Real-Time Game State Rendering**: Displays player resources like health points, ammo count, shield status, and grenade count.
- **Opponent Information**: Shows the health and shield status of the opponent, including an animated skull on the detected QR code.
- **Scoreboard**: Displays the total kills versus the opponent's score.
- **Endgame Notification**: A logout screen appears when players exit the game.
- **Action Animations**: Visual representations of actions like hammer or grenade throws towards the opponent.
- **Damage Feedback**: The screen flashes red when the player takes damage, with intensity based on remaining health.
- **Player Stats Display**: Shows various player stats such as shield, health, ammo, and grenade count.



