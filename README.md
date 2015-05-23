# YaaaaaaS
Yet Another Attempt At An Ascii Adventure System

##Making A Game
Yas Games are contained inside a folder with a .yaml file describing each room plus a yasGame.yaml file to declare it as a yasGame

###yasGame.yaml
The format of the yasGame.yaml is
```
startingRoom: [file to start on]
```

###Room files
Room files are yaml files with a mapping at the root, the mapping contains Room Features aganist their refrence name.

A special refrence name of `_` is used to describe the room as a whole.

Room Features are anything the player can look at or move through to change rooms.

Room Features are mapping of option keys:

desc
: Description of the Feature, displayed when looked at  
descLocked
: Same as `desc` but displayed instead if locked  
link
: Displayed when the player goes through the feature  
linkLocked
: Displayed when a player tries to go through a locked feature  
goto
: Defines which room the feature leads to, if not defined, link and linkLocked are ignored and the user cannot "go" through this feature  
switch
: Mapping of variables to set when the object is looked at  
init
: simular to switch but only for `_`, set when room is entered but will not override existing varaibles  
locked
: defines if the feature is locked. The locked can also be controlled via the variable `![room-name].[feature].locked`

Example Room Feature showing desc and switch:
```
table:
    desc: >
        A large table in the middle of the empty room.
        There is a key on it, you take the key.
    switch:
        'north.locked': False
```
Example Room Feature showing links and locks:
```
north:
    desc: >
        The northen exit, you can go through now because you have the key.
    descLocked: >
        The Northen exit. It is locked
    link: >
        You head north out the room, but it's not much help...
    linkLocked: >
        You try heading north but the exit is locked.
    goto: test-north
    locked: true
```

###!if blocks
For greater control over the game !if blocks can be used in some places (most notable room features).

!if blocks can be declared by placing !if instead of the mapping. !if blocks themselves are maps with simple boolean logic as a key and the block to return as a value. !if blocks are evaulated in order. An empty key `''` is always evaluated.
