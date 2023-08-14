Traceback (most recent call last):
  File "/home/robot/Soccer Robot/src/ROBIN.py", line 47, in <module>
    MediumMotor(OUTPUT_D)  # LEFT   [3]
  File "/usr/lib/python3/dist-packages/ev3dev2/motor.py", line 1134, in __init__
    super(MediumMotor, self).__init__(address, name_pattern, name_exact, driver_name=['lego-ev3-m-motor'], **kwargs)
  File "/usr/lib/python3/dist-packages/ev3dev2/motor.py", line 395, in __init__
    super(Motor, self).__init__(self.SYSTEM_CLASS_NAME, name_pattern, name_exact, **kwargs)
  File "/usr/lib/python3/dist-packages/ev3dev2/__init__.py", line 223, in __init__
    chain_exception(DeviceNotFound("%s is not connected." % self), None)
  File "/usr/lib/python3/dist-packages/ev3dev2/__init__.py", line 54, in chain_exception
    raise exception from cause
ev3dev2.DeviceNotFound: MediumMotor(ev3-ports:outD) is not connected.
