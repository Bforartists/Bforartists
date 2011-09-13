***************
Tips and Tricks
***************

Here are various suggestions that you might find useful when writing scripts.

Some of these are just python features that scripters may not have thought to use with blender, others are blender specific.


Use The Terminal
================

When writing python scripts, it's useful to have a terminal open, this is not the built-in python console but a terminal application which is used to start blender.

There are 3 main uses for the terminal, these are:

* You can see the output of ``print()`` as you're script runs, which is useful to view debug info.

* The error trace-back is printed in full to the terminal which won't always generate an error popup in blender's user interface (depending on how the script is executed).

* If the script runs for too long or you accidentally enter an infinite loop, Ctrl+C in the terminal (Ctrl+Break on Windows) will quit the script early.

.. note::
   For Linux and OSX users this means starting the terminal first, then running blender from within it. On Windows the terminal can be enabled from the help menu.


Use an External Editor
======================

Blenders text editor is fine for small changes and writing tests but its not full featured, for larger projects you'll probably want to use a standalone editor or python IDE.

Editing a text file externally and having the same text open in blender does work but isn't that optimal so here are 2 ways you can easily use an external file from blender.

Using the following examples you'll still need textblock in blender to execute, but reference an external file rather then including it directly.

Executing External Scripts
--------------------------

This is the equivalent to running the script directly, referencing a scripts path from a 2 line textblock.

.. code-block:: python

   filename = "/full/path/to/myscript.py"
   exec(compile(open(filename).read(), filename, 'exec'))


You might want to reference a script relative to the blend file.

.. code-block:: python

   import bpy
   import os

   filename = os.path.join(os.path.basename(bpy.data.filepath), "myscript.py")
   exec(compile(open(filename).read(), filename, 'exec'))


Executing Modules
-----------------

This example shows loading a script in as a module and executing a module function.

.. code-block:: python

   import myscript
   import imp

   imp.reload(myscript)
   myscript.main()


Notice that the script is reloaded every time, this forces use of the modified version, otherwise the cached one in ``sys.modules`` would be used until blender was restarted.

The important difference between this and executing the script directly is it has to call a function in the module, in this case ``main()`` but it can be any function, an advantage with this is you can pass arguments to the function from this small script which is often useful for testing different settings quickly.

The other issue with this is the script has to be in pythons module search path.
While this is not best practice - for testing you can extend the search path, this example adds the current blend files directory to the search path, then loads the script as a module.

.. code-block:: python

   import sys
   import os
   import bpy

   blend_dir = os.path.basename(bpy.data.filepath)
   if blend_dir not in sys.path:
      sys.path.append(blend_dir)

   import myscript
   import imp
   imp.reload(myscript)
   myscript.main()


Don't Use Blender!
==================

While developing your own scripts blenders interface can get in the way, manually reloading, running the scripts, opening file import etc. adds overhead.

For scripts that are not interactive it can end up being more efficient not to use blenders interface at all and instead execute the script on the command line.

.. code-block:: python

   blender --background --python myscript.py


You might want to run this with a blend file so the script has some data to operate on.

.. code-block:: python

   blender myscene.blend --background --python myscript.py


.. note::

   Depending on your setup you might have to enter the full path to the blender executable.


Once the script is running properly in background mode, you'll want to check the output of the script, this depends completely on the task at hand however here are some suggestions.

* render the output to an image, use an image viewer and keep writing over the same image each time.

* save a new blend file, or export the file using one of blenders exporters.

* if the results can be displayed as text - print them or write them to a file.


This can take a little time to setup, but it can be well worth the effort to reduce the time it takes to test changes - you can even have blender running the script ever few seconds with a viewer updating the results, so no need to leave you're text editor to see changes.


Use External Tools
==================

When there are no readily available python modules to perform specific tasks it's worth keeping in mind you may be able to have python execute an external command on you're data and read the result back in.

Using external programs adds an extra dependency and may limit who can use the script but to quickly setup you're own custom pipeline or writing one-off scripts this can be handy.

Examples include:

* Run The Gimp in batch mode to execute custom scripts for advanced image processing.

* Write out 3D models to use external mesh manipulation tools and read back in the results.

* Convert files into recognizable formats before reading.


Bundled Python & Extensions
===========================

The Blender releases distributed from blender.org include a complete python installation on all platforms, this has the disadvantage that any extensions you have installed in you're systems python wont be found by blender.

There are 2 ways around this:

* remove blender python sub-directory, blender will then fallback on the systems python and use that instead **python version must match the one that blender comes with**.

* copy the extensions into blender's python sub-directory so blender can access them, you could also copy the entire python installation into blenders sub-directory, replacing the one blender comes with. This works as long as the python versions match and the paths are created in the same relative locations. Doing this has the advantage that you can redistribute this bundle to others with blender and/or the game player, including any extensions you rely on.


Drop Into a Python Interpreter in You're Script
===============================================

In the middle of a script you may want to inspect some variables, run some function and generally dig about to see whats going on.

.. code-block:: python

   import code
   code.interact(local=locals())


If you want to access both global and local variables do this...

.. code-block:: python

   import code
   namespace = globals().copy()
   namespace.update(locals())
   code.interact(local=namespace)


The next example is an equivalent single line version of the script above which is easier to paste into you're code:

.. code-block:: python

   __import__('code').interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})


``code.interact`` can be added at any line in the script and will pause the script an launch an interactive interpreter in the terminal, when you're done you can quit the interpreter and the script will continue execution.


Admittedly this highlights the lack of any python debugging support built into blender, but its still handy to know.

.. note::

   This works in the game engine as well, it can be handy to inspect the state of a running game.


Advanced
========


Blender as a module
-------------------

From a python perspective it's nicer to have everything as an extension which lets the python script combine many components.

Advantages include:

* you can use external editors/IDE's with blenders python API and execute scripts within the IDE (step over code, inspect variables as the script runs).

* editors/IDE's can auto complete blender modules & variables.

* existing scripts can import blender API's without having to run inside blender.


This is marked advanced because to run blender as a python module requires a special build option.

For instructions on building see `Building blender as a python module <http://wiki.blender.org/index.php/User:Ideasman42/BlenderAsPyModule>`_


Python Safety (Build Option)
----------------------------

Since it's possible to access data which has been removed (see Gotcha's), this can be hard to track down the cause of crashes.

To raise python exceptions on accessing freed data (rather then crashing), enable the CMake build option WITH_PYTHON_SAFETY.

This enables data tracking which makes data access about 2x slower which is why the option is not enabled in release builds.
