Our team, *404 Not Found*, is led by Kartik, and our builders and programmers: Jerimiah, Aryan, Keshva, Aditya, and I (Robin). With a second place finish for the Term 2 In-House competition, we are aiming for first place at the next Robocup competition. I would like to acknoledge [@denyahnov](https://github.com/denyahnov) and his team for the IR seeker framework and giving us lots of inspiration throughout the term.

# Index
  * ROBIN.py is what runs on the robot, which controls client-sided movement + receiving controller values
  * server.py is what you run on your laptop, so the robot can connect to it and an external controller communicates with it.

# Instructions:
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
- Joystick remote control
- Holonomic wheel system
- Ball-following capabilities

# To implement:
- Compass, motion*, and ultrasonic sensors.
- Attacking and defensive strategies
- Communication between both robots
- Second robot script for the other robot which uses two IRs instead of an IR seeker.
*Still not sure what this means, probably referring to ultrasonic detection of the walls.

# Flowchart
![Flowchart](/assets/img1.png?raw=true "Flowchart")
![Defense](/assets/img2.png?raw=true "Defense")