Our team, *404 Not Found*, is led by Kartik, and our builders and programmers: Jerimiah, Aryan, Keshav, Aditya, and I (Robin). With a second place finish for the Term 2 In-House competition, we are aiming for first place at the next Robocup competition. I would like to acknoledge [@denyahnov](https://github.com/denyahnov) and his team for the IR seeker framework and giving us lots of inspiration throughout the term.

# Index
* ./remote/
  * client.py is what runs on the robot, which controls client-sided movement + receiving controller values
  * server.py is what you run on your laptop, so the robot can connect to it and an external controller communicates with it.
* ./src/
  * client.py runs on both robots
  * controller.py runs on the laptop, connects both robots through bluetooth

# Instructions for ./src/:
1. Go to "Wireless and Networks" on the EV3 and connect to the laptop through bluetooth. It should be connected if there is an address at the top of the display.
2. Search "cmd" on the laptop, enter `ipconfig /all` and scroll down until you see `Ethernet adapter Bluetooth Network Connection`. Copy the physical address, replacing the hyphens with colons. e.g. `6C-A1-00-05-72-DE` -> `6C:A1:00:05:72:DE`. Paste this into the "host_address" of the options.json file.
3. Run controller.py. Should say "Server is listening on addr:port".
4. Run client.py on the EV3. After 10-15 seconds, the window on the laptop should update to show a user interface.
<h3>Capable of connecting one or two robots.</h3>
- On the UI, change the slider and press the set speed button to change the speed of the respective robot.
- Activating the switch will turn on/off the automatic gameplay.
- The reset orientation button allows for reorientating the robot such as between rounds, on damaged callouts.
- The joystick acts as a remote control*. It will override automatic gameplay if the switch is activated.
<h5>*Remote control is not permitted in competitive play, however, it was only used for testing of robot stability, motor strength and calibration, and as a fun tool for my peers and I.</h5>

# Instructions for ./remote/:
1. <h6>connect the ev3 brick via bluetooth</h6>
  * scan for devices and connect to the laptop
  * make sure it says **status: connected**
2. <h6>open command prompt (cmd)</h6>
  * type in `ipconfig /all`
  * find the one that says bluetooth connection
  * copy the physical address
3. <h6>paste this into the options.json file, as host_address.</h6>
  * replace the **-** with **:** just like the one already in the file
  * save file
4. <h6>run server.py, make sure that it says Server listening on address:port.</h6>
  * make sure tkinter is installed
  * this can be done by entering `pip install tkinter` in terminal
5. <h6>once server is listening, run ROBIN.py on the ev3.</h6>
  * if all goes well, after around 10 seconds the gui should open on the laptop and you can control it with the joystick on the top right

# Features
- Joystick remote control in ./remote/
- Holonomic wheel system
- Capable of scoring consistently

# To implement:
- Communication between both robots
- Controller for turning on and off robots quicker (was a major problem at the state competition as the robot took up to 15 seconds to boot up)
- Making a robot which can travel around the field at top speed and accuracy.
<br>

# Flowchart (deprecated)
![Flowchart](/assets/img1.png?raw=true "Flowchart")
![Defense](/assets/img2.png?raw=true "Defense")
# Pseudocode (depracted, check code)
![Pseudocode](/assets/img3.png?raw=true "Pseudocode")
