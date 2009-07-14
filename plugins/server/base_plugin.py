import sys
import os

class BasePluginClass(object):
    def __init__(self):
        self.__name = ""
        self.__author = ""
        self.__help = ""
        self.__file = __file__
        self.__activated = False
        self.__inputpriority = -1 # -1 = not used; 99 = priority doesn't matter
                                  # Any other number is priority, lowest number
                                  # executes first
        self.__outputpriority = -1# -1 = not used; 99 = priority doesn't matter
                                  # Any other number is priority, lowest number
                                  # executes first
        self.__pollpriority = -1  # -1 = not used; 99 = priority doesn't matter
                                  # Any other number is priority, lowest number
                                  # executes first


    def preParseIncoming(self, xml_dom, data):
        return xml_dom, data

    def postParseIncoming(self, data):
        return data

    def getPlayer(self):
        return None

    def setPlayer(self, playerData):
        return

    def preParseOutgoing(self):
        return []


    def _getName(self):
        return self.__name

    def _setName(self, val):
        if isinstance(val, basestring):
            self.__name = val
        else:
            self.__name = str(val)


    def _getAuthor(self):
        return self.__author

    def _setAuthor(self, val):
        if isinstance(val, basestring):
            self.__author = val
        else:
            self.__author = str(val)


    def _getHelp(self):
        return self.__help

    def _setHelp(self, val):
        if isinstance(val, basestring):
            self.__help = val
        else:
            self.__help = str(val)


    def _getFile(self):
        return self.__file

    def _setFile(self, val):
        if isinstance(val, basestring):
            self.__file = val
        else:
            self.__file = str(val)


    def _getActivated(self):
        return self.__activated

    def _setActivated(self, val):
        if isinstance(val, bool):
            self.__activated = val
        elif isinstance(val, int):
            if val <= 0:
                self.__activated = False
            else:
                self.__activated = True
        else:
            self.__activated = False


    def _getInputPriority(self):
        return self.__activated

    def _setInputPriority(self, val):
        if isinstance(val, int) and val in xrange(-1, 100):
            self.__inputpriority = val
        else:
            self.__inputpriority = -1


    def _getOutputPriority(self):
        return self.__activated

    def _setOutputPriority(self, val):
        if isinstance(val, int) and val in xrange(-1, 100):
            self.__outputpriority = val
        else:
            self.__outputpriority = -1


    def _getPollPriority(self):
        return self.__pollpriority

    def _setPollPriority(self, val):
        if isinstance(val, int) and val in xrange(-1, 100):
            self.__pollpriority = val
        else:
            self.__pollpriority = -1

    Name = property(_getName, _setName)
    Author = property(_getAuthor, _setAuthor)
    Help = property(_getHelp, _setHelp)
    File = property(_getFile, _setFile)
    Activated = property(_getActivated, _setActivated)
    InputPriority = property(_getInputPriority, _setInputPriority)
    OutputPriority = property(_getOutputPriority, _setOutputPriority)
    PollPriority = property(_getPollPriority, _setPollPriority)

