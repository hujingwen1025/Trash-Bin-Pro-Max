# R07 motion software

Python 3.11+, NumPy and pyserial. The supplied configuration is uncalibrated and physically unqualified. Simulation never opens a serial port.

```sh
cd "Rev 07 - Servo Stewart Sorter/Software"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python sorter.py simulate
python -m unittest discover -s tests -v
```

The four-bin mapping and all dimensions are in `configuration.json`. Angles are servo shaft angles, after 1.8:1 reduction; model coordinates use millimetres, radians and kilograms. Twenty-three tests cover geometry/equilibrium, protocol framing/staging, known-start recovery, qualification, thermal/voltage/tracking faults, cooling, and blocked return when an item bridges the guide. They use a fake bus, not actual motors.

## Calibrate one disconnected servo first

Buy one real HTD-85H and its matched horn. Confirm the legacy 0x55 0x55 protocol, wiring, supply and adapter readback. Remove links and support the tray before actuation. Assign IDs with only one servo on the bus:

```sh
python sorter.py set-id --port /dev/ttyUSB0 --id 1 --new-id 2 --only-one-servo --links-disconnected --arm --confirm-clear
python sorter.py probe --port /dev/ttyUSB0
python sorter.py calibrate-angle --port /dev/ttyUSB0 --id 2 --angle 163.91976 --links-disconnected --arm --confirm-clear
```

Set IDs 1–6 separately; never assign all six to 2. The angle above is the supplied D2 active-pose reference only. Read every drive's value and crank reference from the guide/configuration. Verify direction with a small uncoupled movement. At the active fixture the upper joint plane is Z875.6, tray Z898.6. Attach links without force. Record all six actual lengths and anchor positions.

`calibrate.py --help` builds a **new** configuration from measured active servo angles and direction signs; it clears all qualification flags and never actuates. Do not overwrite the nominal configuration. Set `calibrated=true` in the measured copy only after physical geometry/direction checks. Keep `physical_qualification_passed=false` until the guide's physical tests pass.

## Attended commissioning

Start unloaded, with a physical DC disconnect and a restrained tray. Initially double lift/tilt times in the measured configuration.

```sh
python sorter.py dump --config measured_configuration.json --bin B1 --port /dev/ttyUSB0 --commissioning --arm --confirm-clear --log commissioning.jsonl
```

The program requires the tray to start at its known REST endpoint. It will ask for `EMPTY` before return, including a home command from a dump endpoint. Unknown startup poses, missing replies, excess temperature, voltage, tracking or timing errors latch a fault. There is no blind homing. Support the tray and recover with links disconnected if its position is unknown.

The temperature limit is 55°C, voltage range 10.5–12.6 V, tracking limit 5°, minimum cycle-start interval 30 s. All six targets are validated and staged before a broadcast start. Staging failure blocks that start. A serial failure after a command cannot undo a servo's existing queued/holding state.

Faults stop new commands and retain the last commanded holding positions while power remains. This is not a safety-rated torque-off controller. The independent physical emergency disconnect and deliberate manual restart are required. A host/USB failure may leave motors energized; do not rely on the program to make a jam safe.

## Later integration

`Controller.dump('B1', arm=True, clear=True)` accepts a real `Bus` and an independently validated `empty_check` callback. Returning false or having no callback blocks the return. Recognition, category mapping, presence/hand sensing and their validation are not implemented here. Keep human-supervised motion until that separate integration is qualified.

During motion, feedback uses two reads per50 ms frame: position from one rotating servo plus its temperature or voltage. At20 Hz each motor position is checked approximately every0.3 s and temperature/voltage every0.6 s; complete readback occurs outside timed segments. Tests model16 ms per USB reply plus7 ms staging, and confirm a slower adapter triggers a latched timing fault. This is a timing model, not a real-adapter result. Qualify the actual adapter at the intended update rate.
