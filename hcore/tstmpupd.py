from __future__ import with_statement 
import os
from pthelma.timeseries import Timeseries, datetime_from_iso
from xreverse import xreverse

def update_ts_temp_file(cache_dir, connection, id):
    afilename = cache_dir+'%d.hts'%int(id)
    if os.path.exists(afilename):
        if os.path.getsize(afilename)<3:
            os.remove(afilename)
#Update the file in the case of logged data, if this is possible
    if os.path.exists(afilename):
        with open(afilename, 'r') as fileobject:
            xr = xreverse(fileobject, 2048)
            line = xr.next()
        lastdate = datetime_from_iso(line.split(',')[0])
        ts = Timeseries(int(id))
        ts.read_from_db(connection, onlybottom=True)
        if len(ts)>0:
            db_start, db_end = ts.bounding_dates()
            if db_start>lastdate:
                os.remove(afilename)
            elif db_end>lastdate:
                lastindex = ts.index(lastdate)
                with open(afilename, 'a') as fileobject:
                    ts.write(fileobject, start=ts.keys()[lastindex+1])
#Check for tmmp file or else create it
    if not os.path.exists(afilename):
        ts = Timeseries(int(id))
        ts.read_from_db(connection)
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        with open(afilename, 'w') as afile:
            ts.write(afile)
