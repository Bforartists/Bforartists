# PrimitiveCreationModals
An Addon for Blender <br />
The Primitive Creation Modals is an addon I created for blender to allow you to create primitives using drag operations like you can in other 3d software. <br />
<br />
HOW TO USE IT <br />
You can activate the modals via one of the buttons in the create tab of the tool panel in the 3d view, or in any other area that you can add a primitive mesh from. <br />
Once the modal is active you can see a box icon and 3 numbers in the top middle of the screen that tells you the modal is active and the X,Y,Z Subdivisions in the mesh where applicable. <br />
You click once where you want to start the mesh this will be where the object origin is set, and draging sizes the mesh to your mouse cursor. During the modal there are hotkey you can press to have more control.<br />
HOT KEYS: <br />
C: toggles the centers of the mesh on the current working Axis, i.e. you're dragging the size of a plane out it will toggle the center in the X and Y axis, if you are draging the Z axis it will toggle the center for the Z axis.<br />
E: toggles if the mesh is even, meaning that you can make a perfect cube if you are in the box modal, turning this off on the cylinder or sphere will allow you to make them uneven. <br />
F: Flips the axis that the Z axis is copying, by default the Z axis copys the smaller value between X,Y <br />
CTRL: Snaps the mesh to the grid. <br />
Mouse wheel: Scrolls the amount of subdivisions on the current axis of the mesh. <br />
Mouse wheel + CTRL: Scrolls the grid snap increments, anything above one it will increase/decrease it by 1, anything lower than one will increase/decrease by .25 with the lowest value being .25 <br />
SHIFT + Left click: Finishes the mesh at its current state and keep the modal active. <br />
SHIFT + Right click: Cancels the modal but keeps the mesh as it currently is. <br />
Right click, and ESC: they cancel the modal and delete anything you had made in the modal to that point.<br />
ALT + Right click: Cancels the modal keeping the mesh, but reverts it by one state. i.e. you make a box and alt + right click it will now be a plane with the same X,Y size as the box was. <br />
<br />
You can also change the size, state, segments,and centers in the undo/redo panel (F6 menu) in the bottom left corner.
