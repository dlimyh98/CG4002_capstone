# Hardware

## Arduino dependencies
Ensure that you add the `hardware/libraries` folder to wherever your own Arduino's `libraries` folder is.  
  This ensures that the 3rd party libraries I am using are available to you as well (and that my .ino files can compile on your system).

## Guide for AI data collection
Available under `data_collection/README.md`.  
  Static and dynamic movements available under `data_collection/data_mix`

# Internal Communications

## Arduino
Ensure that the hardware Arduino dependencies mentioned above have been fulfilled before flashing the respective beetles.

## Main code
Ensure all python packages are installed.
  run with ```python3 main.py```

# External Communications

## Evaluation Server
Ensure the `server_address` variable in the `helper.js` file located in the `html` folder in the evaluation server code is set to the right address.
  For example, if the evaluation server is hosted on the Ultra96, then `server_address` should be set to the Ultra96's IP address.

## Main code
### With Eval Server
Open two terminals, one with path `external_communications/eval_server/server`.
  Run the evaluation server: `python WebSocketServer.py`.
    Open `index.html` inside `eval_server/html` to interface with the evaluation server.

For the second terminal, `cd` into `external_communications/Ultra96`.
  For the AI classification purpose, this terminal must be ran in root. Run the following commands: `sudo -s`, then `source run.sh`.
    Run with `python main.py`.

### Without Eval Server (free-flow)
Only one terminal is needed, with path `external_comunications/2p_freeflow`.
  For the AI classification purpose, this terminal must be ran in root. Run the following commands: `sudo -s`, then `source run.sh`.
  Run with `python main.py`.
