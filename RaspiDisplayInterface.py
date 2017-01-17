import sys, fcntl, struct, socket, os, sqlite3, time, signal, datetime
import Adafruit_DHT, Adafruit_CharLCD
import threading, Queue
import env_logger_config


lcd = Adafruit_CharLCD.Adafruit_CharLCDPlate()

q = Queue.Queue(1)

stopevt = threading.Event()

def query_db(query, args=()):
	con = sqlite3.connect(env_logger_config.dbfile)
	cur = con.cursor()
	cur.execute(query, args)
	rv = cur.fetchall()
	cur.close()
	con.close()
	return rv


def lcd_environment():
	humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, env_logger_config.gpio_port)			
	if humidity is not None and temperature is not None:
		lcd.clear()
		lcd.message('Temp={0:0.1f}*C\nHumidity={1:0.1f}%'.format(temperature, humidity))
	else:
		lcd.clear()
		lcd.message('Read error\nTrying again...')

def lcd_datetime():
	i = datetime.datetime.now()
	lcd.clear()
	lcd.message(i.strftime('%Y/%m/%d\n%H:%M:%S'))

def get_ip_address(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])
ipaddr = get_ip_address('eth0')




def lcd_message(message):
	if message == Adafruit_CharLCD.SELECT:
		lcd.clear()
		lcd.message(ipaddr)
	elif message == Adafruit_CharLCD.DOWN:
		last_entry = "SELECT * FROM env_log ORDER BY DateTime DESC LIMIT 1"
		rvs = query_db(last_entry)
		last_message = 'DBTemp={0:0.1f}*C\nDBHumidity={1:0.1f}%'.format(rvs[0][1], rvs[0][2])
		lcd.clear()
		lcd.message(last_message)



class displaydata(threading.Thread):
	def run(self):
		i = 0
		while True:
			if stopevt.is_set():
				lcd.clear()
				return
			if i%2==0:
				lcd_datetime()
			else:
				lcd_environment()
			i+=1
			time.sleep(env_logger_config.display_delay) 
			try:
				message = q.get(False)				
				#print('got message ' + str(message))
				lcd_message(message)
				time.sleep(env_logger_config.display_delay)
			except Queue.Empty:
				#print('Queue is empty')
				pass

class pollkeys(threading.Thread):
	def run(self):
		#print('start reading keyboard')
		#print('Queue size: ' + str(q.qsize()))
		while True:
			try:
				#print('trying to read keyboard')
				if stopevt.is_set():
					return
				if lcd.is_pressed(Adafruit_CharLCD.SELECT):
					print('pressed lcd.SELECT')
					q.put(Adafruit_CharLCD.SELECT, False)
				elif lcd.is_pressed(Adafruit_CharLCD.DOWN):
					print('pressed lcd.DOWN')
					q.put(Adafruit_CharLCD.DOWN, False)
			except Queue.Full:
				#print('Queue is full')
				pass
			except:
				print('caught something else: ', sys.exc_info()[0])
				print(sys.exc_info()[1])
			#print('sleep in reading keyboard')
			time.sleep(env_logger_config.poll_delay)
		print('should never get here')

def handle_sigint(signum, frame):
	print('caught SIGINT; exiting')
	stopevt.set()

def run():
	print('Starting on ' + ipaddr)
	print('Set SIGINT handler')
	signal.signal(signal.SIGINT, handle_sigint)
	displaydata().start() 
	pollkeys().start()
	while True:
		if stopevt.is_set():
			return
		time.sleep(1)

if __name__ == '__main__':
	run()
