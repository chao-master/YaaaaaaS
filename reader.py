#!/bin/python3
import yaml,pprint,functools

class ifBlock(yaml.YAMLObject):
	yaml_tag = "!if"

	def __init__(self,ifStates):
		self.ifStates = ifStates

	@classmethod
	def from_yaml(cls,loader,node):
		return ifBlock([(k.value,v.value) for k,v in node.value])
		
	def get(self,instance):
		for k,v in self.ifStates:
			if k == '' or instance.game.get(instance,k,False):
				return v
		return None

	def __repr__(self):
		return "<ifBlock>"

@functools.lru_cache()
def dataLoad(filename):
	with open(filename) as f:
		return yaml.load(f)

class Room():
	def __init__(self,fileName,game):
		self.fileName = fileName
		self.game = game
		self.data = dataLoad(fileName,)

		for k,v in self.data.items():
			if k == "_": continue
			try:
				game.set(self,k+".locked",v["locked"],False)
			except KeyError:
				pass
			try:
				game.set(self,k+".hidden",v["hidden"],False)
			except KeyError:
				pass

		for k,v in self.data["_"].get("init",{}):
			self.game.set(self,k,v,False)



	def ifEval(self,item):
		try:
			return item.doEval(self)
		except AttributeError:
			return item

class Game():
	def __init__(self,startRoom):
		self.variables = {}
		self.room = Room(startRoom,self)

	def get(self,instance,key,default=None):
		if key[0] == "!":
			key = key[1:]
		else:
			key = instance.fileName + "." + key
		try:
			return self.variables[key]
		except KeyError:
			return default;

	def set(self,instance,key,value,overwrite=True):
		if key[0] == "!":
			key = key[1:]
		else:
			key = instance.fileName + "." + key
		if overwrite or key not in self.variables:
			self.variables[key] = value

	def unset(self,key):
		try:
			del self.variables[i]
		except KeyError:
			pass

	def handleCommand(self,command):
		command = command.split(" ")
		if command[0] == "go":
			link,newRoom = self.room.go(*command[1:])
			if newRoom is not None:
				self.room = Room(newRoom,self)
		elif command[0] == "look":
			desc = self.room.look(*command[1:])




game = Game("test-room")

pprint.pprint(game.room.data)
print(game.room.go("north"))