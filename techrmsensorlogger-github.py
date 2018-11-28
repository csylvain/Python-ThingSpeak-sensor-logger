#!/usr/bin/python3
#-----------------------------------------------------------------------------
# Tech Room Sensor Logger
#   (techrmsensorlogger)
#
# take data reported over wifi from RGBClock (Elektor.com kit w/BME280 BoB)
#   and report measurements to Thingspeak channel
#
# code structure inspired by templogger.py by Matt Hawkins 2015-06-20
#   https://www.raspberrypi-spy.co.uk/2015/06/basic-temperature-logging-to-the-internet-with-raspberry-pi/
#
# code developed with many references to https://docs.python.org/3.6/library/index.html
#   and https://www.w3schools.com/python/ using Visual Studio Code on Linux
#
# CSylvain KB3CS  2018-11-14 initial version
# CSylvain KB3CS  2018-11-25 use urllib3 exclusively
#-----------------------------------------------------------------------------

import time
import sys
import traceback
import certifi
import urllib3

################# Configuration Defaults #################
THINGSPEAKKEY = 'ABCDEFGHIJKLMNOPQRSTUV'
THINGSPEAKURL = 'https://api.thingspeak.com/update'
RGBCLOCKADDR  = '192.168.1.105:81'
DEBUG         = 0
##########################################################

def sendData (hpm,url,chkey,fn1,fn2,fn3,t,p,h):
    # send sensor data
    values = { 'api_key' : chkey,
               'field1' : t,
               'field2' : p,
               'field3' : h }
    
    ts = time.strftime("%FT%H:%M:%S%z")
    try:
        r = hpm.request('GET', url, fields=values)
        rdd = r.data.decode('utf-8')
        if DEBUG:
            print (rdd)
        r.close()

    except Exception as e:
        print (ts, "* Exception ", repr(e))
        return 1
    
    print (ts, '/', fn1, t, '/', fn2, p, '/', fn3,  h, '/ Response', rdd)
    return 0


def main ():
    global THINGSPEAKKEY
    global THINGSPEAKURL

    http = urllib3.PoolManager(retries=False, timeout=5.0) # http
    https = urllib3.PoolManager(retries=False, timeout=5.0,
                                cert_reqs='CERT_REQUIRED', ca_certs=certifi.where()) # https    

    try:
        if DEBUG:
            print ("program gets data from RGBClock and sends data to thingspeak")
        
        while True:
            s = "".join(('http://', RGBCLOCKADDR, '/curval')) # preferable to A+B+C
            if DEBUG > 1:
                print(s)

            ts = time.strftime("%FT%H:%M:%S%z")
            try:           
                r = http.request('GET', s)
                rdd = r.data.decode('utf-8')
                r.close()
                if DEBUG > 2:
                    print(ts, rdd)
            
            except Exception as e:
                print (ts, "* Exception ", repr(e))
                sys.stdout.flush()
                time.sleep(2*60)  # wait 2 mins
                continue

            d = rdd.split(',')

            sobj = slice(0, len(d[1])-2)
            d[1] = d[1][sobj]  # numeric part of '23.36*C'
            sobj = slice(0, len(d[2])-4)
            d[2] = d[2][sobj]  # numeric part of '963.27 hPa'
            sobj = slice(0, len(d[3])-1)
            d[3] = d[3][sobj]  # numeric part of '31.28%'

            if DEBUG > 1:
                print('temperature = ', d[1])
                print('pressure    = ', d[2])
                print('humidity    = ', d[3])

            rv = sendData(https,THINGSPEAKURL,THINGSPEAKKEY,
                            'temperature','pressure','humidity',d[1],d[2],d[3])

            sys.stdout.flush()
            if rv == 0:
                time.sleep(5*60) # 5 mins
            else:
                time.sleep(2*60)
       
    except Exception as e:
        print ("something went very wrong")
        print ("* Exception ", repr(e))
        traceback.print_exc(file=sys.stdout)
        return 1
    
    return 0 # notreached

if __name__ == "__main__":
    main()
