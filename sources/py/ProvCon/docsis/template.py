#!/bin/env python

def RunTemplate ( template_file, output_stream, data ):
    execfile ( template_file, {}, { 'OF' : output_stream, 'DAT' : data } )
    
