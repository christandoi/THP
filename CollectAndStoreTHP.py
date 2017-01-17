#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, Adafruit_DHT, os, os.path, time, datetime, sqlite3
from bmp183 import bmp183
import env_logger_config

con = sqlite3.connect(env_logger_config.dbfile)
sensor = Adafruit_DHT.AM2302

insert_sql = """INSERT INTO env_log (DateTime, Temperature, Humidity) VALUES (?,?,?) """
		
while True:
	
	now = datetime.datetime.now()	
	formtime = str(now.strftime('%Y-%m-%d %H:%M:%S'))
	bmp = bmp183()

	with con:
	   	humidity, temperature = Adafruit_DHT.read_retry(sensor, env_logger_config.gpio_port)
		bmp.measure_pressure()
		pressure = bmp.pressure / 100
		print 
		cur = con.cursor()
		data =  [formtime,temperature,humidity,pressure]
		cur.execute(insert_sql, data)
	con.commit()
		
	print "Commit: %s %.1f %.1f" % tuple(data)
	time.sleep(env_logger_config.log_interval)
