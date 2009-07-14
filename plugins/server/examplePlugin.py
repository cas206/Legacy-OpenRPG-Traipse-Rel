import os
import sys
from base_plugin import BasePluginClass

class Plugin(BasePluginClass):
    def __init__(self):
        BasePluginClass.__init__(self)

        self.Name = "examplePlugin"
        self.File = __file__
        self.Author = "Dj Gilcrease"
        self.Help = "Help"
        self.InputPriority = -1 # -1 = not used; 99 = priority doesn't matter
                                # Any other number is priority, lowest number
                                # executes first
        self.OutputPriority = -1# -1 = not used; 99 = priority doesn't matter
                                # Any other number is priority, lowest number
                                # executes first
        self.PollPriority = -1  # -1 = not used; 99 = priority doesn't matter
                                # Any other number is priority, lowest number
                                # executes first

    def start(self):
        #Do you DB connection here
        pass

    def stop(self):
        #Close your DB connection here
        pass

    def preParseIncoming(self, xml_dom, data):
        #Do something with the Data or Dom, and return it

        return xml_dom, data

    def postParseIncoming(self, data):
        #Do something with the Data before it gets sent to the room

        return data

    def preParseOutgoing(self):
        #Fetch messages from somewhere that need to be sent out

        return []
