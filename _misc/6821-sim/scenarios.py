VIEW = (30, 110, 1300, 850)   # viewport area in event coords (excludes status bar, asset shelf, tabs)


def setup(cube=True):
    x, y = center(); move(x, y); yield 0.3
    key("ESC", x, y); yield 0.05
    key("ESC", x, y, None, "RELEASE"); yield 0.6
    if cube:
        with bpy.context.temp_override(**override()):
            bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 1))
        bpy.context.view_layer.objects.active.name = "Cube"
        yield 0.5
    move(*center()); yield 0.3


def rdiff(n1, n2, box=VIEW, thresh=0.04):
    x0, y0, x1, y1 = box
    return int((np.abs(FRAME[n1][y0:y1, x0:x1] - FRAME[n2][y0:y1, x0:x1]).max(axis=2) > thresh).sum())


def esc():
    x, y = center(); key("ESC", x, y); yield 0.05
    key("ESC", x, y, None, "RELEASE"); yield 0.3


PANEL = {}


def open_panel(base="base", name="SIM_PT_field"):
    """Tear off a test panel, and record geometry from the screenshot diff."""
    yield from grab(base + "_p")
    tear_panel(name); yield 0.8
    yield from grab(base + "_po")
    d = np.abs(FRAME[base + "_p"] - FRAME[base + "_po"]).max(axis=2) > 0.04
    d[:VIEW[1], :] = False; d[VIEW[3]:, :] = False; d[:, :VIEW[0]] = False; d[:, VIEW[2]:] = False
    ys, xs = np.where(d)
    b = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    log("panel bbox", b)
    xmin, ymin, xmax, ymax = b
    PANEL.update(xmin=xmin, ymax=ymax, name=(xmin + 110, ymax - 55), frame=(xmin + 110, ymax - 80),
                 arrow=(xmin + 201, ymax - 80), x=(xmin + 200, ymax - 19), title=(xmin + 80, ymax - 19),
                 box=b, shot=base + "_po")


def s_x_expanded():
    yield from setup(); yield from grab("base")
    tear_menu(); yield 0.8; yield from grab("m")
    b = bbox("base", "m"); check("menu appears", b is not None, b)
    yield from click(b[2] - 14, b[3] - 14)
    move(*center()); yield 0.3
    yield from grab("after")
    check("X closes expanded tear-off", rdiff("base", "after") < 200, rdiff("base", "after"))


SC["x_expanded"] = s_x_expanded


def s_pin():
    yield from setup(); yield from grab("base")
    tear_menu(); yield 0.8; yield from grab("m")
    b = bbox("base", "m")
    yield from click(b[2] - 34, b[3] - 14)
    move(*center()); yield 0.3
    yield from grab("col")
    c = bbox("base", "col"); log("collapsed", c)
    check("pin icon collapses", c is not None and (c[3] - c[1]) < 60, c)
    # Pin icon expands again, at the same spot.
    yield from click(c[2] - 40, (c[1] + c[3]) // 2)
    move(*center()); yield 0.4
    yield from grab("exp")
    check("pin icon expands in place", rdiff("m", "exp") < 400, rdiff("m", "exp"))
    yield from click(b[2] - 34, b[3] - 14)
    move(*center()); yield 0.3
    yield from grab("col2")
    c = bbox("base", "col2")
    yield from click(c[2] - 15, (c[1] + c[3]) // 2)
    yield from grab("after")   # no extra mouse move: must close straight away
    check("X on collapsed pin closes it at once", rdiff("base", "after") < 200, rdiff("base", "after"))


SC["pin"] = s_pin


def s_text_field():
    yield from setup(); yield from grab("base")
    yield from open_panel()
    ob = bpy.context.view_layer.objects.active
    sel0 = len(bpy.context.view_layer.objects.selected)
    nx, ny = PANEL["name"]
    yield from click(nx, ny); yield 0.3
    yield from grab("editing")
    yield from type_key("A", nx, ny, "a")
    yield from type_key("X", nx, ny, "x")
    yield from type_key("RET", nx, ny)
    yield 0.3
    check("typing in torn-off text field, cursor inside", ob.name == "ax", ob.name)
    check("keys did not reach the editor (inside)",
          len(bpy.context.view_layer.objects.selected) == sel0 and "ax" in bpy.data.objects)
    # Cursor outside while editing: keys stay with the field.
    yield from click(nx, ny); yield 0.3
    cx, cy = center(); move(cx, cy - 250); yield 0.3
    yield from type_key("A", cx, cy - 250, "a")
    yield from type_key("B", cx, cy - 250, "b")
    yield from type_key("RET", cx, cy - 250); yield 0.3
    check("typing with cursor outside stays in field", ob.name == "ab", ob.name)
    check("keys did not select in viewport (outside)",
          len(bpy.context.view_layer.objects.selected) == sel0, len(bpy.context.view_layer.objects.selected))
    # Escape cancels.
    yield from click(nx, ny); yield 0.3
    yield from type_key("Q", nx, ny, "q")
    yield from type_key("ESC", nx, ny); yield 0.3
    check("Esc cancels the edit", ob.name == "ab", ob.name)
    yield from grab("afteresc")
    box = (PANEL["xmin"], PANEL["ymax"] - 40, PANEL["xmin"] + 200, PANEL["ymax"])
    check("Esc does not close the tear-off", rdiff("afteresc", "base_po", box) < 400, rdiff("afteresc", "base_po", box))


SC["text_field"] = s_text_field


def s_hotkeys():
    yield from setup(); yield from grab("base")
    cx, cy = center(); cy -= 250; move(cx, cy); yield 0.4
    move(cx, cy); yield 0.4
    ob = bpy.context.view_layer.objects.active
    yield from type_key("TAB", cx, cy); yield 0.8
    log("BASELINE no tear-off, after TAB mode =", ob.mode)
    if ob.mode != "OBJECT":
        yield from type_key("TAB", cx, cy); yield 0.8
    log("BASELINE after second TAB mode =", ob.mode)
    move(*center()); yield 0.3
    yield from open_panel()
    cx, cy = center(); cy -= 250; move(cx, cy); yield 0.4
    move(cx, cy); yield 0.4
    yield from type_key("TAB", cx, cy); yield 0.8
    check("hotkey passes through to the editor", ob.mode == "EDIT", ob.mode)
    yield from grab("edit")
    py = PANEL["ymax"] - 40
    box = (PANEL["xmin"] + 20, py, PANEL["xmin"] + 180, py + 20)
    check("hidden in another mode", rdiff("edit", "base_po", box) > 50, rdiff("edit", "base_po", box))
    yield from type_key("TAB", cx, cy); yield 0.8
    yield from grab("obj")
    check("back in its mode", ob.mode == "OBJECT", ob.mode)
    check("reappears in its mode", rdiff("obj", "base_po", box) < 200, rdiff("obj", "base_po", box))


SC["hotkeys"] = s_hotkeys


def s_number():
    yield from setup(); yield from grab("base")
    yield from open_panel()
    sc = bpy.context.scene
    fx, fy = PANEL["frame"]
    yield from click(fx, fy); yield 0.3
    yield from type_key("SEVEN", fx, fy, "7")
    yield from type_key("RET", fx, fy); yield 0.4
    check("click edits a number field, value typed", sc.frame_current == 7, sc.frame_current)
    ax, ay = PANEL["arrow"]
    f1 = sc.frame_current
    yield from click(ax, ay); yield 0.2
    yield from click(ax, ay); yield 0.4
    check("arrow steps twice", sc.frame_current == f1 + 2, sc.frame_current)
    yield from grab("arrows")
    title_box = (PANEL["xmin"] + 10, PANEL["ymax"] - 30, PANEL["xmin"] + 180, PANEL["ymax"] - 8)
    check("panel still expanded", rdiff("arrows", "base_po", title_box) < 100, rdiff("arrows", "base_po", title_box))


SC["number"] = s_number


def s_dialog():
    yield from setup(); yield from grab("base")
    st = SIM_OT_dialog.state
    with bpy.context.temp_override(**override()):
        bpy.ops.sim.dialog("INVOKE_DEFAULT")
    yield 0.6
    yield from click(778, 498); yield 0.3
    move(*center()); yield 0.4
    yield from grab("c")
    check("regular dialog Cancel runs cancel", st["cancel"] == 1, st)
    check("regular dialog Cancel closes it", rdiff("base", "c") < 200, rdiff("base", "c"))
    with bpy.context.temp_override(**override()):
        bpy.ops.sim.dialog("INVOKE_DEFAULT")
    yield 0.6
    yield from click(623, 498); yield 0.3
    move(*center()); yield 0.4
    yield from grab("o")
    check("regular dialog OK runs exec", st["exec"] == 1, st)
    check("regular dialog OK closes it", rdiff("base", "o") < 200, rdiff("base", "o"))


SC["dialog"] = s_dialog


def s_dialog_drag():
    yield from setup(); yield from grab("base")
    with bpy.context.temp_override(**override()):
        bpy.ops.sim.dialog("INVOKE_DEFAULT")
    yield 0.6; yield from grab("d0")
    d0 = bbox("base", "d0"); log("dialog", d0)
    tx, ty = 600, 567; dx = 300
    move(tx, ty); yield 0.3; move(tx, ty); yield 0.3
    press(tx, ty); yield 0.1
    for i in range(1, 11):
        move(tx + dx * i // 10, ty); yield 0.05
    release(tx + dx, ty); yield 0.4
    yield from grab("d1")
    old_box, new_box = (560, 490, 840, 575), (860, 490, 1140, 575)
    check("dialog drag leaves its old spot", rdiff("base", "d1", old_box) < 200, rdiff("base", "d1", old_box))
    check("dialog drag arrives at new spot", rdiff("base", "d1", new_box) > 2000, rdiff("base", "d1", new_box))
    # Force a refresh: click the value arrow, then look again.
    ax, ay = 822 + dx, 528
    yield from click(ax, ay); yield 0.4
    move(ax, ay - 25); yield 0.3
    yield from grab("d2")
    check("dialog stays put after a refresh (old spot empty)", rdiff("base", "d2", old_box) < 200, rdiff("base", "d2", old_box))
    check("dialog stays put after a refresh (new spot used)", rdiff("base", "d2", new_box) > 2000, rdiff("base", "d2", new_box))
    yield from click(778 + dx, 498); yield 0.3


SC["dialog_drag"] = s_dialog_drag


def s_file_new():
    yield from setup(cube=False)
    yield from click(20, 987); yield 0.4
    yield from grab("menu")
    yield from click(52, 937); yield 1.5
    yield from grab("after")
    log("file new ok, scene", bpy.context.scene.name)


SC["file_new"] = s_file_new


def s_file_new_torn():
    yield from setup(cube=False)
    tear_menu(); yield 0.8
    tear_panel("SIM_PT_field"); yield 0.8
    yield from click(20, 987); yield 0.4
    yield from click(52, 937); yield 1.5
    move(*center()); yield 0.5
    yield from grab("after")
    move(600, 600); yield 0.3
    press(600, 600); yield 0.05
    release(600, 600); yield 0.4
    yield from grab("after2")


SC["file_new_torn"] = s_file_new_torn


def s_top_tear():
    yield from setup(); yield from grab("base")
    yield from click(20, 987); yield 0.4
    yield from click(80, 964); yield 0.8
    move(*center()); yield 0.4
    yield from grab("torn")
    b = bbox("base", "torn"); log("top bar tear-off", b)
    check("tear-off from the top bar stays visible", b is not None and (b[2] - b[0]) > 100 and (b[3] - b[1]) > 200, b)
    yield from click(b[2] - 14, b[3] - 14)
    move(*center()); yield 0.4
    yield from grab("closed")
    full = (0, 0, 1600, 1000)
    check("its X closes it", rdiff("base", "closed", full) < 300, rdiff("base", "closed", full))


SC["top_tear"] = s_top_tear


def s_area_close():
    yield from setup(); yield from grab("base")
    with bpy.context.temp_override(**override()):
        bpy.ops.screen.area_split(direction="VERTICAL", factor=0.5)
    yield 0.8
    log("3d views", len([a for a in scr().areas if a.type == "VIEW_3D"]))
    move(*center()); yield 0.3
    yield from open_panel("b2")
    a0 = area("VIEW_3D", 0)
    with bpy.context.temp_override(window=win(), screen=scr(), area=a0, region=region_of(a0)):
        bpy.ops.screen.area_close()
    yield 0.6
    log("3d views after close", len([a for a in scr().areas if a.type == "VIEW_3D"]))
    for i in range(4):
        move(PANEL["xmin"] + 60 + i * 20, PANEL["ymax"] - 60); yield 0.15
    sc = bpy.context.scene; f0 = sc.frame_current
    yield from click(*PANEL["arrow"]); yield 0.4
    yield from grab("a")
    check("tear-off works after its source area closed", sc.frame_current == f0 + 1, sc.frame_current)


SC["area_close"] = s_area_close


def s_type_change():
    yield from setup(); yield from grab("base")
    yield from open_panel()
    a0 = area()
    a0.type = "CONSOLE"; yield 0.8
    for i in range(4):
        move(PANEL["xmin"] + 60 + i * 20, PANEL["ymax"] - 60); yield 0.15
    yield from click(*PANEL["arrow"]); yield 0.4
    yield from grab("cons")
    [a for a in scr().areas if a.type == "CONSOLE"][0].type = "VIEW_3D"; yield 0.8
    move(*center()); yield 0.4
    yield from grab("back")
    sc = bpy.context.scene; f0 = sc.frame_current
    yield from click(*PANEL["arrow"]); yield 0.4
    check("tear-off works after the editor type round trip", sc.frame_current == f0 + 1, sc.frame_current)


SC["type_change"] = s_type_change


def s_maximize():
    yield from setup(); yield from grab("base")

    def full():
        a = area()
        with bpy.context.temp_override(window=win(), screen=scr(), area=a, region=region_of(a)):
            bpy.ops.screen.screen_full_area()
    full(); yield 0.8
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from grab("maxed")
    full(); yield 0.8
    for i in range(6):
        move(500 + i * 40, 500); yield 0.1
    yield from grab("restored")
    full(); yield 0.8
    for i in range(6):
        move(500 + i * 40, 500); yield 0.1
    full(); yield 0.8
    move(*center()); yield 0.3
    yield from grab("final")


SC["maximize"] = s_maximize


def s_workspace():
    yield from setup(); yield from grab("base")
    yield from open_panel()
    main = win().workspace
    win().workspace = bpy.data.workspaces["Shading"]; yield 1.2
    for i in range(4):
        move(PANEL["xmin"] + 60 + i * 20, PANEL["ymax"] - 60); yield 0.15
    yield from grab("other")
    win().workspace = main; yield 1.0
    move(*center()); yield 0.4
    yield from grab("back")
    box = (PANEL["xmin"] + 20, PANEL["ymax"] - 90, PANEL["xmin"] + 180, PANEL["ymax"] - 10)
    check("visible again in its workspace", rdiff("back", "base_po", box) < 300, rdiff("back", "base_po", box))
    sc = bpy.context.scene; f0 = sc.frame_current
    yield from click(*PANEL["arrow"]); yield 0.4
    check("works after workspace round trip", sc.frame_current == f0 + 1, sc.frame_current)


SC["workspace"] = s_workspace


def s_ws_delete():
    yield from setup(); yield from grab("base")
    yield from open_panel()
    with bpy.context.temp_override(window=win()):
        bpy.ops.workspace.delete()
    yield 1.2
    log("workspace now", win().workspace.name, "main exists", "Main" in bpy.data.workspaces)
    for i in range(4):
        move(500 + i * 40, 500); yield 0.15
    with bpy.context.temp_override(window=win()):
        bpy.ops.workspace.duplicate()
    yield 1.0
    move(600, 500); yield 0.3
    yield from grab("dup")


SC["ws_delete"] = s_ws_delete


def s_reload():
    yield from setup(); yield from grab("base")
    tear_menu(); yield 0.8
    yield from open_panel()
    bpy.ops.script.reload()
    yield 6.0
    log("window still present after reload", bpy.context.window_manager.windows[0] is not None)
    move(*center()); yield 0.4
    yield from grab("after")
    sc = bpy.context.scene; f0 = sc.frame_current
    yield from click(*PANEL["arrow"]); yield 0.4
    log("frame", f0, "->", sc.frame_current)
    yield from grab("after2")


SC["reload"] = s_reload


def s_delete_undo():
    yield from setup(); yield from grab("base")
    bpy.ops.ed.undo_push(message="before")
    yield from open_panel()
    with bpy.context.temp_override(**override()):
        bpy.ops.object.delete(use_global=False, confirm=False)
    yield 0.6
    for i in range(5):
        move(PANEL["xmin"] + 60 + i * 20, PANEL["ymax"] - 56); yield 0.15
    yield from grab("deleted")
    check("object gone", "Cube" not in bpy.data.objects)
    bpy.ops.ed.undo_push(message="deleted")
    with bpy.context.temp_override(window=win(), screen=scr()):
        bpy.ops.ed.undo()
    yield 0.8
    for i in range(5):
        move(PANEL["xmin"] + 60 + i * 20, PANEL["ymax"] - 56); yield 0.15
    yield from grab("undone")
    check("object back after undo", "Cube" in bpy.data.objects)
    with bpy.context.temp_override(window=win(), screen=scr()):
        bpy.ops.ed.redo()
    yield 0.8
    for i in range(5):
        move(PANEL["xmin"] + 60 + i * 20, PANEL["ymax"] - 56); yield 0.15
    yield from click(*PANEL["name"]); yield 0.3
    yield from type_key("ESC", *PANEL["name"]); yield 0.3
    yield from grab("redone")


SC["delete_undo"] = s_delete_undo


def s_dpi():
    yield from setup(); yield from grab("base")
    yield from open_panel()
    tear_menu(); yield 0.8
    yield from grab("before")
    bpy.context.preferences.view.ui_scale = 1.5
    yield 1.5
    move(*center()); yield 0.4
    yield from grab("big")
    bpy.context.preferences.view.ui_scale = 1.0
    yield 1.5
    move(*center()); yield 0.4
    yield from grab("small")
    box = (420, 800, 640, 735)
    box = (420, 650, 640, 735)
    check("menu returns to the same place after a scale change", rdiff("before", "small", box) < 800, rdiff("before", "small", box))


SC["dpi"] = s_dpi


def s_accel():
    yield from setup(); yield from grab("base")
    yield from click(406, 933); yield 0.4
    yield from grab("open")
    yield from type_key("T", 406, 933, "t"); yield 0.5
    yield from grab("t")
    for i in range(3):
        yield from esc()
    move(*center()); yield 0.4
    yield from grab("end")
    check("T in a menu does not tear it off", rdiff("base", "end") < 300, rdiff("base", "end"))


SC["accel"] = s_accel


def s_wheel():
    yield from setup(); yield from grab("base")
    rd = bpy.context.scene.render
    fx, fy = 1527, 554

    def wheel():
        move(fx, fy); yield 0.3
        move(fx, fy); yield 0.3
        win().event_simulate(type="WHEELDOWNMOUSE", value="PRESS", ctrl=True, x=fx, y=fy); yield 0.5
    v0 = rd.resolution_x
    yield from wheel()
    v1 = rd.resolution_x
    log("baseline ctrl+wheel", v0, "->", v1)
    move(*center()); yield 0.3
    tear_menu(); yield 0.8
    yield from wheel()
    v2 = rd.resolution_x
    if v0 == v1:
        log("INCONCLUSIVE: ctrl+wheel did nothing without a tear-off either")
    else:
        check("Ctrl+wheel on a field works with a tear-off open", v2 != v1, (v1, v2))
    yield from grab("w")


SC["wheel"] = s_wheel


def find_kmi(kmname, idname, **props):
    kc = bpy.context.window_manager.keyconfigs.active
    log("keyconfig", kc.name)
    for k in kc.keymaps[kmname].keymap_items:
        if k.idname == idname and k.active and k.value == "PRESS":
            if all(getattr(k.properties, n, None) == v for n, v in props.items()):
                return k
    return None


def send_kmi(k, x, y):
    win().event_simulate(type=k.type, value="PRESS", x=x, y=y, shift=bool(k.shift), ctrl=bool(k.ctrl), alt=bool(k.alt)); yield 0.05
    win().event_simulate(type=k.type, value="RELEASE", x=x, y=y, shift=bool(k.shift), ctrl=bool(k.ctrl), alt=bool(k.alt)); yield 0.6


def s_hotkeys2():
    yield from setup(); yield from grab("base")
    sel = lambda: len(bpy.context.view_layer.objects.selected)
    k_all = find_kmi("Object Mode", "object.select_all", action="SELECT")
    k_none = find_kmi("Object Mode", "object.select_all", action="DESELECT")
    k_tog = find_kmi("Object Non-modal", "object.editmode_toggle") or find_kmi("Object Mode", "object.editmode_toggle")
    log("select all", k_all and (k_all.type, k_all.ctrl, k_all.shift, k_all.alt), "deselect", k_none and (k_none.type, k_none.ctrl, k_none.shift, k_none.alt), "toggle", k_tog and k_tog.type)
    cx, cy = center(); cy -= 250
    move(cx, cy); yield 0.4
    move(cx, cy); yield 0.4
    # Baseline without a tear-off: the key must work at all, otherwise the test means nothing.
    n0 = sel()
    yield from send_kmi(k_none, cx, cy)
    n1 = sel()
    yield from send_kmi(k_all, cx, cy)
    n2 = sel()
    log("BASELINE selected", n0, "deselect->", n1, "select all->", n2)
    check("baseline hotkeys work without a tear-off", n1 == 0 and n2 > 0, (n0, n1, n2))
    move(*center()); yield 0.3
    yield from open_panel()
    cx, cy = center(); cy -= 250
    move(cx, cy); yield 0.4
    move(cx, cy); yield 0.4
    yield from send_kmi(k_none, cx, cy)
    n3 = sel()
    check("hotkey passes through a tear-off, cursor in the editor", n3 == 0, n3)
    yield from send_kmi(k_all, cx, cy)
    n4 = sel()
    check("second hotkey passes through too", n4 > 0, n4)
    # Cursor over the tear-off, nothing being edited.
    px, py = PANEL["xmin"] + 110, PANEL["ymax"] - 19
    move(px, py); yield 0.4
    move(px, py); yield 0.4
    yield from send_kmi(k_none, px, py)
    log("deselect with the cursor over the tear-off title ->", sel())
    yield from grab("after")
    box = (PANEL["xmin"] + 20, PANEL["ymax"] - 40, PANEL["xmin"] + 180, PANEL["ymax"] - 8)
    check("tear-off survives hotkeys", rdiff("after", "base_po", box) < 400, rdiff("after", "base_po", box))
    # Mode change hides and restores it.
    ob = bpy.context.view_layer.objects.active
    if bpy.context.view_layer.objects.active:
        with bpy.context.temp_override(**override()):
            bpy.ops.object.mode_set(mode="EDIT")
        yield 1.0
        move(cx, cy); yield 0.4
        yield from grab("edit")
        b2 = (PANEL["xmin"] + 20, PANEL["ymax"] - 90, PANEL["xmin"] + 180, PANEL["ymax"] - 10)
        check("hidden in another mode", rdiff("edit", "base_po", b2) > 50, rdiff("edit", "base_po", b2))
        with bpy.context.temp_override(**override()):
            bpy.ops.object.mode_set(mode="OBJECT")
        yield 1.0
        move(cx, cy); yield 0.4
        yield from grab("obj")
        check("reappears in its mode", rdiff("obj", "base_po", b2) < 400, rdiff("obj", "base_po", b2))


SC["hotkeys2"] = s_hotkeys2


def s_pref_off():
    yield from setup(); yield from grab("base")
    prefs = bpy.context.preferences
    log("use_tear_off starts", prefs.use_tear_off)
    check("defaults to on", prefs.use_tear_off is True)
    check("menu operator polls while on", bpy.ops.wm.menu_tear_off.poll())
    yield from click(406, 933); yield 0.4
    yield from grab("menu_on")
    on = bbox("base", "menu_on"); log("menu with row", on)
    yield from esc(); yield from esc()
    move(*center()); yield 0.4
    # An expanded, a collapsed and a hidden tear-off must all close when turned off.
    tear_menu(); yield 0.8
    yield from grab("torn")
    b = bbox("base", "torn")
    yield from click(b[2] - 34, b[3] - 14)   # collapse it
    move(*center()); yield 0.3
    move(center()[0] - 400, center()[1]); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    move(*center()); yield 0.3
    prefs.use_tear_off = False
    yield 0.6
    move(*center()); yield 0.5
    yield from grab("off")
    check("turning it off closes open tear-offs", rdiff("base", "off") < 300, rdiff("base", "off"))
    check("menu operator fails poll while off", not bpy.ops.wm.menu_tear_off.poll())
    check("panel operator fails poll while off", not bpy.ops.wm.panel_tear_off.poll())
    yield from click(406, 933); yield 0.4
    yield from grab("menu_off")
    off = bbox("base", "menu_off"); log("menu without row", off)
    # The menu's bottom row sits lower with the extra row, so that strip only differs when on.
    strip = (400, 200, 570, 215)
    check("menu has the row while on", rdiff("base", "menu_on", strip) > 200, rdiff("base", "menu_on", strip))
    check("menu has no row while off", rdiff("base", "menu_off", strip) < 50, rdiff("base", "menu_off", strip))
    yield from esc(); yield from esc()
    prefs.use_tear_off = True
    yield 0.4
    move(*center()); yield 0.3
    tear_menu(); yield 0.8
    yield from grab("again")
    check("works again after turning it back on", bbox("base", "again") is not None)


SC["pref_off"] = s_pref_off


def s_hover_keys():
    yield from setup(); yield from grab("base")
    yield from open_panel()
    wm = bpy.context.window_manager
    fx, fy = PANEL["frame"]
    sc = bpy.context.scene
    sc.frame_current = 42
    yield 0.4
    move(fx, fy); yield 0.3
    move(fx, fy); yield 0.3
    win().event_simulate(type="C", value="PRESS", ctrl=True, x=fx, y=fy); yield 0.05
    win().event_simulate(type="C", value="RELEASE", ctrl=True, x=fx, y=fy); yield 0.5
    check("Ctrl+C copies the hovered torn-off field", wm.clipboard.strip() == "42", repr(wm.clipboard))
    wm.clipboard = "7"
    yield 0.2
    move(fx + 2, fy); yield 0.3
    win().event_simulate(type="V", value="PRESS", ctrl=True, x=fx + 2, y=fy); yield 0.05
    win().event_simulate(type="V", value="RELEASE", ctrl=True, x=fx + 2, y=fy); yield 0.5
    check("Ctrl+V pastes into the hovered torn-off field", sc.frame_current == 7, sc.frame_current)
    k_none = find_kmi("Object Mode", "object.select_all", action="DESELECT")
    k_all = find_kmi("Object Mode", "object.select_all", action="SELECT")
    yield from send_kmi(k_none, fx, fy)
    check("plain hotkey over a torn-off field still reaches the editor", len(bpy.context.view_layer.objects.selected) == 0, len(bpy.context.view_layer.objects.selected))
    yield from send_kmi(k_all, fx, fy)
    check("second hotkey too", len(bpy.context.view_layer.objects.selected) > 0)
    yield from grab("end")
    box = (PANEL["xmin"] + 20, PANEL["ymax"] - 40, PANEL["xmin"] + 180, PANEL["ymax"] - 8)
    check("hotkeys do not close the tear-off", rdiff("end", "base_po", box) < 400, rdiff("end", "base_po", box))


SC["hover_keys"] = s_hover_keys


# ---------------------------------------------------------------- Phase 4: enum tear-offs
# Not run yet. Every click below is relative to a logged bbox, and each scenario saves a shot
# before it clicks, so the first run can calibrate these offsets (100% scale):
# - TEAR_ROW0 and ROW are measured on pin-m.png, a torn-off menu with items right under its header.
# - MENU_BOTTOM is measured on the same shot. LINE is the gap between its rows around a separator.
# - Rows inside attached dropdowns are worked out from those, no shot of one exists yet.
ROW = 20
TEAR_ROW0 = 41
MENU_BOTTOM = 15
LINE = 7
ID_OB = 16975  # MAKE_ID2('O', 'B') in DNA_ID_enums.h.
PIVOTS = ("BOUNDING_BOX_CENTER", "CURSOR", "INDIVIDUAL_ORIGINS", "MEDIAN_POINT", "ACTIVE_ELEMENT")
SIM_ENUM_ITEMS = [("", "Head A", ""), ("A1", "Item A1", ""), ("A2", "Item A2", ""),
                  ("", "Head B", ""), ("B1", "Item B1", ""), ("B2", "Item B2", "")]


def tear_row(b, i=0):
    """Item i of a single column tear-off with bbox b, counted from the top."""
    return (b[0] + b[2]) // 2, b[3] - TEAR_ROW0 - ROW * i


def to_rest():
    """Park the cursor on the viewport, below tear-offs opened at the center, so nothing hovers."""
    cx, cy = center()
    move(cx, cy - 250); yield 0.3
    move(cx, cy - 250); yield 0.3


def view_bbox(n1, n2, below=None, skip=None, thresh=0.04):
    """bbox() inside VIEW only, for frames where headers changed. `below` keeps the rows under y,
    `skip` drops a box such as the panel."""
    d = np.abs(FRAME[n1] - FRAME[n2]).max(axis=2) > thresh
    d[:VIEW[1], :] = False; d[VIEW[3]:, :] = False; d[:, :VIEW[0]] = False; d[:, VIEW[2]:] = False
    if below is not None:
        d[below:, :] = False
    if skip is not None:
        d[skip[1]:skip[3] + 1, skip[0]:skip[2] + 1] = False
    if not d.any():
        return None
    ys, xs = np.where(d)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def is_popup(b):
    return b is not None and (b[2] - b[0]) > 100 and (b[3] - b[1]) > 40


def brightest(name, box):
    x0, y0, x1, y1 = box
    return float(FRAME[name][y0:y1, x0:x1].max())


def items_box(b):
    """The tear-off's rows below its first item."""
    return b[0] + 6, b[1] + 2, b[2] - 6, b[3] - 52


def first_item_box(b):
    return b[0] + 6, b[3] - 50, b[0] + 150, b[3] - 32


def label_box(b):
    """The left of the header row. The icons can move, because the width follows the content."""
    return b[0], b[3] - 24, b[0] + 100, b[3]


def panel_row(i=0):
    """Row i of the torn-off SIM_PT_enum."""
    return PANEL["xmin"] + 110, PANEL["ymax"] - 55 - 25 * i


def open_dropdown(i, name):
    """Click row i of the torn-off panel and return the bbox of what opened under the button.
    The button itself highlights, so the rows from its bottom edge upward are left out."""
    x, y = panel_row(i)
    yield from click(x, y); yield 0.4
    yield from grab(name)
    d = view_bbox(PANEL["shot"], name, below=y - 12)
    log("dropdown", name, "button", (x, y), "bbox", d)
    return d


def pivot_item_y(d, i):
    """Item i in the attached pivot dropdown, measured up from its bottom edge."""
    return d[1] + MENU_BOTTOM + ROW * (len(PIVOTS) - 1 - i)


def pivot_row_y(d):
    """The Tear Off row in the attached pivot dropdown: above the items and their line."""
    return d[1] + MENU_BOTTOM + ROW * len(PIVOTS) + LINE


def open_pivot_panel():
    """Open SIM_PT_enum high in the viewport, so a dropdown has room to open downward."""
    cx, cy = center()
    move(cx, cy + 250); yield 0.3
    yield from open_panel(name="SIM_PT_enum")


def dopesheet_area():
    """Turn the largest area other than the 3D View into a Dope Sheet, and return its index among
    the Dope Sheets, because the short timeline at the bottom may already count as one."""
    a = max((a for a in scr().areas if a.type != "VIEW_3D"), key=lambda a: a.width * a.height)
    a.type = "DOPESHEET_EDITOR"; yield 0.8
    ptrs = [x.as_pointer() for x in scr().areas if x.type == "DOPESHEET_EDITOR"]
    idx = ptrs.index(a.as_pointer())
    log("dope sheet index", idx, "of", len(ptrs), "size", (a.width, a.height),
        "mode", a.spaces.active.mode)
    return idx


def first_key():
    from bpy_extras import anim_utils
    ad = bpy.data.objects["Cube"].animation_data
    bag = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return bag.fcurves[0].keyframe_points[0]


def s_after_ctx():
    yield from setup()
    idx = yield from dopesheet_area()
    move(*center()); yield 0.3
    yield from grab("base")
    tear_menu("SIM_MT_ctx", t="DOPESHEET_EDITOR", rt="WINDOW", idx=idx); yield 0.8
    yield from grab("m")
    b = bbox("base", "m"); log("tear-off bbox", b)
    check("menu appears over the 3D View", b is not None, b)
    st = SIM_OT_area_probe.state
    x, y = tear_row(b)
    yield from click(x, y); yield 0.4
    check("probe runs in the tear-off's own area", st["area"] == "DOPESHEET_EDITOR", st)
    # The cursor stays over the tear-off through the switch, with the 3D View under it.
    st["area"] = None
    main = win().workspace
    win().workspace = bpy.data.workspaces["Shading"]; yield 1.2
    yield from grab("other")
    win().workspace = main; yield 1.0
    yield from grab("back")
    yield from click(x, y); yield 0.4
    check("probe keeps its area after a workspace round trip",
          st["area"] == "DOPESHEET_EDITOR",
          st)


SC["after_ctx"] = s_after_ctx


def s_row_value():
    yield from setup()
    ts = bpy.context.tool_settings
    ts.transform_pivot_point = "CURSOR"; yield 0.3
    yield from open_pivot_panel()
    x = panel_row(0)[0]
    # A regular item still applies.
    d = yield from open_dropdown(0, "dd1")
    yield from click(x, pivot_item_y(d, 2)); yield 0.4
    check("a regular item still applies",
          ts.transform_pivot_point == "INDIVIDUAL_ORIGINS",
          ts.transform_pivot_point)
    ts.transform_pivot_point = "CURSOR"; yield 0.3
    # The row picks no value.
    d = yield from open_dropdown(0, "dd2")
    y = pivot_row_y(d); log("row click", (x, y))
    yield from click(x, y); yield 0.6
    yield from to_rest()
    yield from grab("after")
    check("the row leaves the value alone",
          ts.transform_pivot_point == "CURSOR",
          ts.transform_pivot_point)
    nb = view_bbox("base_po", "after", skip=PANEL["box"]); log("new popup", nb)
    check("the row opens a tear-off", is_popup(nb), nb)
    # Same for a menu attached to a property, the live bug at properties_render.py:131.
    prefs = bpy.context.preferences
    settings = bpy.context.scene.sequencer_colorspace_settings
    settings.name = "Non-Color"; yield 0.3
    prefs.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    prefs.use_tear_off = True; yield 0.4
    cx, cy = center(); move(cx, cy + 250); yield 0.3
    yield from open_panel("b2", "SIM_PT_enum")
    d = yield from open_dropdown(1, "dd3")
    # A menu bound to its button has no row, and still lists its items inside a torn-off panel.
    check("the color space menu lists items in a torn-off panel", is_popup(d) and (d[3] - d[1]) > 100, d)
    # The top rows open submenus and depend on the color config, so pick the bottom one: Working Space.
    mx = panel_row(1)[0]
    yield from click(mx, d[1] + 14); yield 0.6
    yield from to_rest()
    yield from grab("after3")
    check("picking an item applies it", settings.name != "Non-Color", settings.name)
    nb = view_bbox("b2_po", "after3", skip=PANEL["box"]); log("new popup from the menu", nb)
    check("no new popup", not is_popup(nb), nb)


SC["row_value"] = s_row_value


def s_num_keys():
    yield from setup()
    ts = bpy.context.tool_settings
    ts.transform_pivot_point = "CURSOR"; yield 0.3
    yield from open_pivot_panel()
    x = panel_row(0)[0]
    d = yield from open_dropdown(0, "dd1")
    y = pivot_item_y(d, 3)
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    yield from type_key("ONE", x, y, "1"); yield 0.6
    yield from to_rest()
    yield from grab("after1")
    check("key 1 picks the first item",
          ts.transform_pivot_point == "BOUNDING_BOX_CENTER",
          ts.transform_pivot_point)
    nb = view_bbox("base_po", "after1", skip=PANEL["box"]); log("after key 1", nb)
    check("key 1 does not tear off", not is_popup(nb), nb)
    d = yield from open_dropdown(0, "dd2")
    y = pivot_item_y(d, 3)
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    yield from type_key("TWO", x, y, "2"); yield 0.6
    check("key 2 picks the second item",
          ts.transform_pivot_point == "CURSOR",
          ts.transform_pivot_point)


SC["num_keys"] = s_num_keys


def s_multicol_header():
    yield from setup(); yield from grab("base")
    tear_menu("SIM_MT_cols"); yield 0.8
    yield from to_rest()
    yield from grab("m")
    b = bbox("base", "m"); log("multi-column tear-off", b)
    check("menu appears", b is not None, b)
    st = SIM_OT_area_probe.state
    yield from click(b[2] - 60, b[3] - TEAR_ROW0); yield 0.4
    check("an item in the last column clicks", st["runs"] == 1, st)
    yield from click(b[2] - 34, b[3] - 14)
    yield from to_rest()
    yield from grab("col")
    c = bbox("base", "col"); log("collapsed", c)
    check("pin icon collapses", c is not None and (c[3] - c[1]) < 60, c)
    yield from click(c[2] - 40, (c[1] + c[3]) // 2)
    yield from to_rest()
    yield from grab("exp")
    check("pin icon expands in place", rdiff("m", "exp") < 400, rdiff("m", "exp"))
    yield from click(b[2] - 14, b[3] - 14)
    yield from to_rest()
    yield from grab("after")
    check("X closes it", rdiff("base", "after") < 200, rdiff("base", "after"))


SC["multicol_header"] = s_multicol_header


def s_enum_prop():
    yield from setup()
    ts = bpy.context.tool_settings
    ts.transform_pivot_point = "ACTIVE_ELEMENT"; yield 0.3
    yield from grab("base")
    r = tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    check("operator runs", r == {"INTERFACE"}, r)
    check("tearing off leaves the value",
          ts.transform_pivot_point == "ACTIVE_ELEMENT",
          ts.transform_pivot_point)
    yield from to_rest()
    yield from grab("m")
    b = bbox("base", "m"); log("pivot tear-off", b)
    check("tear-off appears", is_popup(b), b)
    # In this order each click changes the value, and the last one differs from frame "m".
    for i in (0, 1, 2, 4, 3):
        x, y = tear_row(b, i); log("click item", i, (x, y))
        yield from click(x, y); yield 0.3
        check("item applies: " + PIVOTS[i],
              ts.transform_pivot_point == PIVOTS[i],
              ts.transform_pivot_point)
    yield from to_rest()
    yield from grab("after")
    check("stays open in place",
          rdiff("m", "after", label_box(b)) < 100,
          rdiff("m", "after", label_box(b)))
    check("the highlight follows", rdiff("m", "after", b) > 100, rdiff("m", "after", b))
    ts.transform_pivot_point = "CURSOR"; yield 0.6
    yield from grab("py")
    check("follows a change from elsewhere",
          rdiff("after", "py", b) > 100,
          rdiff("after", "py", b))


SC["enum_prop"] = s_enum_prop


def s_enum_gone():
    yield from setup(); yield from grab("base")
    ob = bpy.context.view_layer.objects.active
    ob.rotation_mode = "XYZ"
    bpy.ops.ed.undo_push(message="before")
    r = tear_enum(id_type=ID_OB, session_uid=ob.session_uid, data_path="rotation_mode"); yield 0.8
    check("operator runs", r == {"INTERFACE"}, r)
    yield from to_rest()
    yield from grab("m")
    b = bbox("base", "m"); log("rotation mode tear-off", b)
    yield from click(*tear_row(b, 3)); yield 0.4
    check("an item applies", ob.rotation_mode == "YXZ", ob.rotation_mode)
    yield from to_rest()
    yield from grab("clicked")
    with bpy.context.temp_override(**override()):
        bpy.ops.object.delete(use_global=False, confirm=False)
    yield 0.6
    yield from to_rest()
    yield from grab("gone")
    check("object gone", "Cube" not in bpy.data.objects)
    check("the items are gone",
          rdiff("clicked", "gone", items_box(b)) > 500,
          rdiff("clicked", "gone", items_box(b)))
    check("the header stays",
          rdiff("clicked", "gone", label_box(b)) < 100,
          rdiff("clicked", "gone", label_box(b)))
    lit, gray = brightest("clicked", first_item_box(b)), brightest("gone", first_item_box(b))
    check("the row is gray", gray < lit, (lit, gray))
    # Nothing to run here, it only must not crash.
    yield from click(*tear_row(b, 0)); yield 0.4
    bpy.ops.ed.undo_push(message="deleted")
    with bpy.context.temp_override(window=win(), screen=scr()):
        bpy.ops.ed.undo()
    yield 0.8
    yield from to_rest()
    yield from grab("undone")
    check("object back after undo", "Cube" in bpy.data.objects)
    check("the items return", rdiff("clicked", "undone", b) < 400, rdiff("clicked", "undone", b))
    yield from click(*tear_row(b, 1)); yield 0.4
    mode = bpy.data.objects["Cube"].rotation_mode
    check("an item applies after undo", mode == "XYZ", mode)


SC["enum_gone"] = s_enum_gone


def s_enum_bad():
    yield from setup(); yield from grab("base")
    cases = (
        dict(id_type=1, session_uid=1, data_path="x"),
        dict(),
        dict(id_type=ID_OB, session_uid=2147480000, data_path="rotation_mode"),
        dict(use_context=True, data_path="no.such.path"),
        dict(use_context=True, data_path="scene.frame_current"),
        dict(op_idname="SIM_OT_no_such_operator", op_propname="type"),
    )
    for kw in cases:
        r = tear_enum(**kw); yield 0.3
        check("refused: " + str(kw), r == {"CANCELLED"}, r)
    move(*center()); yield 0.3
    yield from grab("after")
    check("nothing opened", rdiff("base", "after") < 200, rdiff("base", "after"))


SC["enum_bad"] = s_enum_bad


def s_enum_py():
    yield from setup()
    sc = bpy.context.scene
    bpy.types.Scene.sim_enum = bpy.props.EnumProperty(
        name="Sim Enum", items=SIM_ENUM_ITEMS, default="A1")
    yield 0.3
    yield from open_pivot_panel()
    # Attached, for the author to compare with the tear-off below.
    px, py = panel_row(2)
    a = yield from open_dropdown(2, "attached")
    yield from type_key("ESC", px, py); yield 0.4
    cx, cy = center()
    move(cx, cy - 50); yield 0.3
    move(cx, cy - 50); yield 0.3
    yield from grab("before")
    r = tear_enum(use_context=True, data_path="scene.sim_enum"); yield 0.8
    check("operator runs", r == {"INTERFACE"}, r)
    yield from to_rest()
    yield from grab("m")
    limit = cy + 60  # Below the panel, which keeps its place at the top.
    b = view_bbox("before", "m", below=limit); log("attached", a, "torn off", b)
    check("tear-off appears", is_popup(b), b)
    # The bottom row holds the last item of each column.
    y = b[1] + MENU_BOTTOM
    yield from click(b[0] + (b[2] - b[0]) // 4, y); yield 0.4
    check("left column applies", sc.sim_enum == "A2", sc.sim_enum)
    yield from click(b[2] - (b[2] - b[0]) // 4, y); yield 0.4
    check("right column applies", sc.sim_enum == "B2", sc.sim_enum)
    yield from to_rest()
    yield from grab("clicked")
    yield from click(b[2] - 34, b[3] - 14)
    yield from to_rest()
    yield from grab("col")
    c = view_bbox("before", "col", below=limit); log("collapsed", c)
    check("pin icon collapses", c is not None and (c[3] - c[1]) < 60, c)
    yield from click(c[2] - 40, (c[1] + c[3]) // 2)
    yield from to_rest()
    yield from grab("exp")
    check("pin icon expands in place",
          rdiff("clicked", "exp", b) < 400,
          rdiff("clicked", "exp", b))
    del bpy.types.Scene.sim_enum
    sc.frame_current += 1; yield 0.6  # Any notifier not for the screen or space refreshes it.
    yield from to_rest()
    yield from grab("gone")
    g = view_bbox("before", "gone", below=limit); log("after the property went away", g)
    check("the items are gone",
          rdiff("clicked", "gone", items_box(b)) > 500,
          rdiff("clicked", "gone", items_box(b)))
    check("the header stays",
          rdiff("clicked", "gone", label_box(b)) < 100,
          rdiff("clicked", "gone", label_box(b)))
    yield from click(g[2] - 14, g[3] - 14)
    yield from to_rest()
    yield from grab("closed")
    check("X closes it", rdiff("before", "closed", g) < 50, rdiff("before", "closed", g))


SC["enum_py"] = s_enum_py


def s_enum_pref():
    yield from setup(); yield from grab("base")
    prefs = bpy.context.preferences
    check("operator polls while on", bpy.ops.wm.enum_tear_off.poll())
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from to_rest()
    yield from grab("m")
    check("tear-off appears", is_popup(bbox("base", "m")), bbox("base", "m"))
    prefs.use_tear_off = False
    yield 0.6
    move(*center()); yield 0.5
    yield from grab("off")
    check("turning it off closes it", rdiff("base", "off") < 300, rdiff("base", "off"))
    check("operator fails poll while off", not bpy.ops.wm.enum_tear_off.poll())
    prefs.use_tear_off = True
    yield 0.4
    move(*center()); yield 0.3
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from grab("again")
    check("works again after turning it back on", bbox("base", "again") is not None)


SC["enum_pref"] = s_enum_pref


def s_enum_new():
    yield from setup(cube=False); yield from grab("base")
    ob = bpy.data.objects["Camera"]
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from to_rest()
    yield from grab("m1")
    b1 = bbox("base", "m1")
    cx, cy = center()
    move(cx - 400, cy); yield 0.3
    tear_enum(id_type=ID_OB, session_uid=ob.session_uid, data_path="rotation_mode"); yield 0.8
    yield from to_rest()
    yield from grab("m2")
    b2 = bbox("m1", "m2"); log("tear-offs", b1, b2)
    yield from click(20, 987); yield 0.4
    yield from click(52, 937); yield 1.5
    yield from to_rest()
    yield from grab("after")
    check("file load closes the context tear-off",
          rdiff("base", "after", b1) < 300,
          rdiff("base", "after", b1))
    check("file load closes the ID tear-off",
          rdiff("base", "after", b2) < 300,
          rdiff("base", "after", b2))
    move(600, 600); yield 0.3
    press(600, 600); yield 0.05
    release(600, 600); yield 0.4
    yield from grab("after2")


SC["enum_new"] = s_enum_new


def s_enum_op():
    yield from setup()
    ob = bpy.data.objects["Cube"]
    ob.keyframe_insert("location", frame=1)
    first_key().select_control_point = True
    yield 0.3
    idx = yield from dopesheet_area()
    move(*center()); yield 0.3
    yield from grab("base")
    r = tear_enum(t="DOPESHEET_EDITOR", rt="WINDOW", idx=idx, op_idname="ACTION_OT_keyframe_type",
                  op_propname="type", op_context=1)  # 1 is OpCallContext::InvokeRegionWin.
    yield 0.8
    check("operator runs", r == {"INTERFACE"}, r)
    yield from to_rest()
    yield from grab("m")
    b = bbox("base", "m"); log("keyframe type tear-off", b)
    check("tear-off appears", is_popup(b), b)
    for i in (1, 3):
        was = first_key().type
        yield from click(*tear_row(b, i)); yield 0.4
        check(f"clicking row {i} sets the keyframe type",
              first_key().type != was,
              (was, first_key().type))
    main = win().workspace
    win().workspace = bpy.data.workspaces["Shading"]; yield 1.2
    win().workspace = main; yield 1.0
    was = first_key().type
    yield from click(*tear_row(b, 0)); yield 0.4
    check("clicks still apply after a workspace round trip",
          first_key().type != was,
          (was, first_key().type))
    # A Python operator goes away and comes back.
    bpy.utils.register_class(SIM_OT_enum); yield 0.3
    cx, cy = center()
    move(cx - 400, cy); yield 0.3
    yield from grab("before2")
    r = tear_enum(op_idname="SIM_OT_enum", op_propname="type", op_context=1); yield 0.8
    check("Python operator tears off", r == {"INTERFACE"}, r)
    yield from to_rest()
    yield from grab("m2")
    b2 = bbox("before2", "m2"); log("Python operator tear-off", b2)
    st = SIM_OT_enum.state
    yield from click(*tear_row(b2, 0)); yield 0.4
    check("its item runs", st["type"] == "FIRST", st)
    yield from to_rest()
    yield from grab("clicked2")
    bpy.utils.unregister_class(SIM_OT_enum); yield 0.6
    yield from to_rest()
    yield from grab("gone")
    check("gray row once unregistered",
          rdiff("clicked2", "gone", items_box(b2)) > 500,
          rdiff("clicked2", "gone", items_box(b2)))
    lit, gray = brightest("clicked2", first_item_box(b2)), brightest("gone", first_item_box(b2))
    check("the row is gray", gray < lit, (lit, gray))
    yield from click(*tear_row(b2, 0)); yield 0.4
    bpy.utils.register_class(SIM_OT_enum); yield 0.3
    bpy.context.scene.frame_current += 1; yield 0.6  # Registering sends nothing that refreshes it.
    yield from to_rest()
    yield from grab("back")
    check("items return once registered",
          rdiff("clicked2", "back", b2) < 400,
          rdiff("clicked2", "back", b2))
    yield from click(*tear_row(b2, 1)); yield 0.4
    check("its item runs again", st["type"] == "SECOND", st)


SC["enum_op"] = s_enum_op


# ---------------------------------------------------------------- Phases 5 and 6
# Not run yet, and the code they test hasn't been built. Positions come from frame diffs at run
# time and each box is logged, so the first run can calibrate these offsets (100% scale):
# - HEADER_Y and SUB_HEADER_Y: PNL_HEADER is 25 tall, these are its middle down from the panel top.
# - GRIP_X: the grip is the last 30 of a header, see drag_area_xmin in handle_panel_header.
# - TITLE_Y, X_ICON, PIN_ICON: the tear-off header. The enum scenarios use 14 down and the panel
#   scenarios 19, so this takes the middle of what both have measured.
# - TOOL_ROW0, TOOL_ROW: from VIEW3D_PT_tools_active, which draws tools at scale_y 1.75.
#
# A region and its tear-off draw the same panel, so counters that don't check
# context.region_popup would pass with no tear-off at all, see SimTearPanel in harness.py.
HEADER_Y = 12
SUB_HEADER_Y = 10
GRIP_X = 10
TITLE_Y = 17
X_ICON = 14
PIN_ICON = 34
TOOL_ROW0 = 55
TOOL_ROW = 35
T = SIM_PT_tear.state
ANCHOR = SIM_PT_tear_anchor.state


def region_box(r):
    return r.x, r.y, r.x + r.width - 1, r.y + r.height - 1


def main_box():
    return region_box(region_of(area()))


def free_box():
    """The viewport between the shelf and the sidebar. A tear-off parked here is the only thing
    that can change in it, whatever the panel's source region does when its poll changes."""
    m = main_box()
    shelf, side = region_of(area(), "TOOLS"), region_of(area(), "UI")
    return max(m[0], shelf.x + shelf.width), m[1], min(m[2], side.x - 1), m[3]


def box_bbox(n1, n2, box, thresh=0.04):
    x0, y0, x1, y1 = box
    a, b = FRAME[n1][y0:y1 + 1, x0:x1 + 1], FRAME[n2][y0:y1 + 1, x0:x1 + 1]
    d = np.abs(a - b).max(axis=2) > thresh
    if not d.any():
        return None
    ys, xs = np.where(d)
    return int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0, int(ys.max()) + y0


def torn_box(n1, n2):
    return box_bbox(n1, n2, free_box())


def real(b, h=80):
    """The box of a torn-off panel with content, not just something that changed."""
    return is_popup(b) and (b[3] - b[1]) >= h


def same_box(a, b, tol=2):
    return (a is not None and b is not None and
            all(abs(p - q) <= tol for p, q in zip(a, b)))


def area_redraw():
    for a in scr().areas:
        a.tag_redraw()


def open_tab(rt, category, *states, t="VIEW_3D"):
    """Show the panels, and make their tab the active one of the region."""
    sp = area(t).spaces.active
    if rt == "UI":
        sp.show_region_ui = True
    else:
        sp.show_region_toolbar = True
        sp.show_toolshelf_tabs = True
    for st in states:
        st["show"] = True
    area_redraw(); yield 0.6
    region_of(area(t), rt).active_panel_category = category
    area_redraw(); yield 0.6


def panel_rect(st, box, name, key="show"):
    """The panel's rect, from a frame with it and a frame without. It needs a panel above it, or
    the next one moves into its place and its top edge doesn't show."""
    yield from to_rest()
    st[key] = False; area_redraw(); yield 0.6
    yield from grab(name + "_off")
    st[key] = True; area_redraw(); yield 0.6
    yield from grab(name + "_on")
    b = box_bbox(name + "_off", name + "_on", box); log("panel rect", name, b)
    if b is None or (b[2] - b[0]) < 40 or (b[3] - b[1]) < 20:
        raise RuntimeError("no panel rect for " + name)
    return b


def sidebar_panel(st, name="rect"):
    yield from open_tab("UI", "SimTear", ANCHOR, st)
    b = yield from panel_rect(st, region_box(region_of(area(), "UI")), name)
    return b


def header_xy(b):
    return (b[0] + b[2]) // 2, b[3] - HEADER_Y


def grip_xy(b):
    return b[2] - GRIP_X, b[3] - HEADER_Y


def content_box(b):
    """The panel below its header, where a collapse shows and a pin icon doesn't."""
    return b[0] + 4, b[1] + 4, b[2] - 4, b[3] - 2 * HEADER_Y - 2


def tear_center(name, t="VIEW_3D", rt="UI", idx=0, from_region=True):
    """Tear off with the cursor at the viewport center, and park the cursor below the result."""
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override(t, rt, idx)):
        r = bpy.ops.wm.panel_tear_off(panel_idname=name, from_region_panel=from_region)
    yield 0.8
    yield from to_rest()
    return r


def close_all():
    """Turning the preference off closes every tear-off, see s_pref_off."""
    prefs = bpy.context.preferences
    prefs.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    prefs.use_tear_off = True; yield 0.4
    yield from to_rest()


def drag(x, y, dx, dy, steps=6):
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.1
    for i in range(1, steps + 1):
        move(x + dx * i // steps, y + dy * i // steps); yield 0.05
    release(x + dx, y + dy); yield 0.4


def drag_title(v, dx, dy):
    yield from drag(v[0] + 80, v[3] - TITLE_Y, dx, dy)


def shift_drag_to_free(x, y, steps=6):
    """Shift+drag from a header to the viewport, button still held. Returns the cursor position.
    The popup has to end up in free_box(), because the source region isn't in it."""
    cx, cy = center()
    tx, ty = cx, cy + 100
    yield from shift_press(x, y)
    for i in range(1, steps + 1):
        move(x + (tx - x) * i // steps, y + (ty - y) * i // steps); yield 0.08
    return tx, ty


def find_shift(n1, n2, b, lo, hi):
    """How far up the pixels of box b in frame n1 moved in frame n2: (dy, mean error)."""
    x0, y0, x1, y1 = b
    src = FRAME[n1][y0:y1, x0:x1]
    best = None
    for dy in range(lo, hi + 1):
        if y0 + dy < 0 or y1 + dy > FRAME[n2].shape[0]:
            continue
        err = float(np.abs(FRAME[n2][y0 + dy:y1 + dy, x0:x1] - src).mean())
        if best is None or err < best[1]:
            best = (dy, err)
    return best


def click_header_checkbox(v):
    """Click along the tear-off header until the checkbox flips and return that x, or None. A click
    on the title does nothing, so only a live checkbox can pass, and it's 20 wide, so steps of 8
    can't jump over it. Simulated presses can't be double-clicks, so the title won't collapse."""
    sc = bpy.context.scene
    was = sc.use_gravity
    for x in range(v[0] + 14, v[0] + 100, 8):
        yield from click(x, v[3] - TITLE_Y); yield 0.2
        if sc.use_gravity != was:
            log("checkbox at", x, "of", v)
            return x
    return None


def s_p5_c_panel():
    yield from setup()
    area().spaces.active.show_region_ui = True; yield 0.6
    yield from to_rest()
    yield from grab("base")
    refused = False
    try:
        with bpy.context.temp_override(**override("VIEW_3D", "UI")):
            bpy.ops.wm.panel_tear_off(panel_idname="SIM_PT_no_such", from_region_panel=True)
    except RuntimeError as ex:
        refused = "not found" in str(ex)
    check("an unknown panel is refused", refused)
    # Only on the region type: #WM_paneltype_find can't see it.
    r = yield from tear_center("VIEW3D_PT_transform")
    check("operator runs on a C panel", r == {"INTERFACE"}, r)
    yield from grab("m")
    b = torn_box("base", "m"); log("transform tear-off", b)
    check("a C panel tears off with its content", real(b, 100), b)


SC["p5_c_panel"] = s_p5_c_panel


def s_p5_place():
    yield from setup()
    st = SIM_PT_place.state
    bpy.context.scene.use_gravity = True
    yield from open_tab("UI", "SimTear", ANCHOR, st)
    yield from to_rest()
    yield from grab("base")
    cx, cy = center()
    r = yield from tear_center("SIM_PT_place")
    check("operator runs", r == {"INTERFACE"}, r)
    yield from grab("m")
    b = torn_box("base", "m"); log("tear-off", b, "cursor was", (cx, cy))
    check("tear-off appears", real(b, 120), b)
    # The toggle is 7 rows down, so opening under it would put the cursor far below this.
    check("the header opens under the cursor, not the toggle",
          b is not None and b[3] - 2 * TITLE_Y - 4 <= cy <= b[3],
          (cy, b))
    check("centered on the cursor", b is not None and abs((b[0] + b[2]) // 2 - cx) < 30, (cx, b))


SC["p5_place"] = s_p5_place


def s_p5_row_close():
    yield from setup()
    T["show"] = True
    yield from to_rest()
    yield from grab("base")
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override("VIEW_3D", "HEADER")):
        bpy.ops.wm.call_panel(name="SIM_PT_tear", keep_open=True)
    yield 0.8
    yield from grab("pop")
    p = box_bbox("base", "pop", free_box()); log("popover", p)
    check("the popover opens", real(p), p)
    check("a regular popover isn't a tear-off yet", T.get("popover_first") is True, T)
    T.pop("popover_first", None)
    yield from click((p[0] + p[2]) // 2, p[3] - TITLE_Y); yield 0.8
    yield from to_rest()
    yield from grab("torn")
    v = torn_box("base", "torn"); log("after the row", v)
    check("the row tears off", real(v), v)
    check("a row tear-off stays a popover to Python", T.get("popover_first") is True, T)
    yield from drag_title(v, 400, 0)
    yield from to_rest()
    yield from grab("moved")
    check("the source popover closed", rdiff("base", "moved", p) < 200, rdiff("base", "moved", p))


SC["p5_row_close"] = s_p5_row_close


def repoll_round(name):
    """A poll failing while torn off, for the panel `name`. The first line of its tear-off is the
    gray row then, and its draw must never run with what the poll guards."""
    sc = bpy.context.scene
    T["show"] = True
    T["bad_draw"] = 0
    T["draw_popup"] = 0
    yield from to_rest()
    yield from grab(name + "_base")
    r = yield from tear_center(name)
    check(name + ": operator runs", r == {"INTERFACE"}, r)
    yield from grab(name + "_live")
    v0 = torn_box(name + "_base", name + "_live"); log("live", v0)
    check(name + ": tear-off appears", is_popup(v0) and v0[3] - v0[1] >= 50, v0)
    check(name + ": it drew itself", T["draw_popup"] > 0, T)
    polled, drawn = T["poll_popup"], T["draw_popup"]
    T["show"] = False
    sc.frame_current += 1; yield 0.8
    yield from grab(name + "_gray")
    v1 = torn_box(name + "_base", name + "_gray"); log("poll failing", v1)
    check(name + ": the re-poll ran", T["poll_popup"] > polled, T)
    check(name + ": no draw with the poll failing", T["bad_draw"] == 0, T)
    check(name + ": no draw in the popup either", T["draw_popup"] == drawn, T)
    check(name + ": the box is shorter",
          v1 is not None and (v0[3] - v0[1]) - (v1[3] - v1[1]) >= ROW,
          (v0, v1))
    # Only the first row: a short popup leaves the viewport and the cube's outline below it.
    row = (v0[0] + 6, v0[3] - 65, v0[0] + 150, v0[3] - 45)
    lit, gray = brightest(name + "_live", row), brightest(name + "_gray", row)
    check(name + ": the row is gray", gray < lit, (lit, gray))
    T["show"] = True
    sc.frame_current += 1; yield 0.8
    yield from grab(name + "_back")
    v2 = torn_box(name + "_base", name + "_back"); log("poll passing again", v2)
    check(name + ": it comes back", T["draw_popup"] > drawn, T)
    check(name + ": same size as before", same_box(v0, v2), (v0, v2))
    yield from close_all()


def s_p5_repoll():
    yield from setup()
    # The round changes the frame, and the overlay text prints it, which widens the measured box.
    area().spaces.active.overlay.show_text = False
    yield from open_tab("UI", "SimTear", ANCHOR, T)
    yield from repoll_round("SIM_PT_tear")
    # It has no poll, so this also proves the parent's poll is walked.
    yield from repoll_round("SIM_PT_tear_sub")


SC["p5_repoll"] = s_p5_repoll


def space_poll_round(cls, t, prop, on, off):
    """Change only a property that the panel polls. No frame change as in repoll_round, because
    that would refresh the tear-off with or without the property's own notifier."""
    st = cls.state
    a = max((a for a in scr().areas if a.type != "VIEW_3D"), key=lambda a: a.width * a.height)
    a.type = t; yield 0.8
    idx = [x.as_pointer() for x in scr().areas if x.type == t].index(a.as_pointer())
    sp = a.spaces.active
    name = prop + "_" + off
    setattr(sp, prop, on)
    st.update(show=True, prop=prop, value=on); yield 0.6
    r = yield from tear_center(cls.bl_idname, t=t, rt="UI", idx=idx)
    check(name + ": operator runs", r == {"INTERFACE"}, r)
    check(name + ": it drew itself", st["draw_popup"] > 0, st)
    polled, drawn = st["poll_popup"], st["draw_popup"]
    setattr(sp, prop, off); yield 0.8
    check(name + ": the change re-polled the tear-off", st["poll_popup"] > polled, st)
    check(name + ": no draw with the poll failing", st["draw_popup"] == drawn, st)
    setattr(sp, prop, on); yield 0.8
    check(name + ": it comes back", st["draw_popup"] > drawn, st)
    st["show"] = False
    yield from close_all()


def s_p5_seq_view():
    yield from setup()
    # No sequence editor here, so prefetch can't send its own notifier and hide a missing one.
    yield from space_poll_round(SIM_PT_seq_poll, "SEQUENCE_EDITOR", "view_type",
                                "SEQUENCER", "PREVIEW")


SC["p5_seq_view"] = s_p5_seq_view


def s_p5_space_modes():
    yield from setup()
    yield from space_poll_round(SIM_PT_clip_poll, "CLIP_EDITOR", "mode", "TRACKING", "MASK")
    yield from space_poll_round(SIM_PT_clip_poll, "CLIP_EDITOR", "view", "CLIP", "GRAPH")
    yield from space_poll_round(SIM_PT_dope_poll, "DOPESHEET_EDITOR", "ui_mode",
                                "DOPESHEET_EDITOR", "ACTION")
    yield from space_poll_round(SIM_PT_graph_poll, "GRAPH_EDITOR", "mode", "FCURVES", "DRIVERS")


SC["p5_space_modes"] = s_p5_space_modes


def s_p5_root_flags():
    yield from setup()
    st = SIM_PT_hdr.state
    sc = bpy.context.scene
    yield from open_tab("UI", "SimTear", ANCHOR, st)
    yield from to_rest()
    yield from grab("base")
    sc.use_gravity = False; yield 0.3
    yield from tear_center("SIM_PT_hdr")
    yield from grab("off")
    v = torn_box("base", "off"); log("tear-off with draw setting enabled=False", v)
    check("tear-off appears", real(v), v)
    x = yield from click_header_checkbox(v)
    check("the header checkbox still works with the content disabled", x is not None, x)
    check("the value turned on", sc.use_gravity is True, sc.use_gravity)
    sc.use_gravity = False
    sc.frame_current += 1; yield 0.8
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    yield from to_rest()
    yield from grab("closed")
    check("the close icon still works with the content disabled",
          rdiff("base", "closed", v) < 200,
          rdiff("base", "closed", v))


SC["p5_root_flags"] = s_p5_root_flags


def s_p5_is_popover():
    yield from setup()
    yield from open_tab("UI", "SimTear", ANCHOR, T)
    r = yield from tear_center("SIM_PT_tear")
    check("region route runs", r == {"INTERFACE"}, r)
    check("region route draws in the popup", T["draw_popup"] > 0, T)
    check("region route: False on the first layout", T.get("popover_first") is False, T)
    check("region route: False on later layouts", T["popover"] is False, T)
    check("region route: False in the child", T.get("sub_popover") is False, T)
    yield from close_all()
    T.pop("popover_first", None); T["popover"] = None; T.pop("sub_popover", None)
    move(*center()); yield 0.3
    tear_panel("SIM_PT_tear"); yield 0.8
    check("row route: True on the first layout", T.get("popover_first") is True, T)
    check("row route: True on later layouts", T["popover"] is True, T)
    check("row route: True in the child", T.get("sub_popover") is True, T)


SC["p5_is_popover"] = s_p5_is_popover


def tab_round(name, st, here, other):
    """Tear off with the Properties editor on tab `here`, and watch the gray row come and go."""
    sp = area("PROPERTIES").spaces.active
    sp.context = here; yield 0.6
    st["show"] = True
    yield from to_rest()
    yield from grab(here + "_base")
    r = yield from tear_center(name, t="PROPERTIES", rt="WINDOW")
    check(here + ": operator runs", r == {"INTERFACE"}, r)
    yield from grab(here + "_live")
    v0 = torn_box(here + "_base", here + "_live"); log(here, "live", v0)
    check(here + ": no gray row on its own tab", real(v0, 100), v0)
    sp.context = other; yield 0.8
    yield from grab(here + "_other")
    v1 = torn_box(here + "_base", here + "_other"); log(other, "gray", v1)
    check(here + ": gray row on another tab",
          v1 is not None and (v0[3] - v0[1]) - (v1[3] - v1[1]) >= ROW,
          (v0, v1))
    sp.context = here; yield 0.8
    yield from grab(here + "_back")
    v2 = torn_box(here + "_base", here + "_back"); log(here, "back", v2)
    check(here + ": live again on its tab", same_box(v0, v2), (v0, v2))
    yield from close_all()


def s_p5_tool_tab():
    yield from setup()
    area("PROPERTIES").spaces.active.show_properties_tool = True; yield 0.4
    # Its space type isn't Properties, which is what made it gray on its own tab at first.
    yield from tab_round("SIM_PT_tool_tab", SIM_PT_tool_tab.state, "TOOL", "SCENE")
    yield from tab_round("SIM_PT_props", SIM_PT_props.state, "SCENE", "OUTPUT")


SC["p5_tool_tab"] = s_p5_tool_tab


def s_p5_row_context():
    yield from setup()
    st = SIM_PT_none.state
    st["show"] = True
    area("PROPERTIES").spaces.active.context = "SCENE"; yield 0.6
    yield from to_rest()
    yield from grab("base")
    # Baseline: from a region this context doesn't match the tab, so the filter does run.
    r = yield from tear_center("SIM_PT_none", t="PROPERTIES", rt="WINDOW")
    check("region route runs", r == {"INTERFACE"}, r)
    yield from grab("region")
    gray = torn_box("base", "region"); log("region route", gray)
    yield from close_all()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_none", t="PROPERTIES", rt="WINDOW"); yield 0.8
    yield from to_rest()
    yield from grab("row")
    live = torn_box("base", "row"); log("row route", live)
    check("the row route has its content", real(live, 100), live)
    check("the region route had only the gray row",
          gray is not None and (live[3] - live[1]) - (gray[3] - gray[1]) >= ROW,
          (live, gray))


SC["p5_row_context"] = s_p5_row_context


def s_p5_header():
    yield from setup()
    st = SIM_PT_hdr.state
    sc = bpy.context.scene
    sc.use_gravity = True
    yield from open_tab("UI", "SimTear", ANCHOR, st)
    yield from to_rest()
    yield from grab("base")
    yield from tear_center("SIM_PT_hdr")
    yield from grab("m")
    v = torn_box("base", "m"); log("tear-off", v)
    check("tear-off appears", real(v), v)
    check("draw_header runs in the tear-off", st["header_popup"] > 0, st)
    check("draw_header_preset runs in the tear-off", st["preset_popup"] > 0, st)
    x = yield from click_header_checkbox(v)
    check("the header checkbox works", x is not None, x)
    check("the value flipped", sc.use_gravity is False, sc.use_gravity)
    yield from to_rest()
    yield from grab("clicked")
    check("the tear-off stays open", real(torn_box("base", "clicked")),
          torn_box("base", "clicked"))
    # The checkbox is the only thing the value drives in the header.
    title = (v[0] + 4, v[3] - 2 * TITLE_Y, v[2] - 44, v[3])
    check("the checkbox redraws", rdiff("m", "clicked", title) > 10, rdiff("m", "clicked", title))


SC["p5_header"] = s_p5_header


def rmb(x, y):
    move(x, y); yield W
    move(x, y); yield W
    press(x, y, "RIGHTMOUSE"); yield 0.05
    release(x, y, "RIGHTMOUSE"); yield 0.5


# From the top of the menu. Tear-off rows have no accelerator key, see menu_block_set_keyaccels.
CTX_ROW_SEARCH = 95
CTX_ROW_NO_SEARCH = 68


def s_p5_ctx_menu():
    yield from setup()
    prefs = bpy.context.preferences
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    pin0 = T["pin"]
    yield from to_rest()
    yield from grab("before")
    # A tabbed sidebar, where the entry sits among others.
    yield from rmb(hx, hy)
    yield from grab("menu")
    d_on = box_bbox("before", "menu", main_box()); log("sidebar menu", d_on)
    check("the sidebar menu opens", is_popup(d_on), d_on)
    yield from click(hx, d_on[3] - CTX_ROW_SEARCH); yield 0.8
    check("the entry tears off", T["draw_popup"] > 0, T)
    check("the region route was used", T["popover"] is False, T)
    check("the sidebar's pin didn't change", T["pin"] == pin0, T)
    yield from to_rest()
    yield from grab("torn")
    v = box_bbox("before", "torn", main_box()); log("tear-off", v)
    yield from drag_title(v, -400, -100)
    yield from to_rest()
    yield from grab("moved")
    check("the tear-off moved off the source", real(torn_box("before", "moved")),
          torn_box("before", "moved"))
    check("the source panel didn't change", rdiff("before", "moved", b) < 100,
          rdiff("before", "moved", b))
    yield from close_all()
    # A subpanel and Properties don't have the sidebar items, so it's the menu's one entry.
    S2 = SIM_PT_tear_sub2.state
    s = yield from panel_rect(S2, region_box(region_of(area(), "UI")), "sub2")
    yield from to_rest()
    yield from grab("before_sub")
    yield from rmb((s[0] + s[2]) // 2, s[3] - SUB_HEADER_Y)
    yield from grab("menu_sub")
    d = box_bbox("before_sub", "menu_sub", main_box()); log("subpanel menu", d)
    check("the subpanel menu opens", is_popup(d), d)
    # A menu with one row opens with that row under the cursor.
    yield from click((s[0] + s[2]) // 2, s[3] - SUB_HEADER_Y); yield 0.8
    check("the subpanel entry tears off", S2["draw_popup"] > 0, S2)
    yield from close_all()
    P = SIM_PT_props.state
    area("PROPERTIES").spaces.active.context = "SCENE"; yield 0.6
    P["show"] = True
    pb = yield from panel_rect(P, region_box(region_of(area("PROPERTIES"))), "props")
    yield from to_rest()
    yield from grab("before_props")
    px, py = header_xy(pb)
    yield from rmb(px, py)
    yield from grab("menu_props")
    d = box_bbox("before_props", "menu_props", region_box(region_of(area("PROPERTIES"))))
    log("Properties menu", d)
    check("the Properties menu opens", d is not None and d[3] - d[1] > 30, d)
    yield from click(px, py); yield 0.8
    check("the Properties entry tears off", P["draw_popup"] > 0, P)
    yield from close_all()
    # Preference off: the menu is shorter by the entry, and its key does nothing.
    drawn = T["draw_popup"]
    prefs.use_tear_off = False; yield 0.6
    yield from to_rest()
    yield from grab("before_off")
    yield from rmb(hx, hy)
    yield from grab("menu_off")
    d_off = box_bbox("before_off", "menu_off", main_box()); log("sidebar menu, off", d_off)
    check("the menu has no entry while off",
          d_off is not None and (d_on[3] - d_on[1]) - (d_off[3] - d_off[1]) >= ROW,
          (d_on, d_off))
    yield from type_key("ESC", hx, hy); yield 0.5
    check("nothing tore off while off", T["draw_popup"] == drawn, T)


SC["p5_ctx_menu"] = s_p5_ctx_menu


def s_p5_shift_click():
    yield from setup()
    # A tabbed region pins.
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    check("starts unpinned", T["pin"] is False, T)
    yield from to_rest()
    yield from grab("before")
    yield from shift_press(hx, hy)
    check("nothing happens on the press itself", T["pin"] is False, T)
    yield from shift_release(hx, hy); yield 0.5
    check("Shift+click pins", T["pin"] is True, T)
    check("Shift+click opens no tear-off", T["draw_popup"] == 0, T)
    yield from to_rest()
    yield from grab("pinned")
    box = content_box(b)
    check("Shift+click doesn't collapse in a tabbed region", rdiff("before", "pinned", box) < 100,
          rdiff("before", "pinned", box))
    # A handler left waiting for a release would swallow this.
    yield from click(hx, hy); yield 0.6
    yield from to_rest()
    yield from grab("closed")
    check("a plain click then collapses", rdiff("before", "closed", box) > 100,
          rdiff("before", "closed", box))
    yield from click(hx, hy); yield 0.6
    yield from to_rest()
    yield from grab("open")
    check("a plain click then expands", rdiff("before", "open", box) < 100,
          rdiff("before", "open", box))
    # A region without tabs does a plain click.
    P = SIM_PT_props.state
    area("PROPERTIES").spaces.active.context = "SCENE"; yield 0.6
    P["show"] = True
    pb = yield from panel_rect(P, region_box(region_of(area("PROPERTIES"))), "props")
    px, py = header_xy(pb)
    box = content_box(pb)
    yield from to_rest()
    yield from grab("p_before")
    yield from shift_press(px, py)
    yield from shift_release(px, py); yield 0.6
    yield from to_rest()
    yield from grab("p_closed")
    check("Shift+click collapses in Properties", rdiff("p_before", "p_closed", box) > 100,
          rdiff("p_before", "p_closed", box))
    check("no tear-off in Properties", P["draw_popup"] == 0, P)
    yield from click(px, py); yield 0.6
    yield from to_rest()
    yield from grab("p_open")
    check("a plain click then expands in Properties", rdiff("p_before", "p_open", box) < 100,
          rdiff("p_before", "p_open", box))


SC["p5_shift_click"] = s_p5_shift_click


def s_p5_plain_drag():
    yield from setup()
    b = yield from sidebar_panel(T)
    gx, gy = grip_xy(b)
    yield from to_rest()
    yield from grab("before")
    # Up past the anchor, so the panel has to end above it with its content whole.
    yield from drag(gx, gy, 0, 110, steps=10); yield 0.8
    check("a plain drag opens no tear-off", T["draw_popup"] == 0, T)
    yield from to_rest()
    yield from grab("after")
    s = find_shift("before", "after", b, 0, 150); log("panel moved by", s)
    check("the panel moved up and kept its content",
          s is not None and s[0] >= 20 and s[1] < 0.03,
          s)


SC["p5_plain_drag"] = s_p5_plain_drag


def s_p5_threshold():
    yield from setup()
    prefs = bpy.context.preferences
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    t = int(prefs.inputs.drag_threshold_mouse * prefs.system.ui_scale); log("threshold", t)
    # The keyboard threshold is 30 by default. Well under it, this fails if that one is back.
    check("the mouse threshold is the small one", 0 < t < 20, t)
    yield from shift_press(hx, hy)
    yield from grab("pressed")
    move(hx - t, hy); yield 0.3
    yield from grab("at")
    check("exactly at the threshold, nothing", T["draw_popup"] == 0, T)
    check("exactly at the threshold, same frame", rdiff("pressed", "at", main_box()) < 100,
          rdiff("pressed", "at", main_box()))
    move(hx - t - 1, hy); yield 0.5
    yield from grab("past")
    check("one pixel past it tears off", T["draw_popup"] > 0, T)
    p = box_bbox("pressed", "past", main_box()); log("tear-off", p)
    check("the tear-off shows", real(p), p)
    yield from shift_release(hx - t - 1, hy)


SC["p5_threshold"] = s_p5_threshold


def s_p5_grab():
    yield from setup()
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    yield from to_rest()
    yield from grab("before")
    tx, ty = yield from shift_drag_to_free(hx, hy)
    yield from grab("held")
    v1 = torn_box("before", "held"); log("held", v1)
    check("Shift+drag tears off a region panel", real(v1), v1)
    check("the tear-off is the region route", T["popover"] is False, T)
    # The first refresh runs during this, and the grab must survive it.
    dx, dy = -120, -60
    for i in range(1, 5):
        move(tx + dx * i // 4, ty + dy * i // 4); yield 0.1
    yield from grab("held2")
    v2 = torn_box("before", "held2"); log("held further", v2)
    moved = v1 is not None and v2 is not None and (v2[0] - v1[0], v2[1] - v1[1])
    check("it follows the cursor by the same delta",
          moved and abs(moved[0] - dx) <= 2 and abs(moved[1] - dy) <= 2,
          (moved, (dx, dy)))
    check("same size while it follows",
          moved and abs((v2[2] - v2[0]) - (v1[2] - v1[0])) <= 2 and
          abs((v2[3] - v2[1]) - (v1[3] - v1[1])) <= 2,
          (v1, v2))
    yield from shift_release(tx + dx, ty + dy)
    move(tx + dx - 90, ty + dy - 40); yield 0.4
    yield from grab("released")
    v3 = torn_box("before", "released"); log("released", v3)
    check("it stops at the release and stays open", same_box(v2, v3), (v2, v3))
    yield from to_rest()
    yield from grab("rest")
    check("the source panel is untouched, so is its order", rdiff("before", "rest", b) < 100,
          rdiff("before", "rest", b))


SC["p5_grab"] = s_p5_grab


def s_p5_once():
    yield from setup()
    st = SIM_PT_once.state
    sc = bpy.context.scene
    was = sc.use_gravity
    yield from open_tab("UI", "SimTear", ANCHOR, st)
    b = yield from panel_rect(st, region_box(region_of(area(), "UI")), "rect")
    yield from to_rest()
    yield from grab("before")
    # The checkbox label covers the header up to the grip, and takes the press. Use the arrow.
    gx, gy = b[0] + 13, b[3] - HEADER_Y
    tx, ty = yield from shift_drag_to_free(gx, gy)
    yield from grab("held")
    v1 = torn_box("before", "held"); log("held", v1)
    check("tear-off appears", real(v1), v1)
    yield from shift_release(tx, ty); yield 0.4
    yield from grab("released")
    v2 = torn_box("before", "released"); log("released", v2)
    check("the release leaves it open", same_box(v1, v2), (v1, v2))
    check("the release doesn't press the checkbox", sc.use_gravity == was, sc.use_gravity)
    yield from click(tx, ty); yield 0.3
    check("that release really was over the checkbox", sc.use_gravity != was, sc.use_gravity)


SC["p5_once"] = s_p5_once


def s_p5_esc():
    yield from setup()
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    box = content_box(b)
    yield from to_rest()
    yield from grab("before")
    yield from shift_press(hx, hy)
    key("ESC", hx, hy); yield 0.05
    key("ESC", hx, hy, None, "RELEASE"); yield 0.2
    move(hx - 60, hy - 40); yield 0.4
    check("no tear-off after Esc", T["draw_popup"] == 0, T)
    yield from shift_release(hx - 60, hy - 40)
    check("Esc leaves the pin alone", T["pin"] is False, T)
    yield from to_rest()
    yield from grab("after")
    check("Esc leaves the panel alone", rdiff("before", "after", b) < 100,
          rdiff("before", "after", b))
    yield from click(hx, hy); yield 0.6
    yield from to_rest()
    yield from grab("closed")
    check("a plain click works after Esc", rdiff("before", "closed", box) > 100,
          rdiff("before", "closed", box))


SC["p5_esc"] = s_p5_esc


def s_p5_region_gone():
    yield from setup()
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    yield from shift_press(hx, hy)
    area().type = "CONSOLE"; yield 0.8
    move(hx - 60, hy - 40); yield 0.3
    move(hx - 90, hy - 40); yield 0.3
    check("no tear-off once the region is gone", T["draw_popup"] == 0, T)
    yield from shift_release(hx - 90, hy - 40)
    [a for a in scr().areas if a.type == "CONSOLE"][0].type = "VIEW_3D"; yield 0.8
    # The handler is gone and nothing else broke: the gesture works from scratch.
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    yield from to_rest()
    yield from grab("before")
    tx, ty = yield from shift_drag_to_free(hx, hy)
    yield from shift_release(tx, ty); yield 0.4
    yield from grab("again")
    v = torn_box("before", "again"); log("after the round trip", v)
    check("the gesture works again", real(v) and T["draw_popup"] > 0, (v, T))


SC["p5_region_gone"] = s_p5_region_gone


def finish_with_memory_report():
    """harness.py ends with os._exit, which skips the exit report and loses what a release build
    still has buffered for stdout, so a memory check has to quit for real. run.sh then prints the
    lines to compare, since Python can't read them back. Needs --debug-memory, as in run.sh."""
    log("DONE", "ALLPASS" if all(r[1] for r in results) else "SOMEFAIL",
        f"{sum(r[1] for r in results)}/{len(results)}")
    bpy.ops.wm.memory_statistics()
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.quit_blender()
    yield 30


def wait_for_previews(seconds=8.0):
    """Until the preview jobs are done, and return whether one ran."""
    ran = False
    for _ in range(int(seconds / 0.25)):
        running = bpy.app.is_job_running("RENDER_PREVIEW")
        ran = ran or running
        if ran and not running:
            break
        yield 0.25
    return ran


def s_p5_preview_close():
    """Every popup with a preview is a new owner of a Render. The count of `new render` in the
    lines run.sh prints must stay the same, because rounds 2 to 4 only repeat round 1. The exit
    report can't show this: RE_FreeAllRender empties the list before it runs. Each round waits for
    the jobs, because one running at close keeps the Render on purpose."""
    yield from setup()
    bpy.context.view_layer.objects.active.data.materials.append(
        bpy.data.materials.new("SimPreview"))
    area("PROPERTIES").spaces.active.context = "MATERIAL"; yield 0.8
    yield from to_rest()
    yield from grab("base")
    for i in range(4):
        r = yield from tear_center("MATERIAL_PT_preview", t="PROPERTIES", rt="WINDOW")
        check(f"round {i}: operator runs", r == {"INTERFACE"}, r)
        yield from wait_for_previews()
        yield 2.0
        yield from to_rest()
        yield from grab(f"round{i}")
        v = torn_box("base", f"round{i}"); log("tear-off", v)
        # The job can finish between two polls, so look at the picture: a sphere on checkers.
        spread = (float(np.std(FRAME[f"round{i}"][v[1] + 30:v[3] - 50, v[0] + 20:v[2] - 60]))
                  if real(v, 150) else 0.0)
        check(f"round {i}: the preview rendered", spread > 0.1, spread)
        yield from close_all()
        if i == 0:
            bpy.ops.wm.memory_statistics()
    yield from finish_with_memory_report()


SC["p5_preview_close"] = s_p5_preview_close


def s_p5_workspace_gone():
    """As p5_region_gone, but a screen change drops handlers by area before any region exits, and
    that path has to free the gesture too. run.sh must print no panel_tear_off_gesture_begin line.
    """
    yield from setup()
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    yield from shift_press(hx, hy)
    main = win().workspace
    win().workspace = bpy.data.workspaces["Shading"]; yield 1.2
    move(hx - 60, hy - 40); yield 0.3
    move(hx - 90, hy - 40); yield 0.3
    check("no tear-off after the screen changed", T["draw_popup"] == 0, T)
    yield from shift_release(hx - 90, hy - 40)
    win().workspace = main; yield 1.0
    # The handler is gone and nothing else broke: the gesture works from scratch.
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    yield from to_rest()
    yield from grab("before")
    tx, ty = yield from shift_drag_to_free(hx, hy)
    yield from shift_release(tx, ty); yield 0.4
    yield from grab("again")
    v = torn_box("before", "again"); log("after the round trip", v)
    check("the gesture works again", real(v) and T["draw_popup"] > 0, (v, T))
    yield from close_all()
    yield from finish_with_memory_report()


SC["p5_workspace_gone"] = s_p5_workspace_gone


def s_p5_pref_off():
    yield from setup()
    prefs = bpy.context.preferences
    P = SIM_PT_props.state
    area("PROPERTIES").spaces.active.context = "SCENE"; yield 0.6
    P["show"] = True
    rbox = region_box(region_of(area("PROPERTIES")))
    pb = yield from panel_rect(P, rbox, "props")
    gx, gy = grip_xy(pb)
    # Baseline: on the grip of a region without tabs, this same gesture tears off while on.
    yield from shift_press(gx, gy)
    for i in range(1, 7):
        move(gx - 20 * i, gy + 10 * i); yield 0.08
    yield 0.4
    check("while on, the gesture tears off", P["draw_popup"] > 0, P)
    yield from shift_release(gx - 120, gy + 60)
    yield from close_all()
    drawn = P["draw_popup"]
    prefs.use_tear_off = False; yield 0.6
    check("the operator fails its poll while off", not bpy.ops.wm.panel_tear_off.poll())
    yield from to_rest()
    yield from grab("before")
    yield from shift_press(gx, gy)
    for i in range(1, 7):
        move(gx, gy + 10 * i); yield 0.08
    yield from grab("dragging")
    check("while off, no tear-off", P["draw_popup"] == drawn, P)
    check("while off, the grip reorders as it always did", rdiff("before", "dragging", rbox) > 200,
          rdiff("before", "dragging", rbox))
    yield from shift_release(gx, gy + 60); yield 0.6
    # A tabbed region pins right on the press, with nothing waiting for a release.
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    yield from shift_press(hx, hy); yield 0.4
    check("while off, a tabbed region pins on the press", T["pin"] is True, T)
    move(hx - 60, hy - 40); yield 0.4
    check("while off, moving tears nothing off", T["draw_popup"] == 0, T)
    yield from shift_release(hx - 60, hy - 40)
    prefs.use_tear_off = True; yield 0.4
    yield from shift_press(hx, hy)
    for i in range(1, 7):
        move(hx - 20 * i, hy - 10 * i); yield 0.08
    yield 0.4
    check("works again once back on", T["draw_popup"] > 0, T)
    yield from shift_release(hx - 120, hy - 60)


SC["p5_pref_off"] = s_p5_pref_off


def s_p5_lifecycle():
    yield from setup()
    ob = bpy.context.view_layer.objects.active
    b = yield from sidebar_panel(T)
    hx, hy = header_xy(b)
    yield from to_rest()
    yield from grab("base")
    tx, ty = yield from shift_drag_to_free(hx, hy)
    yield from shift_release(tx, ty); yield 0.3
    yield from to_rest()
    yield from grab("m")
    v = torn_box("base", "m"); log("gesture tear-off", v)
    check("tear-off appears", real(v), v)
    label = (v[0] + 20, v[3] - 2 * TITLE_Y, v[0] + 120, v[3] - 4)
    # Pin.
    yield from click(v[2] - PIN_ICON, v[3] - TITLE_Y)
    yield from to_rest()
    yield from grab("col")
    c = torn_box("base", "col"); log("collapsed", c)
    check("pin icon collapses", c is not None and (c[3] - c[1]) < 60, c)
    yield from click(c[2] - 40, (c[1] + c[3]) // 2)
    yield from to_rest()
    yield from grab("exp")
    check("pin icon expands in place", rdiff("m", "exp", v) < 400, rdiff("m", "exp", v))
    # Workspace.
    main = win().workspace
    win().workspace = bpy.data.workspaces["Shading"]; yield 1.2
    win().workspace = main; yield 1.0
    yield from to_rest()
    yield from grab("ws")
    check("back after a workspace round trip", rdiff("m", "ws", label) < 200,
          rdiff("m", "ws", label))
    # Mode.
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="EDIT")
    yield 0.8
    yield from to_rest()
    yield from grab("edit")
    check("hidden in another mode", ob.mode == "EDIT" and rdiff("m", "edit", label) > 50,
          (ob.mode, rdiff("m", "edit", label)))
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="OBJECT")
    yield 0.8
    yield from to_rest()
    yield from grab("obj")
    check("back in its mode", rdiff("m", "obj", label) < 200, rdiff("m", "obj", label))
    # Editor type.
    area().type = "CONSOLE"; yield 0.8
    [a for a in scr().areas if a.type == "CONSOLE"][0].type = "VIEW_3D"; yield 0.8
    yield from to_rest()
    yield from grab("type")
    check("back after an editor round trip", rdiff("m", "type", label) < 200,
          rdiff("m", "type", label))
    # Close.
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    yield from to_rest()
    yield from grab("closed")
    check("X closes it", rdiff("base", "closed", v) < 200, rdiff("base", "closed", v))


SC["p5_lifecycle"] = s_p5_lifecycle


def shelf():
    return region_of(area(), "TOOLS")


def shelf_resize(target, category="SimTear"):
    """Drag the real shelf's edge, and return its width. The zone is around the edge, see
    region_azone_edge, and inside it comes first, because a miss outside presses the viewport."""
    r = shelf()
    # Beside the top panels, because a region that overlaps has its edge zone only next to them.
    w0, y = r.width, r.y + r.height - 60
    for off in (-1, 1):
        x = r.x + w0 + off
        yield from drag(x, y, target - w0, 0, steps=8); yield 0.4
        if shelf().width != w0:
            break
    area_redraw(); yield 0.4
    # A miss inside can land on a tab.
    shelf().active_panel_category = category
    area_redraw(); yield 0.6
    log("shelf width", w0, "->", shelf().width, "asked for", target)
    return shelf().width


def s_p6_columns():
    yield from setup()
    # The shelf resizes, and the overlay text moves with it, which widens the measured box.
    area().spaces.active.overlay.show_text = False
    sc = bpy.context.scene
    C = SIM_PT_cols.state
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    # Baseline: the shelf can be resized at all, and the region's own count follows it.
    w = yield from shelf_resize(170)
    check("the shelf resizes", abs(w - 170) < 50, w)
    region_count = C["region"].get("count"); log("region", C["region"])
    check("the region drew its panel", region_count is not None, C["region"])

    # All routes. A wrong region here gives width 0, and nothing else shows it.
    def route_checks(route):
        rec = C["popup"]
        check(route + ": drew in the popup", rec.get("draws", 0) > 0, rec)
        check(route + ": has a shelf width", rec.get("width", 0) > 0, rec)
        check(route + ": same count as the shelf", rec.get("count") == C["region"]["count"],
              (rec, C["region"]))
        check(route + ": same as measuring the region",
              rec.get("count") == rec.get("region_count"),
              rec)
    C["popup"].clear()
    r = yield from tear_center("SIM_PT_cols", rt="TOOLS")
    check("operator route runs", r == {"INTERFACE"}, r)
    route_checks("operator")
    yield from close_all()
    b = yield from panel_rect(C, region_box(shelf()), "cols")
    hx, hy = header_xy(b)
    C["popup"].clear()
    yield from to_rest()
    yield from grab("before_ctx")
    yield from rmb(hx, hy)
    yield from grab("ctx")
    d = box_bbox("before_ctx", "ctx", main_box()); log("shelf menu", d)
    yield from click(hx, d[3] - CTX_ROW_NO_SEARCH); yield 0.8
    route_checks("context menu")
    yield from close_all()
    C["popup"].clear()
    yield from to_rest()
    yield from grab("before")
    tx, ty = yield from shift_drag_to_free(hx, hy)
    yield 0.4
    route_checks("Shift+drag")
    yield from shift_release(tx, ty); yield 0.3

    # The real shelf changes, the tear-off doesn't.
    yield from to_rest()
    yield from grab("m")
    v = torn_box("before", "m"); log("gesture tear-off", v)
    check("tear-off appears", is_popup(v) or (v is not None and v[3] - v[1] > 40), v)
    width0, count0, draws0 = C["popup"]["width"], C["popup"]["count"], C["popup"]["draws"]
    w2 = yield from shelf_resize(280)
    sc.frame_current += 1; yield 0.8
    check("the shelf count changed", C["region"]["count"] != count0, C["region"])
    check("the tear-off redrew after that", C["popup"]["draws"] > draws0, C["popup"])
    check("the tear-off keeps its width", C["popup"]["width"] == width0, C["popup"])
    check("the tear-off keeps its count", C["popup"]["count"] == count0, C["popup"])
    check("measuring the region would have changed it", C["popup"]["region_count"] != count0,
          C["popup"])
    yield from to_rest()
    yield from grab("resized")
    # Right of the wider shelf and of the stats text that moves with it.
    mid = (420, main_box()[1], region_of(area(), "UI").x - 1, main_box()[3])
    v2 = box_bbox("before", "resized", mid); log("tear-off after the resize", v2, "shelf", w2)
    check("the box keeps its width", v2 is not None and abs((v2[2] - v2[0]) - (v[2] - v[0])) <= 2,
          (v, v2))
    # Collapse and expand keep it too.
    yield from click(v[2] - PIN_ICON, v[3] - TITLE_Y)
    yield from to_rest()
    yield from grab("col")
    c = box_bbox("before", "col", mid); log("collapsed", c)
    check("pin icon collapses", c is not None and (c[3] - c[1]) < 60, c)
    yield from click(c[2] - 40, (c[1] + c[3]) // 2)
    yield from to_rest()
    yield from grab("exp")
    v3 = box_bbox("before", "exp", mid); log("expanded", v3)
    check("collapse and expand keep the box width",
          v3 is not None and abs((v3[2] - v3[0]) - (v[2] - v[0])) <= 2,
          (v, v3))
    check("collapse and expand keep the width", C["popup"]["width"] == width0, C["popup"])
    yield from close_all()

    # Each count the shelf has. Its width snaps, so log what each drag reached.
    seen = {}
    for target in (70, 140, 180, 280):
        w = yield from shelf_resize(target)
        yield from to_rest()
        yield from grab("wb")
        C["popup"].clear()
        yield from tear_center("SIM_PT_cols", rt="TOOLS")
        yield from grab("wm")
        vw = torn_box("wb", "wm")
        rc = C["region"]["count"]
        log("target", target, "width", w, "region", C["region"], "popup", C["popup"], "box", vw)
        check(f"at {target}: same count", C["popup"].get("count") == rc, (C["popup"], rc))
        seen[rc] = vw[2] - vw[0] if vw else None
        yield from close_all()
    check("every count was reached", sorted(seen) == [1, 2, 3, 4], seen)
    widths = [seen[k] for k in sorted(seen) if seen[k] is not None]
    check("more columns, a wider box", widths == sorted(widths) and widths[0] < widths[-1], seen)

    # Everything that isn't a shelf: 0, and it did draw, so a stale 0 can't pass.
    U = SIM_PT_ui_cols.state
    yield from open_tab("UI", "SimTear", ANCHOR, U)
    yield from tear_center("SIM_PT_ui_cols")
    check("a sidebar panel has no shelf width",
          U["popup"].get("draws", 0) > 0 and U["popup"].get("width") == 0, U["popup"])
    yield from close_all()
    U["popup"].clear()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_ui_cols"); yield 0.8
    check("a row tear-off has no shelf width",
          U["popup"].get("draws", 0) > 0 and U["popup"].get("width") == 0, U["popup"])
    yield from close_all()
    CL = SIM_PT_clip_cols.state
    a = max((a for a in scr().areas if a.type != "VIEW_3D"), key=lambda a: a.width * a.height)
    a.type = "CLIP_EDITOR"; yield 0.8
    CL["show"] = True
    a.spaces.active.show_region_toolbar = True; yield 0.6
    yield from tear_center("SIM_PT_clip_cols", t="CLIP_EDITOR", rt="TOOLS")
    check("a Clip Editor tool panel has no shelf width",
          CL["popup"].get("draws", 0) > 0 and CL["popup"].get("width") == 0, CL["popup"])
    yield from close_all()

    # One add-on from the call sites, through its own copy of the function.
    bpy.ops.preferences.addon_enable(module="bfa_power_user_tools"); yield 0.6
    import bfa_power_user_tools.toolshelf as addon_shelf
    bpy.context.window_manager.BFA_UI_addon_props.BFA_PROP_toggle_insertframes = True
    calls = []
    orig = addon_shelf.toolsystem_column_count

    def spy(region, layout=None):
        calls.append(None if layout is None else layout.tear_off_width)
        return orig(region, layout)
    addon_shelf.toolsystem_column_count = spy
    r = yield from tear_center("BFA_PT_toolshelf_frames", rt="TOOLS")
    addon_shelf.toolsystem_column_count = orig
    log("add-on calls", calls[:6])
    check("the add-on panel tears off", r == {"INTERFACE"}, r)
    check("the add-on passes its layout and sees the width",
          any(c and c > 0 for c in calls),
          calls[:6])


SC["p6_columns"] = s_p6_columns


def s_p6_tools():
    yield from setup()
    C = SIM_PT_cols.state
    wm_tools = win().workspace.tools
    ob = bpy.context.view_layer.objects.active
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    yield 0.4
    check("in Object mode", ob.mode == "OBJECT", ob.mode)
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    # Parked outside the popup, because a change in what's hovered could fake a refresh.
    yield from tear_center("SIM_PT_cols", rt="TOOLS")
    check("the tear-off has a shelf width", C["popup"].get("width", 0) > 0, C["popup"])
    check("it sees the first tool", C["popup"].get("tool") == "builtin.select_box", C["popup"])
    # Object mode, so only the message bus can refresh it. A brush tool also sends a notifier.
    draws = C["popup"]["draws"]
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    yield 0.8
    check("a tool change rebuilds the tear-off", C["popup"]["draws"] > draws, C["popup"])
    check("it sees the new tool", C["popup"].get("tool") == "builtin.move", C["popup"])
    yield from close_all()
    # The real tool panel, torn off: a click in it sets a tool.
    shelf().active_panel_category = "Tools"; area_redraw(); yield 0.6
    yield from grab("base")
    r = yield from tear_center("VIEW3D_PT_tools_active", rt="TOOLS")
    check("the tool panel tears off", r == {"INTERFACE"}, r)
    yield from grab("m")
    v = torn_box("base", "m"); log("tool panel tear-off", v)
    check("it has tools in it", real(v), v)
    # Back to the first tool, because the row below could be the one the last step set.
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    yield 0.6
    yield from grab("m")
    was = wm_tools.from_space_view3d_mode("OBJECT", create=False).idname
    yield from click(v[0] + 30, v[3] - TOOL_ROW0 - TOOL_ROW * 3); yield 0.6
    now = wm_tools.from_space_view3d_mode("OBJECT", create=False).idname
    log("tool", was, "->", now)
    check("clicking a tool in the tear-off sets it", now != was, (was, now))
    yield from to_rest()
    yield from grab("clicked")
    check("its highlight follows", rdiff("m", "clicked", v) > 50, rdiff("m", "clicked", v))


SC["p6_tools"] = s_p6_tools


def median_color(name, box):
    x0, y0, x1, y1 = box
    return np.median(FRAME[name][y0:y1, x0:x1].reshape(-1, 3), axis=0)


def near(color, want, tol):
    return all(abs(float(c) - float(w)) <= tol for c, w in zip(color, want))


def count_color(name, box, channel, other, margin=0.4):
    """Pixels in box where one channel beats another by a wide margin: text of a set color."""
    x0, y0, x1, y1 = box
    f = FRAME[name][y0:y1, x0:x1]
    return int(((f[:, :, channel] - f[:, :, other]) > margin).sum())


def s_p6_look():
    yield from setup()
    th = bpy.context.preferences.themes[0]
    C = SIM_PT_cols.state
    # Colors no default uses, so each style can only show its own. Regular labels take panel_text
    # and popup labels take wcol_menu_back.text, see draw_button and widget_state_label.
    th.user_interface.panel_text = (1.0, 0.0, 0.0)
    th.user_interface.wcol_menu_back.text = (0.0, 1.0, 0.0)
    th.regions.sidebars.back = (0.8, 0.8, 0.8, th.regions.sidebars.back[3])
    yield 0.5
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    yield from open_tab("UI", "SimTear", ANCHOR, T)
    yield from to_rest()
    yield from grab("base")
    # The shelf panel.
    yield from tear_center("SIM_PT_cols", rt="TOOLS")
    check("the shelf tear-off has a shelf width", C["popup"].get("width", 0) > 0, C["popup"])
    yield from grab("shelf")
    v = torn_box("base", "shelf"); log("shelf tear-off", v)
    check("the shelf tear-off appears", is_popup(v) or (v is not None and v[3] - v[1] > 40), v)
    inner = (v[0] + 8, v[1] + 8, v[2] - 8, v[3] - 8)
    col = median_color("shelf", inner); log("shelf tear-off color", col)
    check("the shelf tear-off has the shelf's color",
          near(col, th.regions.sidebars.back[:3], 0.05), col)
    check("its labels have the regular style, red", count_color("shelf", inner, 0, 1) > 10,
          count_color("shelf", inner, 0, 1))
    check("and not the popup style, green", count_color("shelf", inner, 1, 0) == 0,
          count_color("shelf", inner, 1, 0))
    yield from close_all()
    # A panel from elsewhere, the baseline that shows these checks can fail.
    yield from tear_center("SIM_PT_tear")
    yield from grab("other")
    v = torn_box("base", "other"); log("other tear-off", v)
    check("the other tear-off appears", real(v), v)
    inner = (v[0] + 8, v[1] + 8, v[2] - 8, v[3] - 8)
    col = median_color("other", inner); log("other tear-off color", col)
    check("the other tear-off keeps the popup color",
          near(col, th.user_interface.wcol_menu_back.inner[:3], 0.1)
          and not near(col, th.regions.sidebars.back[:3], 0.1), col)
    check("its labels have the popup style, green", count_color("other", inner, 1, 0) > 10,
          count_color("other", inner, 1, 0))
    check("and not the regular style, red", count_color("other", inner, 0, 1) == 0,
          count_color("other", inner, 0, 1))


SC["p6_look"] = s_p6_look
