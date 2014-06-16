import os
import shutil
import tempfile

from simpletail import ropen

from pthelma.timeseries import Timeseries, datetime_from_iso

def update_ts_temp_file(cache_dir, connection, id):
    full_rewrite = False

    afilename = os.path.join(cache_dir, '%d.hts'%(id,))
    if os.path.exists(afilename):
        if os.path.getsize(afilename)<3:
            full_rewrite = True
    #Update the file in the case of logged data, if this is possible
    if os.path.exists(afilename) and not full_rewrite:
        with ropen(afilename) as fileobject:
            line = fileobject.readline()
        lastdate = datetime_from_iso(line.split(',')[0])
        ts = Timeseries(id)
        ts.read_from_db(connection, bottom_only=True)
        if len(ts)>0:
            db_start, db_end = ts.bounding_dates()
            if db_start>lastdate:
                full_rewrite = True
            elif db_end>lastdate:
                lastindex = ts.index(lastdate)
                with open(afilename, 'a') as fileobject:
                    ts.write(fileobject, start=ts.keys()[lastindex+1])
#Check for tmmp file or else create it
    if not os.path.exists(afilename) or full_rewrite:
        ts = Timeseries(id)
        ts.read_from_db(connection)
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        tempfile_handle, tempfile_name = tempfile.mkstemp(dir=cache_dir)
        with os.fdopen(tempfile_handle, 'w') as afile:
            ts.write(afile)
        shutil.move(tempfile_name, afilename)
