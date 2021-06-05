#!/usr/bin/python3
# Userspace smart fan control daemon for amdgpu

import glob, time, os.path

hwmon = next(i for i in glob.iglob('/sys/class/hwmon/hwmon*') if open(os.path.join(i, 'name')).read().strip() == 'amdgpu')
TEMP_INPUT = f'{hwmon}/temp1_input'
FAN_INPUT = f'{hwmon}/fan1_input'
PWM_VALUE = f'{hwmon}/pwm1'
PWM_MODE = f'{hwmon}/pwm1_enable'

FAN_START = 50  # minimum speed at which fans steadily spin up
FAN_STOP = 42   # maximum speed at which fans still spin

#TEMP_MIN = 40
#TEMP_MAX = 75

CURVE = {
	0: 0,
	35: 91,
	40: 109,
	50: 127,
	65: 153,
	75: 255,
}

TEMPS = tuple(CURVE)

def log(*args, **kwargs): pass #print(*args, **kwargs)

def read_temp(): return int(open(TEMP_INPUT).read())/1000
def read_speed(): return int(open(FAN_INPUT).read())
def write_speed(v): open(PWM_VALUE, 'w').write(str(v))

def set_speed(v):
	global fan_running

	v = int(v)

	log(f"Setting speed {v}")

	open(PWM_MODE, 'w').write('1') # TODO FIXME

	if (v < FAN_STOP and fan_running is True):
		write_speed(0)
		speed = read_speed()
		log(" waiting for fan to stop...", end=' ', flush=True)
		while (speed >= (speed := read_speed())):
			time.sleep(0.1)
		log()
		fan_running = False
	elif (v > FAN_STOP and fan_running is False):
		write_speed(FAN_START)
		speed = read_speed()
		log(" waiting for fan to start...", end=' ', flush=True)
		while (read_speed() <= speed):
			time.sleep(0.1)
		log()
		fan_running = True

	write_speed(v)

def main():
	global fan_running
	fan_running = None

	open(PWM_MODE, 'w').write('1')
	write_speed(0)

	try:
		while (True):
			temp = read_temp()

			if (temp < TEMPS[0]): set_speed(0)
			else:
				for ii, i in enumerate(TEMPS):
					if (temp >= i): continue
					lt, ht = TEMPS[ii-1], TEMPS[ii]
					lv, hv = CURVE[lt], CURVE[ht]
					log(f"Temp {int(temp)}°C.", end=' ')
					set_speed(((temp-lt)*(hv-lv) // (ht-lt)) + lv)
					break
			#elif (temp <= TEMP_MAX): set_speed((temp-TEMP_MIN)*255 // (TEMP_MAX-TEMP_MIN)) # TODO
			#else: set_speed(255)

			time.sleep(1)
	except KeyboardInterrupt: exit()
	finally: #open(PWM_MODE, 'w').write('2')
		write_speed(0)

if (__name__ == '__main__'): exit(main())

# by Sdore, 2021
