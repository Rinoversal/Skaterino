@echo off
rem Re-dumps skate.'s physics tuning with ReSkate Studio's CLI. Edit the two paths if yours differ.
set "CLI=C:\Program Files (x86)\Steam\steamapps\common\Skate\ReSkate Studio\reskate_cli.exe"
set "GAME=C:\Program Files (x86)\Steam\steamapps\common\Skate"
"%CLI%" ebx-values "%GAME%" gameplay/skatephysicstuning > "%~dp0skatephysicstuning.txt"
findstr /i "JumpMaxHeight JumpMinHeight WipeoutMaxLandingSpeedDown WipeoutMaxLandingSpeedHoriz SpeedWobbleStartSpeed SteeringVsSpeedMaxSpeed WheelRadius DeckMidLength WallRideMinSpeed WallRideMaxTime" "%~dp0skatephysicstuning.txt"
echo Put the values above into skate_limits.json.
pause
