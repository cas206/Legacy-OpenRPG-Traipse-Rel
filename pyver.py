import sys  # Needed for version
import string # Needed for split
from orpg.orpg_version import * # To get NEEDS_PYTHON_MAJOR, MINOR, and MICRO

def getNumber(numberstringtoconvert):
    currentnumberstring = ""
    for number in numberstringtoconvert:
        if number >= "0" and number <="9":
            currentnumberstring += number
        else:
            break
    if currentnumberstring == "":
        return 0
    else:
        return int(currentnumberstring)
# This checks to make sure a certain version of python or later is in use
# The actual version requested is set in orpg/openrpg_version
def checkPyVersion():

    #  taking the first split on whitespace of sys.version gives us the version info without the build stuff
    vernumstring = string.split(sys.version)[0]

    #  This splits the version string into (major,minor,micro).  Actually, a complicating factor
    #  is that there sometimes isn't a micro, e.g. 2.0.  We'll just do it the hard way to build
    #  the numbers instead of tuple unpacking.
    splits = string.split(vernumstring,'.')

    #  Assign default values
    micro = 0
    minor = 0
    major = 0
    # Assign the integer conversion of each, assuming that it was found.  If not found, we assumed 0 just above.
    if len(splits) > 0:
        major = getNumber(splits[0])
    if len(splits) > 1:
        minor = getNumber(splits[1])
    if len(splits) > 2:
        micro = getNumber(splits[2])
    # Check against min version info from orpg/orpg_version
    if major >= NEEDS_PYTHON_MAJOR:
        if major > NEEDS_PYTHON_MAJOR:  # If it's greater, there's no need to check the minor
            return
        if minor >= NEEDS_PYTHON_MINOR:
            if minor > NEEDS_PYTHON_MINOR:  # If it's greater, there's no need to check the micro
                return
            if micro >= NEEDS_PYTHON_MICRO:
                return

    # If we get here, then the version check failed so we inform the user of the required version and exit
    print "Invalid python version being used.  Detected version %s,"  % (vernumstring)
    print "but version %i.%i.%i or better is required!" % (NEEDS_PYTHON_MAJOR,NEEDS_PYTHON_MINOR,NEEDS_PYTHON_MICRO)
    print "You either have the wrong version of Python installed or you"
    print "have multiple versions installed.  If you have multiple versions,"
    print "please make sure Python %i.%i.%i or better is found first in your path or explicitly" % (NEEDS_PYTHON_MAJOR,NEEDS_PYTHON_MINOR,NEEDS_PYTHON_MICRO)
    print "start using, \"<path>\python <program>\"."
    sys.exit( 1 )
