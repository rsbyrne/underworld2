##~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~##
##                                                                                   ##
##  This file forms part of the Underworld geophysics modelling application.         ##
##                                                                                   ##
##  For full license and copyright information, please refer to the LICENSE.md file  ##
##  located at the project root, or contact the authors.                             ##
##                                                                                   ##
##~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~#~##
"""
this is a docstring
"""

# ok, first need to change default python dlopen flags to global
# this is because when python imports the module, the shared libraries are loaded as RTLD_LOCAL
# and then when MPI_Init is called, OpenMPI tries to dlopen its plugin, they are unable to
# link to the openmpi libraries as they are private
import sys as _sys
import ctypes as _ctypes
_oldflags = _sys.getdlopenflags()
_sys.setdlopenflags( _oldflags | _ctypes.RTLD_GLOBAL )

import libUnderworld
import container
import mesh
import fevariable
import conditions
import function
import swarm
import systems
import utils

#import threading
#def go():
#    import urllib2
#    try:
#        print("Hottub time!!")
#        response = urllib2.urlopen('http://github.moresi.info')
#        html = response.read()
#        print("Hottub time!!")
#    except:
#        pass
#    return
#    #print("Nein!!")
#thread = threading.Thread( target=go )
#thread.start()
# ok, now set this back to the original value
_sys.setdlopenflags( _oldflags )

# lets go right ahead and init now.  user can re-init if necessary.
import _stgermain
_data =  libUnderworld.StGermain_Tools.StgInit( [] )

_stgermain.LoadModules( {"import":["StgDomain","StgFEM","PICellerator","Underworld","gLucifer","Solvers"]} )

def rank():
    """
    Returns the rank of the current processors.

    Parameters
    ----------
        None

    Returns:
    ----------
        rank (unsigned) : Rank of current processor.
    """
    return _data.rank


def nProcs():
    """
    Returns the number of processors being utilised by the simulation.

    Parameters
    ----------
        None

    Returns:
    ----------
        nProcs (unsigned) : Number of processors.
    """
    return _data.nProcs


def help(object):
    """
    This help function simply prints the object's docstring, without also
    printing the entire object hierarchy's docstrings (as per the python
    build in help() function).

    Parameters
    ----------
        object:  Any python object.

    Returns:
    ----------
        None
    """
    print("Object docstring:\n")
    print(object.__doc__)
    print("Object initialiser docstring:\n")
    print(object.__init__.__doc__)

# lets handle exceptions differently in parallel to ensure we call 
if nProcs() > 1:
    origexcepthook = _sys.excepthook
    def uw_uncaught_exception_handler(exctype, value, tb):
        print('\n###########################################################################################')
        print('###########################################################################################')
        print('An uncaught exception was encountered on processor {}.'.format(rank()))
        # pass through to original handler
        origexcepthook(exctype, value, tb)
        print('###########################################################################################')
        print('###########################################################################################')
        libUnderworld.StGermain_Tools.StgAbort( _data )
    _sys.excepthook = uw_uncaught_exception_handler

def _prepend_message_to_exception(e, message):
    """
    This function simply adds a message to an encountered exception. 
    Currently it is not python 3 friendly.  Check here
    http://stackoverflow.com/questions/6062576/adding-information-to-a-python-exception
    """
    raise type(e), type(e)(message + '\n' + e.message), _sys.exc_info()[2]


class _del_uw_class:
    """
    This simple class simply facilitates calling StgFinalise on uw exit
    Previous implementations used the 'atexit' module, but this called finalise
    *before* python garbage collection which as problematic as objects were being
    deleted after StgFinalise was called.
    """
    def __init__(self,delfunc, deldata):
        self.delfunc = delfunc
        self.deldata = deldata
    def __del__(self):
        self.delfunc(self.deldata)

_delclassinstance = _del_uw_class(libUnderworld.StGermain_Tools.StgFinalise, _data)



