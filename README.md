# Index
ROBIN.py is what runs on the robot, which controls sending sensor values.
server.py is what you run on your laptop, so the robot can connect to it, and it get the sensor values and put it into a nice GUI :)

instructions:
1. connect the ev3 brick via bluetooth
	scan for devices and connect to the laptop
	make sure it says status: connected
2. open command prompt
	type in 'ipconfig /all'
	find the one that says bluetooth connection
	copy the physical address
3. paste this into the options.json file, as host_address.
	replace the - with : just like the one already in the file
	save file
4. run server.py, make sure that it says server listening on address:port.
	make sure tkinter is installed
	this can be done by entering 'pip install tkinter' in terminal
5. once server is listening, run ROBIN.py on the ev3.
	if all goes well, after around 10 seconds the gui should open on the laptop and you can control it with the joystick on the top right