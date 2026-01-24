@echo off
set RUN_ID=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%%TIME:~0,2%%TIME:~3,2%
python orchestrator\Gatekeeper.py %RUN_ID%
