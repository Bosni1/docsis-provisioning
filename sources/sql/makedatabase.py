#!/bin/env python
import os
import re

root_source_dir = "database"
output_file = "database.sql"

SETTINGS = {
    "SCHEMA" : "pv.",
    "SCHEMA_NAME" : "pv",
}


def concatenate_dir_files ( path ):
    files = os.listdir ( path )
    files.sort()
    for fname in files:
        try:
            num = int ( fname[:3] )
        except ValueError:
            continue
        fullname = path + "/" + fname
        print fullname
        if os.path.isdir ( fullname ):
            concatenate_dir_files ( fullname )
        else:
            f = open ( fullname, 'r' )
            output.write ( ("-" * 100) + "\n--\n-- " + fullname + "\n" + ("-" * 100) + "\n" )
            output.write ( f.read() )
            f.close()

output = open ( output_file, 'w' )        
concatenate_dir_files  ( root_source_dir )
output.close()

output = open ( output_file, 'r' )        
source = output.read()
output.close()

for var in SETTINGS:
    source = source.replace ( "{:" + var + ":}", SETTINGS[var] )

output = open ( output_file, 'w' )        
output.write (source)
output.close()

