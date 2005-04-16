# Blender.Registry module

"""
The Blender.Registry submodule.

B{New}: L{GetKey} and L{SetKey} can respectively load and save data to disk now.

Registry
========

This module provides a way to create, retrieve and edit B{persistent data} in
Blender. When a script runs in Blender, it has its own private global
dictionary, which is deleted when the script finishes. This is done to avoid
problems with name clashes and garbage collecting.  But the result is that
data created by a script isn't kept after it leaves, for itself or others to
access later: the data isn't persistent. The Registry module was created to
give script authors a way around this limitation.

In Python terms, the Registry holds a dictionary of dictionaries.
You should use it to save Python objects only, not BPython (Blender Python)
objects -- but you can save BPython object names, since those are strings.
Also, if you need to save a considerable amount of data, we recommend saving
it to a file instead. There's no need to keep huge blocks of memory around when
they can simply be read from a file.

Examples of what this module can be used for:

a) Saving data from a script that another script will need to access later.

b) Saving configuration data for a script.  Users can view and edit this data
using the "Scripts Configuration Editor" script, then.

c) Saving configuration data from your script's gui (button values) so that the
next time the user runs your script, the changes will still be there.  

Example::

  import Blender
  from Blender import Registry

  # first declare your global variables:
  myvar1 = 0
  myvar2 = 3.2
  mystr = "hello"

  # then check if they are already at the Registry (saved on a
  # previous execution of this script) or on disk:
  rdict = Registry.GetKey('MyScript', True)
  if rdict: # if found, get the values saved there
    myvar1 = rdict['myvar1']
    myvar2 = rdict['myvar2']
    mystr = rdict['mystr']

  # let's create a function to update the Registry when we need to:
  def update_Registry():
    d = {}
    d['myvar1'] = myvar1
    d['myvar2'] = myvar2
    d['mystr'] = mystr
    # cache = True: data is also saved to a file
    Blender.Registry.SetKey('MyScript', d, True)

  # ...
  # here goes the main part of the script ...
  # ...

  # at the end, before exiting, we use our helper function:
  update_Registry()
  # note1: better not update the Registry when the user cancels the script
  # note2: most scripts shouldn't need to register more than one key.
"""

def Keys ():
  """
  Get all keys currently in the Registry's dictionary.
  """

def GetKey (key, cached = False):
  """
  Get key 'key' from the Registry.
  @type key: string
  @param key: a key from the Registry dictionary.
  @type cached: bool
  @param cached: if True and the requested key isn't already loaded in the
      Registry, it will also be searched on the user or default scripts config
      data dir (config subdir in L{Blender.Get}('datadir')).
  @return: the dictionary called 'key'.
  """

def SetKey (key, dict, cache = False):
  """
  Store a new entry in the Registry.
  @type key: string
  @param key: the name of the new entry, tipically your script's name.
  @type dict: dictionary
  @param dict: a dict with all data you want to save in the Registry.
  @type cache: bool
  @param cache: if True the given key data will also be saved as a file
      in the config subdir of the scripts user or default data dir (see
      L{Blender.Get}.
  """

def RemoveKey (key):
  """
  Remove the dictionary with key 'key' from the Registry.
  @type key: string
  @param key: the name of an existing Registry key.
  """
