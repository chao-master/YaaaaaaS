#!/bin/python3
import functools
import textwrap
import yaml
import pprint
import os.path
import warnings

import parser

##Used for getting the size of the terminal
def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])

##Used to allow implementaion of if blocks in yaml
class ifBlock(yaml.YAMLObject):
    yaml_tag = "!if"

    def __init__(self,ifStates):
        self.ifStates = ifStates

    @classmethod
    def from_yaml(cls,loader,node):
        return ifBlock([(k.value,loader.construct_object(v,deep=True)) for k,v in node.value])

    def doEval(self,game):
        for k,v in self.ifStates:
            if not k:
                return v
            try:
                k,m = k.split("=",1)
            except ValueError:
                m=True
            gt = game.getVar(k,False)
            if type(gt) == bool:
                m = m.lower() == "true"
            else:
                m = type(gt)(m)
            if gt == m:
                return v
        return None

class NotSection(Exception):
    pass

class NotLinkSection(Exception):
    pass

class NoValue(Exception):
    pass

class ParsingWarning(UserWarning):
    pass

##Game logic
class Game():
    def __init__(self,folder):
        self.variables = {}
        self.folder = folder
        self.roomName = None
        self.roomData = None

        with open(os.path.join(self.folder,"yasGame.yaml")) as f:
            config = yaml.load(f)
            self.changeRoomTo = config["startingRoom"]


    def changeRoom(self):
        if self.changeRoomTo == self.roomName:
            self.changeRoomTo = None
            return False
        self.roomName = self.changeRoomTo
        self.changeRoomTo = None
        self.roomData = loadRoom(os.path.join(self.folder,self.roomName))

        try:
            for k,v in self.getData("_","init").items():
                self.setVar(k,v,False)
        except NoValue:
            pass
        except AttributeError as e:
            warnings.warn(ParsingWarning("Warning file {}'s _.init isn't a mapping".format(self.roomName)))

        for k,v in self.getData().items():
            if k == "_": continue
            try:
                self.setVar(k+".locked",v["locked"],False)
            except KeyError:
                pass
            try:
                self.setVar(k+".hidden",v["hidden"],False)
            except KeyError:
                pass
        return True

    def _normKey(self,key):
        return key[1:] if key[0] == "~" else self.roomName + "." + key

    def getVar(self,key,default=None):
        key = self._normKey(key)
        try:
            return self.variables[key]
        except KeyError:
            return default;

    def setVar(self,key,value,overwrite=True):
        key = self._normKey(key)
        if overwrite or key not in self.variables:
            self.variables[key] = value

    def unif(self,item):
        try:
            return item.doEval(self)
        except AttributeError:
            return item

    def getData(self,section=None,value=None):
        if section == None:
            return {k:self.unif(v) for k,v in self.roomData.items() if self.unif(v)}
        else:
            return self.unif(self._getData(section,value))

    def _getData(self,section,value=None):
        try:
            dSection = self.unif(self.roomData[section])
        except KeyError:
            raise NotSection(section)
        if dSection is None: #Fix to raise If based error
            raise NotSection(section)

        if value is None:
            return dSection

        if value == "desc":
            try:
                if self.getVar(section+".locked",False):
                    return dSection["descLocked"]
            except KeyError: pass
            return dSection.get("desc","The {} isn't that intresting".format(section))

        if value == "link":
            if "goto" not in dSection:
                raise NotLinkSection(section)
            if self.getVar(section+".locked",False):
                return dSection.get("linkLocked","You try to head {}, but cannot".format(section))
            else:
                return dSection.get("link","You head {}".format(section))

        if section == "_" and (value == "prompt" or value == "name"):
            return dSection.get(value,"???")

        try:
            return dSection[value]
        except KeyError:
            raise NoValue((section,value))

    def go(self,to):
        try:
            rtn = self.getData(to,"link")
            if not self.getVar(to+".locked",False):
                self.changeRoomTo = self.getData(to,"goto")
            return rtn
        except NotSection:
            return "There is no {} to go to".format(to)
        except NotLinkSection:
            return "You can't go to {}".format(to)

    def look(self,to="_"):
        try:
            rtn = self.getData(to,"desc")
        except NotSection:
            return "There is no {} to look at".format(to)
        try:
            for k,v in self.getData(to,"switch").items():
                self.setVar(k,v)
        except NoValue: pass
        return rtn

    def gameLoop(self):
        while 1:
            width = getTerminalSize()[0]

            inpu = None
            if self.changeRoomTo is not None:
                if self.changeRoom():
                    inpu = ["look"]
                else:
                    print (textwrap.fill("You find you haven't really moved anywhere", width=width-5, initial_indent=" "*5, subsequent_indent=" "*5))
            if inpu is None:
                inpu = input(self.getData("_","prompt")+": ").split(" ")

            if len(inpu) == 1:

                if inpu[0] == "look":
                    print ("=== {title:-^{width}} ===".format(title=" "+self.getData("_","name")+" ", width=width-10))
                    print (textwrap.fill(self.look("_"), width=width-5, initial_indent=" "*5, subsequent_indent=" "*5))
                    continue

                if inpu[0] in self.getData().keys():
                    inpu = ["go",inpu[0]]

                if inpu[0] == "DEBUG": #debug command
                    pprint.pprint(game.variables)
                    pprint.pprint(game.getData())
                    continue

            if len(inpu) == 2:

                if inpu[0] == "look":
                    print (textwrap.fill(self.look(inpu[1]), width=width-5, initial_indent=" "*5, subsequent_indent=" "*5))
                    continue

                if inpu[0] == "go":
                    print (textwrap.fill(self.go(inpu[1]), width=width-5, initial_indent=" "*5, subsequent_indent=" "*5))
                    continue

            print (" * Bad command try: go or look * ")

game = Game("pony")
game.gameLoop()
