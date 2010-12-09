#!/usr/bin/python

import sys
import commands
import re
import getopt
import ConfigParser
import signal
import time
#import argparse

options = {
  'apache': False, 
  'mysql': False, 
  'config': 'server-watch.config',
  'delimeter': '\t',
  'delay': 1.0,
}
config = {}

#
# Get system load
#
def getLoad():
  try:
    loadavgProc = open('/proc/loadavg', 'r')
    lines = loadavgProc.readlines()
    loadavgProc.close()
  except IOError, e:
    # Log an error or something
    return False

  lines = lines[0]
  vals = lines.split(' ')

  data = {
    '1': {'title': '1MinLoad', 'value': vals[0]},
    '2': {'title': '5MinLoad', 'value': vals[1]},
    '3': {'title': '15MinLoad', 'value': vals[2]},
  }
  return data

#
# Get various CPU states
#
def getCpu():
  command = "mpstat 1 1"
  output = commands.getoutput(command)
  lines = output.split('\n')
  result = re.findall(r'([0-9]+[\.]\d+)', lines[3])

  data = {
    '4': {'title': '%user', 'value': result[0]},
    '5': {'title': '%nice', 'value': result[1]},
    '6': {'title': '%sys', 'value': result[2]},
    '7': {'title': '%iowait', 'value': result[3]},
    '8': {'title': '%irq', 'value': result[4]},
    '9': {'title': '%soft', 'value': result[5]},
    '10': {'title': '%steal', 'value': result[6]},
    '11': {'title': '%idle', 'value': result[7]},
  }
  return data

#
# Get memory usage
#
def getMem():
  try:
    meminfoProc = open('/proc/meminfo', 'r')
    lines = meminfoProc.readlines()
    meminfoProc.close()
  except IOError, e:
    # Log an error or something
    return False

  # We run this several times so one-time compile now
  regexp = re.compile(r'([0-9]+)') 
  meminfo = {}

  # Loop through and extract the numerical values
  for line in lines:
    values = line.split(':')
    match = re.search(regexp, values[1])
    if match != None:
      meminfo[str(values[0])] = match.group(0)

  physTotal = int(meminfo['MemTotal'])
  physFree = int(meminfo['MemFree'])
  physUsed = physTotal - physFree
  swapTotal = int(meminfo['SwapTotal'])
  swapFree = int(meminfo['SwapFree'])
  swapUsed = swapTotal - swapFree

  memData = {}

  # Convert to MB
  memData['physFree'] = physFree / 1024
  memData['physUsed'] = physUsed / 1024
  memData['cached'] = int(meminfo['Cached']) / 1024
  memData['swapFree'] = swapFree / 1024
  memData['swapUsed'] = swapUsed / 1024

  data = {
    '12': {'title': 'MemFree', 'value': physFree / 1024},
    '13': {'title': 'MemUsed', 'value': physUsed / 1024},
    '14': {'title': 'SwapFree', 'value': swapFree / 1024},
    '15': {'title': 'SwapUsed', 'value': swapUsed / 1024},
    '16': {'title': 'Cached', 'value': int(meminfo['Cached']) / 1024},
  }
  return data

#
# Get the number of apache processes
#
def getApache():
  command = "pgrep httpd | wc -l"
  output = commands.getoutput(command)
  data = {
    '17': {'title': 'ApacheProcesses', 'value': output},
  }

  return data

#
# Get some various mysql data
#
def getMysql():
  mysqlData = {}
  
  import MySQLdb
  
  # Check for mysql configs 
  mysqlHost = config.get('mysql', 'host')
  mysqlUser = config.get('mysql', 'user')
  mysqlPass = config.get('mysql', 'password')

  try:
    db = MySQLdb.connect(mysqlHost, mysqlUser, mysqlPass)
  except MySQLdb.OperationalError, message:
    print 'Failed to connect to MySQL: ' + str(message)
    return False

  cursor = db.cursor()
  cursor.execute('SHOW GLOBAL STATUS LIKE "Created_tmp_disk_tables"')
  result = cursor.fetchone()
  mysqlData['createdTmpDiskTables'] = float(result[1])

  cursor = db.cursor()
  cursor.execute('SHOW STATUS LIKE "Max_used_connections"')
  result = cursor.fetchone()
  mysqlData['maxUsedConnections'] = float(result[1])

  cursor = db.cursor()
  cursor.execute('SHOW STATUS LIKE "Open_files"')
  result = cursor.fetchone()
  mysqlData['openFiles'] = float(result[1])

  cursor = db.cursor()
  cursor.execute('SHOW GLOBAL STATUS LIKE "Slow_queries"')
  result = cursor.fetchone()
  mysqlData['slowQueries'] = float(result[1])

  cursor = db.cursor()
  cursor.execute('SHOW STATUS LIKE "Table_locks_waited"')
  result = cursor.fetchone()
  mysqlData['tableLocksWaited'] = float(result[1])

  cursor = db.cursor()
  cursor.execute('SHOW STATUS LIKE "Threads_connected"')
  result = cursor.fetchone()
  mysqlData['threadsConnected'] = float(result[1])

  try:
	  cursor = db.cursor(MySQLdb.cursors.DictCursor)
	  cursor.execute('SHOW SLAVE STATUS')
	  result = cursor.fetchone()
  except MySQLdb.OperationalError, message:
	  result = None

  if result != None:
	  mysqlData['secondsBehindMaster'] = result['Seconds_Behind_Master']
  else:
	  mysqlData['secondsBehindMaster'] = -1

  data = {
    '18': {'title': 'MysqlUsedConnections', 'value': mysqlData['maxUsedConnections']},
    '19': {'title': 'MysqlCreatedTmpDiskTables', 'value': mysqlData['createdTmpDiskTables']},
    '20': {'title': 'MysqlOpenFiles', 'value': mysqlData['openFiles']},
    '21': {'title': 'MysqlSlowQueries', 'value': mysqlData['slowQueries']},
    '22': {'title': 'MysqlTableLocksWaited', 'value': mysqlData['tableLocksWaited']},
    '23': {'title': 'MysqlThreads', 'value': mysqlData['threadsConnected']},
    '24': {'title': 'MysqlSecondsBehind', 'value': mysqlData['secondsBehindMaster']},
  }

  return data


#
# Output a header row based on the configured log format
#
def outputHeader(data):
  header = []
  for key in config.get('log', 'format').split(' '):
    if key in data:
      header.append(data[key]['title'])

  print options['delimeter'].join(header)

#
# Output a row of data based on the configured log format
#
def outputRow(data):
  row = []
  for key in config.get('log', 'format').split(' '):
    if key in data:
      row.append(data[key]['value'])

  r = map(str, row)
  print options['delimeter'].join(r)


#
# Main processing loop, print log rows until the process is killed
#
def main(args):
  lines = 0  

  while True:
    data = {}

    data.update(getLoad())
    data.update(getCpu())
    data.update(getMem())

    if options['apache']:
      data.update(getApache())

    if options['mysql']:
      data.update(getMysql())

    if lines == 0:
      outputHeader(data)

    outputRow(data)
    lines += 1
    
    # Subtract 1 b/c mpstat for getCPu already delays for 1 second
    time.sleep(options['delay'] - 1)

#
# print usage
#
def usage():
  print 'See someone that knows how to use this tool, or read the code'
  print 'python serverWatch.py [-a|-m|-c <config file>|-d <delimeter>|-s <delay>]'

#
# Gracefully handle a CTRL+c
#
def handle_exit(signal, frame):
  sys.exit(0)

				
if __name__ == "__main__":
  #parser = argparse.ArgumentParser()
  #parser.add_argument('--apache', action='store_true', help='Should log Apache data')
  #parser.add_argument('--mysql', action='store_true', help='Should log MySQL data')
  #args = parser.parse_args()

  signal.signal(signal.SIGINT, handle_exit)

  # Use getopts until we can install python 2.7.x
  try:
    opts, args = getopt.getopt(sys.argv[1:], "amc:d:s:", ["apache", "mysql", "config", "delimeter", "seconds"])
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

  for o, a in opts:
    if o in ("-a", "--apache"):
      options['apache'] = True
    elif o in ("-m", "--mysql"):
      options['mysql'] = True
    elif o in ("-c", "--config"):
      options['config'] = a
    elif o in ("-d", "--delimeter"):
      options['delimeter'] = a
    elif o in ("-s", "--seconds"):
      delay = float(a)
      if delay >= 1.0:
        options['delay'] = delay
      else:
        print 'Delay must be 1 second or greater'
        sys.exit(2)

  # Setup the parser and defaults
  config = ConfigParser.RawConfigParser()
  config.add_section('log')
  config.set('log', 'format', '1 11 12 13')
  config.read(options['config'])  

  main(args)
