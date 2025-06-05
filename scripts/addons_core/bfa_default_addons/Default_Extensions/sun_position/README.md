# Sun Position

Sun Position allows positioning and animating the Sun (to a certain
degree of accuracy), to simulate real-world natural lighting. It uses
physical characteristics to position the Sun in the scene: geographic
location, time and date. It is based on the Earth System Research
Laboratory’s [online calculator](https://gml.noaa.gov/grad/solcalc/).


## Activation

Activate the extension by going to the Extensions section of the user
preferences, searching for “Sun” and clicking the check box to the
left of the result.


## Interface

Located in the `Properties → World → Sun Position panel`.


## Usage

This add-on has two distinct modes of operation: the [Normal
Mode](#normal-mode) allows you to animate the Sun realistically, while
the [Environment Mode](#environment-mode) is useful for synchronizing
a sun light to an environment texture.

The usage mode can be selected from the top of the Sun Position panel.


### Normal Mode

This is the mode by default. After selecting the time and place, you
can set up a sun light, a sky texture, and a collection to serve as
visualization.

#### Use Object

Select the Sun object which will be placed according to the chosen
time and place. Its position will be updated every time you change the
location or time, and you can thus create animations by setting
keyframes on them.

#### Use Collection

Select a collection of objects to be placed around the scene for
visualization. Two options are available: [analemma](#analemma) and
[diurnal](#diurnal).

Note: it is recommended to create a collection in the scene, and to
move the objects into this collection. If you wish to create several
visualizations, create as many collections as needed, select them in
turn and choose the right settings. Once deselected, a collection will
stay in place.

##### Analemma

The [analemma](https://en.wikipedia.org/wiki/Analemma) is a
visualization of the position of the Sun in the sky around the year
for a given time of the day. In other words, it is like a time lapse
picture of the sky over a year, with the Sun appearing multiple times
at the same time of the day.

![](docs/bell-lab.jpg)  
The analemma was used here to match [this
picture](https://commons.wikimedia.org/wiki/File:Analemma_fishburn.tif).

##### Diurnal

This option allows you to visualize the trajectory of the Sun in the
sky during a single day.

#### Sky Texture

Select a Sky Texture node in the World shading node tree. It will be
set up to match the Sun animation. This is useful if you want to have
a simple sky texture matching a sun light’s position.

#### Location

In order for the Sun to be placed correctly, you need to choose a
place on Earth where the scene is located. This place is represented
by two coordinates, *Longitude* (East / West) and *Latitude* (North /
South). They are expressed in degrees, from -180° to +180° for the
longitude, and from -90° to 90° for the latitude. The coordinates
match those found on such databases as OpenStreetMap or Google Maps.
You may enter and animate them manually, or paste them in.

##### Entering Coordinates

In the *Location* panel, enter *Latitude* and *Longitude* coordinates
corresponding to the location you wish to simulate. A simpler way is
to go to an online map such as OpenStreetMap, copy the coordinates
from there, and paste them into the *Enter Coordinates* field. They
will be parsed automatically.

Another source is Wikipedia. Suppose you want to render the [Barcelona
Pavilion](https://en.wikipedia.org/wiki/Barcelona_Pavilion) by Mies
van der Rohe. You can copy the coordinates from the article and paste
them into Blender.

| ![](docs/barcelona-wiki.png) | ![](docs/barcelona-coor.png) |
|:-:|:-:|
| Copy the coordinates from Wikipedia. | And paste them into Blender to have them parsed. |

##### North Offset

By default, the North points to the Y axis in the scene (to the top of
the screen in top view). But sometimes, you may have modeled it in
another orientation. In that case, you may enter a *North Offset*, to
change the orientation of the scene. *Show North* toggles a dashed
line pointing to the North in the 3D Viewport, to help you visualize
the cardinal directions.

#### Setting the Time

After selecting the location on Earth, select or animate the date and
time. This is fairly straightforward, but care must be taken to match
the *Time* zone and *Daylight Saving* to the moment you wish to
simulate. Time entered is the local time, but the global, UTC time may
be displayed below as well.

Note: time is stored in decimal format instead of
`hour:minute:second`. To match a time in that format, look at the
label *Local*.


### Environment Mode

Instead of simulating the position of the Sun for a real location and
time, this mode simply locks an environment texture with a sun light
object. It is useful if you want to increase the contrast in a
texture, by using an additional Sun.

#### Synchronizing the Sun Object to the Environment Texture

Start by selecting the Sun object and Environment Texture node. You
can then synchronize them by enabling *Sync Sun to Texture*. Hovering
any 3D Viewport will display the environment texture. Use the `MMB` to
pan, scroll wheel to zoom, and `Ctrl-MMB` to set the exposure. Zoom
and click the center of the Sun in the texture. After that, the Sun
object will be locked to it.

You can now rotate both the texture and the light by using the
*Rotation* slider.

![](docs/env-selection.png)  
Click the Sun in the environment texture in the 3D Viewport to lock it
to the sun light object.


## Authors
This add-on was originally written by Michael Martin with
contributions by Aaron Carlisle, Brendon Murphy, Campbell Barton,
Eduardo Schilling, Julian Eisel, n-Burn, and Stephen Leger.

It is currently maintained by Damien Picard.


## License
This add-on is licensed under the GPL license; either version 3 of the
License, or (at your option) any later version.
