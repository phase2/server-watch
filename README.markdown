Server Watch
============

This is script setup to allow for easy logging of various server level statistics that
is useful when doing system profiling and load testing.

Usage
-----

This is a simple Python script that can be run via 

    ./server-watch.py
    
This logs the desired values to stdout. Those can be redirected to a file as:

    ./server-watch.py > /tmp/server-data.log
    
There are a few command line options to customize the behavior

* -c, --config < config file >

    > Specifies which config file to use

* -a, --apache

    > Enable apache connection monitoring

* -m, --mysql

    > Enable mysql monitoring

* -d, --delimeter < delimete r>

    > What string to use as a delimeter for the log file, defaults to a tab

* -s, --seconds < delay >

    > How many seconds to delay b/w report rows, defaults to 1 second


Configuration File
------------------

There are a few sections in the configuration file

### Log

This controls the output columns in the log file a sample configuration looks like

    [log]
    format = 1 11 12 13

* format

    > Format is a space delineated listing of the columns to appear in the output rows.

The following fields are available for logging
* 1: 1 minute Load
* 2: 5 minute Load
* 3: 15 minute Load
* 4: %user - CPU % at user
* 5: %nice - CPU % at user w/ nice
* 6: %sys - CPU % at kernel
* 7: %iowait - CPU % at kernel in iowait 
* 8: %irq - CPU % serving interrupts
* 9: %soft - CPU % serving soft interrupts
* 10: %steal - CPU % at involuntary wait (hypervisor)
* 11: %idle = CPU % idle
* 12: Physical memory used
* 13: Physical memory free
* 14: Swap memory used
* 15: Swap memory free
* 16: Memory in page cache 
* 17: Number of apache processes
* 18: Mysql max used connections
* 19: Mysql total created tmp disk tables 
* 20: Mysql open files
* 21: Mysql total slow queries
* 22: Mysql table locks waited
* 23: Mysql threads connected
* 24: Mysql seconds behind master

### MySQL

This controls the connection info to MySQL

    [mysql]
    host = localhost
    user = root
    password = root

* host

    > The host name to connect

* user

    > The username for connecting

* password

    > The password connecting




