import sqlite3, os
from flask import g, Flask, send_file

import env_logger_config

app = Flask(__name__)

#fetches database
def get_db():
	db = getattr(g, '_database', None)
	print db
	if db is None:
		db = g._database = sqlite3.connect(env_logger_config.dbfile)
		db.row_factory = sqlite3.Row
	return db

@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

def query_db(query, args=()):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return rv

#start server
@app.route('/')
def display_dtth_html():
	rvs = query_db("SELECT * FROM env_log ORDER BY DateTime DESC LIMIT 1")
	retval = '<style>table,th,td{border:1px solid black;}</style>\n'
	retval += '<table><tr><th>Date</th><th>Temperature</th><th>Humidity</th></tr>\n'
	for rv in rvs:
		retval += '<tr><td>%s</td><td>%.1f</td><td>%.1f</td></tr>\n' % (rv[0], rv[1], rv[2])	
	retval += '</table>\n'
	return retval

@app.route('/csv')
def display_dtth_csv():
	rvs = query_db("SELECT * FROM env_log ORDER BY DateTime DESC LIMIT 1")
	retval = ','.join(map(str,rvs[0]))
	print retval
	return retval

@app.route('/database')
def ret_database_file():
	file = open(env_logger_config.dbfile, 'rb')
	response = send_file(file, as_attachment=True, attachment_filename=os.path.basename(env_logger_config.dbfile))
	return response

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80, debug=True)
