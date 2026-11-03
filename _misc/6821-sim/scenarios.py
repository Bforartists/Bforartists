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
    # This menu has no title, and its length depends on the color config, so measure from its top.
    mx, my = panel_row(1)
    y = my - 12 - (TEAR_ROW0 - ROW - LINE); log("menu row click", (mx, y))
    yield from click(mx, y); yield 0.6
    yield from to_rest()
    yield from grab("after3")
    check("the menu's row leaves the value alone", settings.name == "Non-Color", settings.name)
    nb = view_bbox("b2_po", "after3", skip=PANEL["box"]); log("new popup from the menu", nb)
    check("the menu's row opens a tear-off", nb is not None, nb)


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
