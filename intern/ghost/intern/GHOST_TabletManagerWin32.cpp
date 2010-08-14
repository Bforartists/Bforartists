// safe & friendly WinTab wrapper
// by Mike Erwin, July 2010

#include "GHOST_TabletManagerWin32.h"
#include "GHOST_WindowWin32.h"
#include "GHOST_System.h"
#include "GHOST_EventCursor.h"
#include "GHOST_EventButton.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define PACKETDATA PK_CURSOR | PK_X | PK_Y | PK_BUTTONS | PK_NORMAL_PRESSURE | PK_ORIENTATION
#define PACKETMODE 0 /*PK_BUTTONS*/
// #define PACKETTILT PKEXT_ABSOLUTE

#include "pktdef.h"

#define MAX_QUEUE_SIZE 100

static void print(AXIS const& t, char const* label = NULL)
	{
	const char* unitName[] = {"dinosaur","inch","cm","circle"};

	if (label)
		printf("%s: ", label);

	printf("%d to %d, %d.%d per %s\n",
		t.axMin, t.axMax,
		HIWORD(t.axResolution), LOWORD(t.axResolution),
		unitName[t.axUnits]);
	}

GHOST_TabletManagerWin32::GHOST_TabletManagerWin32()
	: activeWindow(NULL)
	{
	dropTool();

	// open WinTab
	lib_Wintab = LoadLibrary("wintab32.dll");

	if (lib_Wintab)
		{
		// connect function pointers
		func_Open = (WTOPENA) GetProcAddress(lib_Wintab,"WTOpenA");
		func_Close = (WTCLOSE) GetProcAddress(lib_Wintab,"WTClose");
		func_Info = (WTINFOA) GetProcAddress(lib_Wintab,"WTInfoA");
		func_QueueSizeSet = (WTQUEUESIZESET) GetProcAddress(lib_Wintab,"WTQueueSizeSet");
		func_PacketsGet = (WTPACKETSGET) GetProcAddress(lib_Wintab,"WTPacketsGet");
		func_Packet = (WTPACKET) GetProcAddress(lib_Wintab,"WTPacket");

		WORD specV, implV;
		func_Info(WTI_INTERFACE, IFC_SPECVERSION, &specV);
		func_Info(WTI_INTERFACE, IFC_IMPLVERSION, &implV);
		printf("WinTab version %d.%d (%d.%d)\n",
			HIBYTE(specV), LOBYTE(specV), HIBYTE(implV), LOBYTE(implV));

		// query for overall capabilities and ranges
		char tabletName[LC_NAMELEN];
		if (func_Info(WTI_DEVICES, DVC_NAME, tabletName))
			puts(tabletName);

		puts("active tablet area");
		AXIS xRange, yRange;
		func_Info(WTI_DEVICES, DVC_X, &xRange);
		func_Info(WTI_DEVICES, DVC_Y, &yRange);
		print(xRange,"x"); print(yRange,"y");


		func_Info(WTI_DEVICES, DVC_NCSRTYPES, &cursorCount);
		func_Info(WTI_DEVICES, DVC_FIRSTCSR, &cursorBase);

		puts("pressure sensitivity");
		AXIS pressureRange;
		hasPressure = func_Info(WTI_DEVICES, DVC_NPRESSURE, &pressureRange);// && pressureRange.axMax != 0;
		print(pressureRange);

		if (hasPressure)
			pressureScale = 1.f / pressureRange.axMax;
		else
			pressureScale = 0.f;

		puts("tilt sensitivity");
		AXIS tiltRange[3];
		hasTilt = func_Info(WTI_DEVICES, DVC_ORIENTATION, tiltRange);

		if (hasTilt)
			{
			// leave this code in place to help support tablets I haven't tested
			const char* axisName[] = {"azimuth","altitude","twist"};
			for (int i = 0; i < 3; ++i)
				print(tiltRange[i], axisName[i]);

			// cheat by using available data from Intuos4. test on other tablets!!!
			azimuthScale = 1.f / HIWORD(tiltRange[1].axResolution);
			altitudeScale = 1.f / tiltRange[1].axMax;
			}
		else
			{
			puts("none");
			azimuthScale = altitudeScale = 0.f;
			}

#if 0 // WTX_TILT -- cartesian tilt extension, no conversion needed
		// this isn't working for [mce], so let it rest for now
		printf("raw tilt sensitivity:\n");
		hasTilt = false;
		UINT tag = 0;
		UINT extensionCount;
		func_Info(WTI_INTERFACE, IFC_NEXTENSIONS, &extensionCount);
		for (UINT i = 0; i < extensionCount; ++i)
			{
			printf("trying extension %d\n", i);
			func_Info(WTI_EXTENSIONS + i, EXT_TAG, &tag);
			if (tag == WTX_TILT)
				{
				hasTilt = true;
				break;
				}
			}

		if (hasTilt)
			{
			AXIS tiltRange[2];
			func_Info(WTI_EXTENSIONS + tag, EXT_AXES, tiltRange);
			print("x", tiltRange[0]);
			print("y", tiltRange[1]);
			tiltScaleX = 1.f / tiltRange[0].axMax;
			tiltScaleY = 1.f / tiltRange[1].axMax;
			func_Info(WTI_EXTENSIONS + tag, EXT_MASK, &tiltMask);
			}
		else
			{
			puts("none");
			tiltScaleX = tiltScaleY = 0.f;
			}
#endif // WTX_TILT
		}
	}

GHOST_TabletManagerWin32::~GHOST_TabletManagerWin32()
	{
	// close WinTab
	FreeLibrary(lib_Wintab);
	}

bool GHOST_TabletManagerWin32::available()
	{
	return lib_Wintab // driver installed
		&& func_Info(0,0,NULL); // tablet plugged in
	}

HCTX GHOST_TabletManagerWin32::contextForWindow(GHOST_WindowWin32* window)
	{
	std::map<GHOST_WindowWin32*,HCTX>::iterator i = contexts.find(window);
	if (i == contexts.end())
		return 0; // not found
	else
		return i->second;
	}

void GHOST_TabletManagerWin32::openForWindow(GHOST_WindowWin32* window)
	{
	if (contextForWindow(window) != 0)
		// this window already has a tablet context
		return;

	// set up context
	LOGCONTEXT archetype;
	func_Info(WTI_DEFSYSCTX, 0, &archetype);
//	func_Info(WTI_DEFCONTEXT, 0, &archetype);

	strcpy(archetype.lcName, "blender special");

	WTPKT packetData = PACKETDATA;
	if (!hasPressure)
		packetData &= ~PK_NORMAL_PRESSURE;
	if (!hasTilt)
		packetData &= ~PK_ORIENTATION;
	archetype.lcPktData = packetData;

 	archetype.lcPktMode = PACKETMODE;
	archetype.lcOptions |= /*CXO_MESSAGES |*/ CXO_CSRMESSAGES;
//	archetype.lcOptions |= CXO_SYSTEM | CXO_MESSAGES | CXO_CSRMESSAGES;

#if PACKETMODE & PK_BUTTONS
	// we want first 5 buttons
	archetype.lcBtnDnMask = 0x1f;
	archetype.lcBtnUpMask = 0x1f;
#endif

// BEGIN derived from Wacom's TILTTEST.C:
	AXIS TabletX, TabletY;
	func_Info(WTI_DEVICES,DVC_X,&TabletX);
	func_Info(WTI_DEVICES,DVC_Y,&TabletY);
	archetype.lcInOrgX = 0;
	archetype.lcInOrgY = 0;
	archetype.lcInExtX = TabletX.axMax;
	archetype.lcInExtY = TabletY.axMax;
    /* output the data in screen coords */
	archetype.lcOutOrgX = archetype.lcOutOrgY = 0;
	archetype.lcOutExtX = GetSystemMetrics(SM_CXSCREEN);
    /* move origin to upper left */
	archetype.lcOutExtY = -GetSystemMetrics(SM_CYSCREEN);
// END

/*	if (hasTilt)
		{
		archetype.lcPktData |= tiltMask;
		archetype.lcMoveMask |= tiltMask;
		} */

	// open the context
	HCTX context = func_Open(window->getHWND(), &archetype, TRUE);

	// request a deep packet queue
	int tabletQueueSize = MAX_QUEUE_SIZE;
	while (!func_QueueSizeSet(context, tabletQueueSize))
		--tabletQueueSize;
	printf("tablet queue size: %d\n", tabletQueueSize);

	contexts[window] = context;
	}

void GHOST_TabletManagerWin32::closeForWindow(GHOST_WindowWin32* window)
	{
	HCTX context = contextForWindow(window);

	if (context)
		{
		func_Close(context);
		// also remove it from our books:
		contexts.erase(contexts.find(window));
		}
	}

void GHOST_TabletManagerWin32::convertTilt(ORIENTATION const& ort, TabletToolData& data)
	{
	// this code used to live in GHOST_WindowWin32
	// now it lives here

	float vecLen;
	float altRad, azmRad;	/* in radians */

	/*
	from the wintab spec:
	orAzimuth	Specifies the clockwise rotation of the
	cursor about the z axis through a full circular range.

	orAltitude	Specifies the angle with the x-y plane
	through a signed, semicircular range.  Positive values
	specify an angle upward toward the positive z axis;
	negative values specify an angle downward toward the negative z axis.

	wintab.h defines .orAltitude as a UINT but documents .orAltitude
	as positive for upward angles and negative for downward angles.
	WACOM uses negative altitude values to show that the pen is inverted;
	therefore we cast .orAltitude as an (int) and then use the absolute value.
	*/

	/* convert raw fixed point data to radians */
	altRad = fabs(ort.orAltitude) * altitudeScale * M_PI/2.0;
	azmRad = ort.orAzimuth * azimuthScale * M_PI*2.0;

	/* find length of the stylus' projected vector on the XY plane */
	vecLen = cos(altRad);

	/* from there calculate X and Y components based on azimuth */
	data.tilt_x = sin(azmRad) * vecLen;
	data.tilt_y = sin(M_PI/2.0 - azmRad) * vecLen;
	}

bool GHOST_TabletManagerWin32::processPackets(GHOST_WindowWin32* window)
	{
	if (window == NULL)
		window = activeWindow;

	HCTX context = contextForWindow(window);

	bool anyProcessed = false;

	if (context)
		{
//		PACKET packet;
//		func_Packet(context, serialNumber, &packet);
		PACKET packets[MAX_QUEUE_SIZE];
		int n = func_PacketsGet(context, MAX_QUEUE_SIZE, packets);
//		printf("processing %d packets\n", n);

		for (int i = 0; i < n; ++i)
			{
			PACKET const& packet = packets[i];
			TabletToolData data = {activeTool};
			int x = packet.pkX;
			int y = packet.pkY;
	
			if (activeTool.type == TABLET_MOUSE)
				if (x == prevMouseX && y == prevMouseY && packet.pkButtons == prevButtons)
					// don't send any "mouse hasn't moved" events
					continue;
				else {
					prevMouseX = x;
					prevMouseY = y;
					}

			anyProcessed = true;

			// Since we're using a digitizing context, we need to
			// move the on-screen cursor ourselves.
			// SetCursorPos(x, y);

			switch (activeTool.type)
				{
				case TABLET_MOUSE:
					printf("mouse");
					break;
				case TABLET_PEN:
					printf("pen");
					break;
				case TABLET_ERASER:
					printf("eraser");
					break;
				default:
					printf("???");
				}
	
			printf(" (%d,%d)", x, y);
	
			if (activeTool.hasPressure)
				{
				if (packet.pkNormalPressure)
					{
					data.pressure = pressureScale * packet.pkNormalPressure;
					printf(" %d%%", (int)(100 * data.pressure));
					}
				else
					data.tool.hasPressure = false;
				}
	
			if (activeTool.hasTilt)
				{
				ORIENTATION const& o = packet.pkOrientation;

				if (o.orAzimuth || o.orAltitude)
					{
					convertTilt(o, data);
					printf(" /%d,%d/", o.orAzimuth, o.orAltitude);
					printf(" /%.2f,%.2f/", data.tilt_x, data.tilt_y);
					if (fabs(data.tilt_x) < 0.001 && fabs(data.tilt_x) < 0.001)
						{
						// really should fix the initial test for activeTool.hasTilt,
						// not apply a band-aid here.
						data.tool.hasTilt = false;
						data.tilt_x = 0.f;
						data.tilt_y = 0.f;
						}
					}
				else
					data.tool.hasTilt = false;

				// data.tilt_x = tiltScaleX * packet.pkTilt.tiltX;
				// data.tilt_y = tiltScaleY * packet.pkTilt.tiltY;
				}

			// at this point, construct a GHOST event and push it into the queue!

			GHOST_System* system = (GHOST_System*) GHOST_ISystem::getSystem();

			// any buttons changed?
			#if PACKETMODE & PK_BUTTONS
			// relative buttons mode
			if (packet.pkButtons)
				{
				// which button?
				GHOST_TButtonMask e_button;
				int buttonNumber = LOWORD(packet.pkButtons);
				e_button = (GHOST_TButtonMask) buttonNumber;

				// pressed or released?
				GHOST_TEventType e_action;
				int buttonAction = HIWORD(packet.pkButtons);
				if (buttonAction == TBN_DOWN)
					e_action = GHOST_kEventButtonDown;
				else
					e_action = GHOST_kEventButtonUp;

				printf(" button %d %s\n", buttonNumber, buttonAction == TBN_DOWN ? "down" : "up");

				GHOST_EventButton* e = new GHOST_EventButton(system->getMilliSeconds(), e_action, window, e_button);
				
				system->pushEvent(e);
				}
			#else
			// absolute buttons mode
			UINT diff = prevButtons ^ packet.pkButtons;
			if (diff)
				{
				for (int i = 0; i < 32 /*GHOST_kButtonNumMasks*/; ++i)
					{
					UINT mask = 1 << i;

					if (diff & mask)
						{
						GHOST_TButtonMask e_button = (GHOST_TButtonMask) i;
						GHOST_TEventType e_action = (packet.pkButtons & mask) ? GHOST_kEventButtonDown : GHOST_kEventButtonUp;

						GHOST_EventButton* e = new GHOST_EventButton(system->getMilliSeconds(), e_action, window, e_button);
						GHOST_TabletData& e_data = ((GHOST_TEventButtonData*) e->getData())->tablet;
						e_data.Active = (GHOST_TTabletMode) data.tool.type;
						e_data.Pressure = data.pressure;
						e_data.Xtilt = data.tilt_x;
						e_data.Ytilt = data.tilt_y;

						printf(" button %d %s\n", i, (e_action == GHOST_kEventButtonDown) ? "down" : "up");

						system->pushEvent(e);
						}
					}

				prevButtons = packet.pkButtons;
				}
			#endif
			else
				{
				GHOST_EventCursor* e = new GHOST_EventCursor(system->getMilliSeconds(), GHOST_kEventCursorMove, window, x, y);

				// use older TabletData struct for testing until mine is in place
				GHOST_TabletData& e_data = ((GHOST_TEventCursorData*) e->getData())->tablet;
				e_data.Active = (GHOST_TTabletMode) data.tool.type;
				e_data.Pressure = data.pressure;
				e_data.Xtilt = data.tilt_x;
				e_data.Ytilt = data.tilt_y;

				puts(" move");

				system->pushEvent(e);
				}
			}
		}
	return anyProcessed;
	}

void GHOST_TabletManagerWin32::changeTool(GHOST_WindowWin32* window, UINT serialNumber)
	{
	puts("-- changing tool --");

	dropTool();

	HCTX context = contextForWindow(window);

	if (context)
		{
		activeWindow = window;
	
		PACKET packet;
		func_Packet(context, serialNumber, &packet);
		UINT cursor = (packet.pkCursor - cursorBase) % cursorCount;
	
		// printf("%d mod %d = %d\n", packet.pkCursor - cursorBase, cursorCount, cursor);
	
		switch (cursor)
			{
			case 0: // older Intuos tablets can track two cursors at once
			case 3: // so we test for both here
				activeTool.type = TABLET_MOUSE;
				break;
			case 1:
			case 4:
				activeTool.type = TABLET_PEN;
				break;
			case 2:
			case 5:
				activeTool.type = TABLET_ERASER;
				break;
			default:
				activeTool.type = TABLET_NONE;
			}
	
		WTPKT toolData;
		func_Info(WTI_CURSORS + packet.pkCursor, CSR_PKTDATA, &toolData);
		activeTool.hasPressure = toolData & PK_NORMAL_PRESSURE;
		activeTool.hasTilt = toolData & PK_ORIENTATION;
	//	activeTool.hasTilt = toolData & tiltMask;
	
		if (activeTool.hasPressure)
			puts(" - pressure");
	
		if (activeTool.hasTilt)
			puts(" - tilt");
	
		// and just for fun:
		if (toolData & PK_BUTTONS)
			puts(" - buttons");
		}
	}

void GHOST_TabletManagerWin32::dropTool()
	{
	activeTool.type = TABLET_NONE;
	activeTool.hasPressure = false;
	activeTool.hasTilt = false;
	
	prevMouseX = prevMouseY = 0;
	prevButtons = 0;
	
	activeWindow = NULL;
	}
