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


def open_panel(base="base"):
    """Tear off the test panel, and record geometry from the screenshot diff."""
    yield from grab(base + "_p")
    tear_panel("SIM_PT_field"); yield 0.8
    yield from grab(base + "_po")
    d = np.abs(FRAME[base + "_p"] - FRAME[base + "_po"]).max(axis=2) > 0.04
    d[:VIEW[1], :] = False; d[VIEW[3]:, :] = False; d[:, :VIEW[0]] = False; d[:, VIEW[2]:] = False
    ys, xs = np.where(d)
    b = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    log("panel bbox", b)
    xmin, ymin, xmax, ymax = b
    PANEL.update(xmin=xmin, ymax=ymax, name=(xmin + 110, ymax - 55), frame=(xmin + 110, ymax - 80),
                 arrow=(xmin + 201, ymax - 80), x=(xmin + 200, ymax - 19), title=(xmin + 80, ymax - 19))


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
