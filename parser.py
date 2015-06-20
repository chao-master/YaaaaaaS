#!/bin/python3
import yaml
import warnings
import re
import functools
from collections import OrderedDict,defaultdict

##Generic Base Class that builds and handles the other's common methods
class GenericBlock(object):
    def __init__(self,parent,key):
        self.parent = parent
        self.game = parent.game
        self.key = key

    def addChildren(self,children):
        self.children = children

    def doEval(self):
        rtn = self._doEval()
        try:
            return rtn.doEval()
        except AttributeError:
            return rtn

    def __repr__(self):
        return "<{}~{}>".format(type(self).__name__,self.key)

##Used to allow implementaion of if blocks in yaml
class IfBlock(GenericBlock):
    def _doEval(self):
        for k,v in self.children:
            if not k:
                return v
            try:
                k,m = k.split("=",1)
            except ValueError:
                m=True
            gt = self.game.getVar(k,False)
            if type(gt) == bool:
                m = m.lower() == "true"
            else:
                m = type(gt)(m)
            if gt == m:
                return v
        return None

##Interactable Objects/Connectors
class InteractionBlock(GenericBlock):
    def addChildren(self,children):
        self.children = defaultdict()
        self.children.update(children)

##Room object
class RoomDescriptionBlock(InteractionBlock):
    pass

class RoomBlock(GenericBlock):
    def __init__(self,parent,key):
        self.parent = parent
        self.game = parent
        self.key = key

    def addChildren(self,children):
        self.me = children["_"]
        del children["_"]
        self.children = children

class SwitchBlock(GenericBlock):
    def addChildren(self,children):
        self.children = children

def objParse(mapping,parent=None,path=[None]):
    if not isinstance(mapping, dict):
        return mapping

    if path == [None]:
        cls = RoomBlock
    elif path[-1] == "switch":
        cls = SwitchBlock
    elif any(['=' in k or '<' in k or '>' in k for k in mapping]):
        cls = IfBlock
        rtn = cls(parent,path[-1])
        rtn.addChildren({k:objParse(v,rtn,path) for k,v in mapping.items()})
        return rtn
    else:
        cls = InteractionBlock
    rtn = cls(parent,path[-1])
    rtn.addChildren({k:objParse(v,rtn,path+[k]) for k,v in mapping.items()})
    return rtn

##Loads and caches yaml
@functools.lru_cache(maxsize=128, typed=False)
def loadRoom(fileName):
    with open(fileName+".yaml") as f:
        return objParse(yaml.load(f))

if __name__ == "__main__":
    import os
    for file in os.listdir('pony'):
        if file[-5:] == ".yaml":
            if file == "yasGame.yaml":
                continue

            print
            print (file)
            print ("-"*len(file))
            room = loadRoom("pony/"+file[:-5])
            def _(k,v,l=0):
                __v = v
                if isinstance(__v,str) and len(__v)>40:
                    __v=__v[:37]+"..."
                print ("{}{}: {}".format(("\t"*l),k,__v))
                if isinstance(v,RoomBlock):
                    for _k,_v in v.me.children.items():
                        _(_k,_v,l+1)
                try:
                    for _k,_v in v.children.items():
                        _(_k,_v,l+1)
                except AttributeError:
                    pass
            _("Room",room,0)
