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
    # Inside the fitted menu: the viewport beside it changes with the scale.
    box = (525, 650, 695, 735)
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
    clear_stored()
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
    # A fitted menu can be narrower than this, and the viewport beside it isn't part of the item.
    return b[0] + 6, b[3] - 50, min(b[0] + 150, b[2] - 6), b[3] - 32


def label_box(b):
    """The left of the header row. The icons can move, because the width follows the content, and
    on a fitted menu they start 60 to 100 in."""
    return b[0], b[3] - 24, b[0] + 60, b[3]


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
    clear_stored()
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
    clear_stored()
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
    # Load UI is off in factory settings, so File > New keeps the workspaces, and their pins.
    check("file new keeps the context tear-off",
          rdiff("m2", "after", b1) < 300,
          rdiff("m2", "after", b1))
    # The new file has a Cube too, and an enum finds its ID by name.
    check("file new keeps the ID tear-off, on the object of that name",
          rdiff("m2", "after", b2) < 300,
          rdiff("m2", "after", b2))
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


def clear_stored():
    """Turning the preference off keeps pins on the list, to come back. For a scenario that uses
    off and on to clear the screen."""
    for ws in bpy.data.workspaces:
        group = ws.bl_system_properties_get(do_create=False)
        if group is not None and "bfa_tear_offs" in group:
            del group["bfa_tear_offs"]


def close_all():
    """Turning the preference off closes every tear-off, see s_pref_off."""
    prefs = bpy.context.preferences
    prefs.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    clear_stored()
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
    clear_stored()
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
    # A panel from elsewhere looks the same.
    yield from tear_center("SIM_PT_tear")
    yield from grab("other")
    v = torn_box("base", "other"); log("other tear-off", v)
    check("the other tear-off appears", real(v), v)
    inner = (v[0] + 8, v[1] + 8, v[2] - 8, v[3] - 8)
    col = median_color("other", inner); log("other tear-off color", col)
    check("a region panel isn't the popup color",
          not near(col, th.user_interface.wcol_menu_back.inner[:3], 0.05), col)
    check("its labels have the regular style, red", count_color("other", inner, 0, 1) > 10,
          count_color("other", inner, 0, 1))
    yield from close_all()
    # A menu, the baseline that shows these checks can fail.
    tear_menu("SIM_MT_short"); yield 0.8
    yield from grab("menu")
    v = torn_box("base", "menu"); log("menu tear-off", v)
    check("the menu appears", real(v), v)
    inner = (v[0] + 8, v[1] + 8, v[2] - 8, v[3] - 8)
    col = median_color("menu", inner); log("menu tear-off color", col)
    check("a torn-off menu keeps the popup color",
          near(col, th.user_interface.wcol_menu_back.inner[:3], 0.1)
          and not near(col, th.regions.sidebars.back[:3], 0.1), col)
    check("its text has the popup style, green", count_color("menu", inner, 1, 0) > 10,
          count_color("menu", inner, 1, 0))


SC["p6_look"] = s_p6_look


# ---------------------------------------------------------------- Phases 7 and 8
# Not run yet, and the code they test hasn't been built. Positions come from frame diffs at run
# time and every box is logged, so the first run can calibrate. A frame diff's box is the block's
# rect here: on p6_look-other.png nothing outside it differs and its outline is the box's edge.
# Measured on earlier shots (100% scale):
# - STRIP_MENU: the header's line is 28 down from the top, on multicol_header-m.png.
# - STRIP_PANEL: that line is 37 down, on number-base_po.png. Rows there are 20 tall, 25 apart.
# - TITLE_MENU: the enum scenarios' 14 down, TITLE_Y is the panels' 17.
# Inferred, so check these first if a step fails:
# - PARK: must stay left of every tear-off opened at the center, and clear of the shelf.
# - BAR_X: inside the scrollbar, from tear_off_scrollbar_calc, which isn't in any shot yet.
# - The grips' bands, from tear_off_zone_at: 6 outside and 3 inside. The steps press 2 outside.
# - The wheel moves content by one UI_UNIT_Y, 20 px, as menu_scroll_to_y does.
#
# Double-clicks can't be simulated, and cursors don't show in a screenshot, so a grip's reset and
# every cursor shape stay hand tests. "Same as before" needs a build without these phases, see
# ref_check.
PARK = (250, 200)
STRIP_MENU = 29
STRIP_PANEL = 38
TITLE_MENU = 14
PANEL_ROW0 = 55
PANEL_ROW = 25
BAR_X = 5
# The header's line stops 8 short of the edge, on multicol_header-m.png.
LINE_GAP = 12
# UI_MENU_WIDTH_MIN is 180 at 100%, and a box's far edge is its last pixel.
FLOOR = 178


def park():
    """Over the viewport, so nothing is hovered and no row or grip is lit."""
    move(*PARK); yield 0.3
    move(*PARK); yield 0.3


def begin(*states):
    """Only the tear-off may differ between frames, so no tooltips and no overlay text. The panels
    show from the start, because their tab appearing in the sidebar would be in every diff."""
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    for st in states:
        st["show"] = True
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("base")


def mid_x(b):
    return (b[0] + b[2]) // 2


def mid_y(b):
    return (b[1] + b[3]) // 2


def width(b):
    return b[2] - b[0]


def height(b):
    return b[3] - b[1]


def strip_box(b, h):
    """The header of a tear-off with box b, down to its line."""
    return b[0] + 2, b[3] - h, b[2] - 2, b[3] - 1


def rows_box(b, h):
    """What scrolls in a tear-off with box b."""
    return b[0] + 2, b[1] + 2, b[2] - 2, b[3] - h - 1


def need(b, what):
    """Every later step clicks relative to this box, and without it would only add noise."""
    check(what, b is not None, b)
    if b is None:
        raise RuntimeError("no box: " + what)
    return b


def need_box(n1, n2, what):
    return need(bbox(n1, n2), what)


def popup_box(n1, n2):
    """Everything above the status bar and right of the tabs. An open menu changes the status bar's
    text, and changed data lights the Undo button, neither of which is part of the popup."""
    return box_bbox(n1, n2, (30, 25, 1340, 999))


def open_menu(name):
    move(*center()); yield 0.3
    tear_menu(name); yield 0.8
    yield from park()


def open_tpanel(name):
    move(*center()); yield 0.3
    tear_panel(name); yield 0.8
    yield from park()


def opened(gen, frame, what, base="base"):
    yield from gen
    yield from grab(frame)
    return need_box(base, frame, what)


def call_menu(name):
    with bpy.context.temp_override(**override("VIEW_3D", "HEADER")):
        bpy.ops.wm.call_menu(name=name)


def call_panel(name):
    with bpy.context.temp_override(**override("VIEW_3D", "HEADER")):
        bpy.ops.wm.call_panel(name=name, keep_open=True)


def dismiss():
    """Close a regular popup, and anything a failed step left open with it."""
    yield from esc()
    yield from esc()
    yield from park()


def title_drag(b, title_y, dx, dy):
    # Not drag_title: at 80 in, a fitted menu's title is already its pin icon.
    yield from drag(b[0] + 40, b[3] - title_y, dx, dy)
    yield from park()


def collapse(b, title_y, name, base="base", box=None):
    """Press the pin icon. Returns the box of the pin it leaves."""
    yield from click(b[2] - PIN_ICON, b[3] - title_y)
    yield from park()
    yield from grab(name)
    c = need(box_bbox(base, name, box) if box else bbox(base, name), "collapsed: " + name)
    check("the pin icon collapses it: " + name, height(c) < 60, c)
    return c


def expand(c, name):
    yield from click(c[2] - 40, mid_y(c))
    yield from park()
    yield from grab(name)


def closes(b, title_y, name, base="base"):
    yield from click(b[2] - X_ICON, b[3] - title_y)
    yield from park()
    yield from grab(name)
    n = rdiff(base, name, b)
    check("the X closes it: " + name, n < 200, n)


def wheel(x, y, down=True, n=1, gap=0.1):
    t = "WHEELDOWNMOUSE" if down else "WHEELUPMOUSE"
    move(x, y); yield W
    move(x, y); yield W
    for _ in range(n):
        win().event_simulate(type=t, value="PRESS", x=int(x), y=int(y)); yield gap


def crop(b, by):
    """Drag the bottom grip up from just below the block."""
    yield from drag(mid_x(b), b[1] - 2, 0, by)
    yield from park()


def uncrop(v, by):
    """Drag the bottom grip down past where a crop of `by` started, as far as the window allows."""
    yield from drag(mid_x(v), v[1] - 2, 0, -min(by + 40, v[1] - 5))
    yield from park()


def grip_cancel(x, y, tx, ty, cancel="ESC"):
    """Press a grip, go to (tx, ty), cancel with the button still down, and only then release."""
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.1
    for i in range(1, 5):
        move(x + (tx - x) * i // 4, y + (ty - y) * i // 4); yield 0.05
    yield 0.2
    if cancel == "RIGHTMOUSE":
        press(tx, ty, cancel); yield 0.1
        release(tx, ty, cancel); yield 0.2
    else:
        key(cancel, tx, ty); yield 0.05
        key(cancel, tx, ty, None, "RELEASE"); yield 0.2
    release(tx, ty); yield 0.4


def ink(name, box, margin=0.2):
    """The box of what stands out from the median color of a box: text and icons."""
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return None
    f = FRAME[name][y0:y1 + 1, x0:x1 + 1]
    d = np.abs(f - np.median(f.reshape(-1, 3), axis=0)).max(axis=2) > margin
    if not d.any():
        return None
    ys, xs = np.where(d)
    return int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0, int(ys.max()) + y0


def text_w(text):
    """The width of text in the UI font. Inferred: that's the default font at the widget size."""
    import blf
    points = bpy.context.preferences.ui_styles[0].widget.points
    blf.size(0, points * bpy.context.preferences.system.ui_scale)
    return blf.dimensions(0, text)[0]


def text_whole(name, box, text):
    """Whether text in a box is as wide as the font says. A clipped text ends sooner, in dots."""
    t, want = ink(name, box), text_w(text)
    log("ink", t, "font width", want, "for", text)
    return t is not None and width(t) >= 0.9 * want


def title_whole(name, b, title, title_y=TITLE_MENU):
    # Starts past the grip, and ends before the pin icon.
    box = (b[0] + 24, b[3] - title_y - 9, b[2] - PIN_ICON - 8, b[3] - title_y + 9)
    return text_whole(name, box, title)


def field_right(name, b, y):
    """The first pixel from the block's right edge in row y that isn't the block's background."""
    row = FRAME[name][y]
    bg = row[b[2] - 4]
    x = b[2] - 4
    while x > b[0] and np.abs(row[x] - bg).max() < 0.04:
        x -= 1
    return x


def line_extent(name, b, down):
    """How far the header's line reaches, down from the top of box b."""
    y = b[3] - down
    xs = np.where(np.abs(FRAME[name][y, b[0] + 3:b[2] - 1] -
                         FRAME[name][y + 4, b[0] + 3:b[2] - 1]).max(axis=1) > 0.03)[0]
    return (int(xs.min()) + b[0] + 3, int(xs.max()) + b[0] + 3) if xs.size else None


def patch_diff(n1, x1, y1, n2, x2, y2, w, h, thresh=0.04):
    """Pixels that differ between a patch of one frame and one elsewhere in another."""
    a = FRAME[n1][y1:y1 + h, x1:x1 + w]
    b = FRAME[n2][y2:y2 + h, x2:x2 + w]
    return int((np.abs(a - b).max(axis=2) > thresh).sum())


def color_count(name, box, xy, thresh=0.03):
    """Pixels in a box that aren't the color at xy, for something faint like a resting bar."""
    x0, y0, x1, y1 = box
    return int((np.abs(FRAME[name][y0:y1 + 1, x0:x1 + 1] - FRAME[name][xy[1], xy[0]]).max(axis=2) >
                thresh).sum())


def load_shot(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[:, :, :3]


def ref_check(shot_name, box):
    """Same pixels as a build without Phases 7 and 8. Record with SIM_RECORD_REF=1 run.sh ... on
    such a build, into ref/ beside the shots. Without a recording this only says so, because
    comparing a build with itself would pass whatever it does."""
    import shutil
    src = os.path.join(SHOTS, f"{SCEN}-{shot_name}.png")
    ref_dir = os.path.join(OUT, "ref")
    ref = os.path.join(ref_dir, f"{SCEN}-{shot_name}.png")
    if os.environ.get("SIM_RECORD_REF"):
        os.makedirs(ref_dir, exist_ok=True)
        shutil.copyfile(src, ref)
        log("REF recorded", ref)
        return
    if not os.path.exists(ref):
        log("INCONCLUSIVE: nothing to compare with, record", ref)
        return
    x0, y0, x1, y1 = box
    n = int((np.abs(load_shot(ref)[y0:y1 + 1, x0:x1 + 1] -
                    FRAME[shot_name][y0:y1 + 1, x0:x1 + 1]).max(axis=2) > 0.01).sum())
    check("same pixels as before these phases: " + shot_name, n == 0, n)


# ---------------------------------------------------------------- Phase 7: menus
def s_p7_menu_fit():
    yield from begin()
    P = SIM_OT_row_probe.state
    # The attached menu keeps the floor, which is what the torn-off one has to drop.
    move(*center()); yield 0.3
    call_menu("SIM_MT_short"); yield 0.8
    yield from grab("att")
    a = need_box("base", "att", "the attached menu opens")
    check("the attached menu keeps its floor", width(a) >= FLOOR, a)
    yield from dismiss()

    # Short rows and a short title: the title decides.
    b = yield from opened(open_menu("SIM_MT_short"), "m", "the tear-off opens")
    check("narrower than the floor", width(b) < FLOOR, b)
    check("narrower than the attached menu", width(b) < width(a), (b, a))
    check("no narrower than its header", title_whole("m", b, "Sim Short"), b)
    for i in (0, 2):
        x, y = tear_row(b, i)
        yield from click(x, y); yield 0.3
        check(f"row {i} clicks", P["last"] == i, P)
    yield from park()
    c = yield from collapse(b, TITLE_MENU, "col")
    yield from expand(c, "exp")
    check("the pin expands it in place", rdiff("m", "exp", b) < 100, rdiff("m", "exp", b))
    yield from closes(b, TITLE_MENU, "closed")

    # Short rows and a long title: the header sets the width, and its icons stay reachable.
    b = yield from opened(open_menu("SIM_MT_short_title"), "t", "the long title opens")
    check("the title isn't clipped", title_whole("t", b, LONG_TITLE), b)
    c = yield from collapse(b, TITLE_MENU, "tcol")
    yield from expand(c, "texp")
    yield from closes(b, TITLE_MENU, "tclosed")

    # A long row: the rows set the width.
    b = yield from opened(open_menu("SIM_MT_long"), "l", "the long row opens")
    x, y = tear_row(b, 0)
    row = (b[0] + 2, y - 9, b[2] - 2, y + 9)
    check("the longest row isn't clipped", text_whole("l", row, LONG_ROW + " 00"), b)
    check("the title stays", title_whole("l", b, "Sim Long"), b)
    yield from click(x, y); yield 0.3
    check("the long row clicks", P["last"] == 0, P)
    yield from park()
    yield from closes(b, TITLE_MENU, "lclosed")


SC["p7_menu_fit"] = s_p7_menu_fit


def s_p7_attached():
    """An attached menu doesn't change, with or without a tear-off open beside it."""
    yield from begin()
    move(*center()); yield 0.3
    call_menu("SIM_MT_short"); yield 0.8
    yield from grab("att1")
    a = need(popup_box("base", "att1"), "the attached menu opens")
    check("it keeps its floor", width(a) >= FLOOR, a)
    ref_check("att1", a)
    yield from dismiss()
    b = yield from opened(open_menu("SIM_MT_short"), "m", "the tear-off opens")
    yield from title_drag(b, TITLE_MENU, -300, -200)
    move(*center()); yield 0.3
    call_menu("SIM_MT_short"); yield 0.8
    yield from grab("att2")
    n = rdiff("att1", "att2", a)
    check("the same with a tear-off open", n < 20, n)
    yield from dismiss()


SC["p7_attached"] = s_p7_attached


def s_p7_menu_cols():
    yield from begin()
    P = SIM_OT_row_probe.state
    # The header is wider than the columns, and goes to the last one.
    b = yield from opened(open_menu("SIM_MT_cols_long"), "m", "the tear-off opens")
    check("the title isn't clipped", title_whole("m", b, LONG_TITLE), b)
    y = b[3] - TEAR_ROW0
    yield from click(b[0] + 30, y); yield 0.3
    check("a row in the first column clicks", P["last"] == 0, P)
    yield from click(b[2] - 30, y); yield 0.3
    check("a row in the last column clicks", P["last"] == 100, P)
    yield from park()
    line = line_extent("m", b, 28); log("line", line)
    check("the line spans the columns", line is not None and line[1] >= b[2] - LINE_GAP, (line, b))
    c = yield from collapse(b, TITLE_MENU, "col")
    yield from expand(c, "exp")
    check("the pin expands it in place", rdiff("m", "exp", b) < 100, rdiff("m", "exp", b))
    yield from closes(b, TITLE_MENU, "closed")
    # The columns are wider than the title. Measured at 259 wide before these phases, and the room
    # for the scrollbar is 15.
    b = yield from opened(open_menu("SIM_MT_cols"), "s", "the shorter title opens")
    check("no wider than it used to be", width(b) <= 259 + 15, b)
    st = SIM_OT_area_probe.state
    yield from click(b[2] - 60, b[3] - TEAR_ROW0); yield 0.3
    check("its last column clicks", st["runs"] == 1, st)
    yield from park()
    yield from closes(b, TITLE_MENU, "sclosed")


SC["p7_menu_cols"] = s_p7_menu_cols


def s_p7_menu_enum():
    yield from begin()
    ts = bpy.context.tool_settings
    was = ts.transform_pivot_point
    move(*center()); yield 0.3
    r = tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    check("the operator runs", r == {"INTERFACE"}, r)
    check("tearing off leaves the value", ts.transform_pivot_point == was, was)
    yield from park()
    yield from grab("m")
    b = need_box("base", "m", "the tear-off opens")
    # Measured at 291 wide before these phases, when the title always took 10 units.
    check("narrower than it used to be", width(b) < 291, b)
    check("the title isn't clipped", title_whole("m", b, "Transform Pivot Point"), b)
    for i in (0, 1, 2, 4, 3):
        x, y = tear_row(b, i)
        yield from click(x, y); yield 0.3
        check("item applies: " + PIVOTS[i], ts.transform_pivot_point == PIVOTS[i],
              ts.transform_pivot_point)
    yield from park()
    # Only in the viewport, because the items changed the pivot icon in its header.
    c = yield from collapse(b, TITLE_MENU, "col", box=VIEW)
    yield from expand(c, "exp")
    yield from closes(b, TITLE_MENU, "closed")


SC["p7_menu_enum"] = s_p7_menu_enum


def sub_width(parent, y, before, name):
    """Open the submenu of the row at y, and return the width of what opens beside the parent."""
    yield from click(mid_x(parent), y); yield 0.5
    yield from grab(name)
    s = box_bbox(before, name, (parent[2] + 1, 0, 1599, 999))
    log("submenu", name, s, "beside", parent)
    return width(s) if s else None


def s_p7_submenu():
    """A submenu of a fitted menu keeps the floor, or it would open as narrow as its parent."""
    yield from begin()
    move(*center()); yield 0.3
    call_menu("SIM_MT_parent"); yield 0.8
    yield from grab("att")
    a = need(popup_box("base", "att"), "the attached parent opens")
    # Two rows below it, measured up from the bottom edge, because this menu also has a title.
    w_att = yield from sub_width(a, a[1] + MENU_BOTTOM + ROW * 2, "att", "att_sub")
    yield from dismiss()
    yield from dismiss()
    b = yield from opened(open_menu("SIM_MT_parent"), "m", "the torn-off parent opens")
    check("the torn-off parent is fitted", width(b) < FLOOR, b)
    w_torn = yield from sub_width(b, tear_row(b, 0)[1], "m", "torn_sub")
    check("it opens from the attached parent", w_att is not None, w_att)
    check("it opens from the torn-off parent", w_torn is not None, w_torn)
    check("it keeps the floor", w_torn is not None and w_torn >= 165, w_torn)
    # Inferred tolerance: the attached one follows its row, the torn-off one is the floor itself.
    check("the same width from both", w_att is not None and w_torn is not None and
          abs(w_att - w_torn) <= 12, (w_att, w_torn))
    yield from dismiss()


SC["p7_submenu"] = s_p7_submenu


# ---------------------------------------------------------------- Phase 7: the right edge
def s_p7_width_reflow():
    st = SIM_PT_wrap.state
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_wrap"), "m", "the tear-off opens")
    y = mid_y(b)
    field_y = b[3] - PANEL_ROW0
    edge0 = field_right("m", b, field_y)
    log("field edge", edge0, "of", b)
    check("the field is measured, not the block", b[2] - edge0 >= 6, (edge0, b))
    draws = st["draw_popup"]
    yield from drag(b[2] + 2, y, 120, 0)
    yield from park()
    yield from grab("wide")
    v = need_box("base", "wide", "after the drag")
    check("wider by the drag", abs(width(v) - width(b) - 120) <= 2, (b, v))
    check("the left edge stays", abs(v[0] - b[0]) <= 1, (b, v))
    check("the height stays", abs(height(v) - height(b)) <= 1, (b, v))
    check("Python drew it again", st["draw_popup"] > draws, st["draw_popup"])
    # Reflow, not a stretched image: the field's edge follows and its margin keeps its size, and
    # what's left of the field is the same pixels.
    edge1 = field_right("wide", v, field_y)
    log("field edge", edge1, "of", v)
    check("the field got wider", abs(edge1 - edge0 - 120) <= 2, (edge0, edge1))
    check("its margin stays", abs((v[2] - edge1) - (b[2] - edge0)) <= 1, (edge0, edge1))
    left = (b[0] + 2, b[1] + 2, b[0] + 60, b[3] - 2)
    check("the left of the rows doesn't stretch", rdiff("m", "wide", left) < 30,
          rdiff("m", "wide", left))
    # Back to the designed width, and it's exact: the drag lands where it started.
    yield from drag(v[2] + 2, y, b[2] - v[2], 0)
    yield from park()
    yield from grab("back")
    w = need_box("base", "back", "after the drag back")
    check("back at the designed width", same_box(b, w, 1), (b, w))
    check("the same pixels as at the start", rdiff("m", "back", b) < 50, rdiff("m", "back", b))
    yield from closes(b, TITLE_Y, "closed")


SC["p7_width_reflow"] = s_p7_width_reflow


def s_p7_width_limits():
    st, small = SIM_PT_wrap.state, SIM_PT_small.state
    ui = SIM_PT_ui_cols.state
    yield from begin(st, small, ui)
    b = yield from opened(open_tpanel("SIM_PT_wrap"), "m", "the tear-off opens")
    y = mid_y(b)
    # The maximum: the window, and the left edge doesn't give way.
    x = b[2] + 2
    yield from drag(x, y, 1598 - x, 0)
    yield from park()
    yield from grab("max")
    v = need_box("base", "max", "dragged past the window")
    log("at the window edge", v)
    check("the right edge stays in the window", v[2] <= 1590, v)
    check("the left edge stays", abs(v[0] - b[0]) <= 1, (b, v))
    check("it did grow", width(v) > width(b) + 300, (b, v))
    # The minimum for wrapped text: its rows are full, so about the designed width. p9_width_min
    # has the panel that goes below it.
    yield from drag(v[2] + 2, y, 10 - (v[2] + 2), 0)
    yield from park()
    yield from grab("min")
    w = need_box("base", "min", "dragged far left")
    log("at the minimum", w, "designed", b)
    check("the minimum is no wider than the designed width", width(w) <= width(b) + 1, (b, w))
    check("and the left edge stays", abs(w[0] - b[0]) <= 1, (b, w))
    yield from close_all()
    yield from park()

    # The block is wider than this panel's layout, and one pixel must not narrow it to the layout.
    s = yield from opened(open_tpanel("SIM_PT_small"), "s", "the small panel opens")
    check("the block hugs its layout, with no popup minimum", width(s) < FLOOR, s)
    yield from drag(s[2] + 2, mid_y(s), 1, 0)
    yield from park()
    yield from grab("s1")
    v = need_box("base", "s1", "after one pixel")
    check("one pixel never narrows it", width(v) >= width(s), (s, v))
    check("one pixel does no more than that", width(v) <= width(s) + 3, (s, v))
    yield from drag(v[2] + 2, mid_y(s), 40, 0)
    yield from park()
    yield from grab("s2")
    v = need_box("base", "s2", "after more")
    check("then it grows with the drag", abs(width(v) - width(s) - 41) <= 3, (s, v))
    yield from drag(v[2] + 2, mid_y(s), -300, 0)
    yield from park()
    yield from grab("s3")
    v = need_box("base", "s3", "dragged back")
    check("it returns to its first width", same_box(s, v, 1), (s, v))
    yield from close_all()
    yield from park()

    # Python only ever sees a shelf's width. It did draw, so a stale 0 can't pass.
    p = yield from opened(open_tpanel("SIM_PT_ui_cols"), "u", "the other panel opens")
    draws = ui["popup"].get("draws", 0)
    yield from drag(p[2] + 2, mid_y(p), 60, 0)
    yield from park()
    check("it drew again after the drag", ui["popup"].get("draws", 0) > draws, ui["popup"])
    check("Python still sees no width", ui["popup"].get("width") == 0, ui["popup"])


SC["p7_width_limits"] = s_p7_width_limits


def s_p7_width_cancel():
    st = SIM_PT_wrap.state
    P = SIM_OT_row_probe.state
    sc = bpy.context.scene
    yield from begin(st)
    ob = bpy.context.view_layer.objects.active
    b = yield from opened(open_tpanel("SIM_PT_wrap"), "m", "the tear-off opens")
    gy = mid_y(b)
    # A press in the outer band is over the viewport, which must not see it.
    check("the cube starts selected", ob.select_get(), None)
    yield from click(b[2] + 2, gy)
    yield from park()
    yield from grab("pressed")
    check("the band keeps the selection", ob.select_get(), None)
    check("a press alone doesn't resize", same_box(b, bbox("base", "pressed"), 1),
          bbox("base", "pressed"))
    yield from drag(b[2] + 2, gy, 80, 0)
    yield from park()
    yield from grab("wide")
    w = need_box("base", "wide", "after the drag")
    check("wider by the drag", abs(width(w) - width(b) - 80) <= 2, (b, w))
    # Over a row with the button down. A cancel must restore the size and swallow the release.
    row_y = b[3] - PANEL_ROW0 - PANEL_ROW * 2
    for cancel in ("ESC", "RIGHTMOUSE"):
        runs = P["runs"]
        yield from grip_cancel(w[2] + 2, row_y, mid_x(b), row_y, cancel)
        yield from park()
        yield from grab("cancel_" + cancel)
        v = bbox("base", "cancel_" + cancel)
        check(cancel + " restores the width", same_box(w, v, 1), (w, v))
        check(cancel + ": the release runs no row", P["runs"] == runs, P)
    # And input isn't stuck after that.
    yield from click(mid_x(b), row_y); yield 0.3
    check("the row still clicks after a cancel", P["last"] == 7, P)
    yield from park()
    # A checkbox waiting to start a drag-toggle finishes, wherever the release lands.
    was = sc.use_gravity
    x, y = b[0] + 60, b[3] - PANEL_ROW0 - PANEL_ROW
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.1
    move(x + 30, y); yield 0.05
    move(w[2] + 2, y); yield 0.2
    release(w[2] + 2, y); yield 0.4
    yield from park()
    yield from grab("toggled")
    check("a checkbox dragged into the band still toggles", sc.use_gravity != was, sc.use_gravity)
    # Only in the viewport, because the checkbox could also show in the Properties editor.
    v = box_bbox("base", "toggled", VIEW)
    check("and that doesn't resize", same_box(w, v, 1), (w, v))
    # The baseline for the band: the same press with no tear-off does deselect.
    yield from close_all()
    yield from click(b[2] + 2, gy)
    yield from park()
    if ob.select_get():
        log("INCONCLUSIVE: a press on that spot doesn't deselect without a tear-off either")
    else:
        check("without a tear-off that press deselects", True)


SC["p7_width_cancel"] = s_p7_width_cancel


def s_p7_width_two():
    """Modal ownership stays with the older tear-off, and the newer one clears its hover."""
    st = SIM_PT_wrap.state
    yield from begin(st)
    a0 = yield from opened(open_tpanel("SIM_PT_wrap"), "a_m", "the older tear-off opens")
    yield from title_drag(a0, TITLE_Y, -300, -150)
    yield from grab("a")
    a = need_box("base", "a", "the older tear-off moved")
    b = yield from opened(open_tpanel("SIM_PT_field"), "two", "the newer tear-off opens", base="a")
    log("older", a, "newer", b)
    # Hover: the line shows on the older, and goes when the cursor is inside the newer.
    x, y = a[2] + 2, mid_y(a)
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    yield from grab("hover")
    edge = (a[2] - 4, a[1] + 10, a[2] + 1, a[3] - 10)
    line = box_bbox("two", "hover", edge)
    check("the grip lights while hovered", line is not None, line)
    # In one move, so the older one never sees the cursor leave its band.
    tx, ty = b[0] + 60, b[3] - TITLE_Y
    move(tx, ty); yield 0.3
    move(tx, ty); yield 0.3
    yield from grab("moved")
    gone = box_bbox("two", "moved", a)
    check("inside the newer one the older goes dark", gone is None, gone)
    # Press on the older and release over the newer.
    yield from park()
    tx, ty = mid_x(b), mid_y(b)
    yield from drag(x, y, tx - x, ty - y)
    yield from park()
    yield from grab("released")
    own = (a[0] - 2, a[1], 1599, a[3])
    v = need(box_bbox("base", "released", own), "the older tear-off after the drag")
    check("the older one took the drag", abs(v[2] - a[2] - (tx - x)) <= 2, (a, v))
    check("the newer one is untouched", rdiff("two", "released", b) < 50,
          rdiff("two", "released", b))
    # A later move changes nothing, so the drag did end.
    move(tx, ty); yield 0.2
    move(x + 60, y); yield 0.2
    move(tx, ty - 10); yield 0.2
    yield from park()
    yield from grab("later")
    check("a later move changes nothing", rdiff("released", "later", own) < 50,
          rdiff("released", "later", own))


SC["p7_width_two"] = s_p7_width_two


def s_p7_width_keep():
    st = SIM_PT_wrap.state
    view = bpy.context.preferences.view
    yield from begin(st)
    # A frame to diff at the other scale.
    view.ui_scale = 1.5; yield 1.5
    yield from park()
    yield from grab("base15")
    view.ui_scale = 1.0; yield 1.5
    yield from park()
    yield from grab("base")
    b = yield from opened(open_tpanel("SIM_PT_wrap"), "m", "the tear-off opens")
    yield from drag(b[2] + 2, mid_y(b), 100, 0)
    yield from park()
    yield from grab("wide")
    v = need_box("base", "wide", "after the drag")
    c = yield from collapse(v, TITLE_Y, "col")
    yield from expand(c, "exp")
    w = need_box("base", "exp", "after expanding")
    check("collapse and expand keep the width", same_box(v, w, 1), (v, w))
    view.ui_scale = 1.5; yield 1.5
    yield from park()
    yield from grab("big")
    g = need_box("base15", "big", "at 150%")
    log("at 150%", g, "at 100%", v)
    check("a scale change scales it", abs(width(g) - 1.5 * width(v)) <= 6, (v, g))
    view.ui_scale = 1.0; yield 1.5
    yield from park()
    yield from grab("small")
    s = need_box("base", "small", "back at 100%")
    check("and returns", abs(width(s) - width(v)) <= 2, (v, s))


SC["p7_width_keep"] = s_p7_width_keep


# ---------------------------------------------------------------- Phase 7: the tool shelf
def s_p7_shelf_steps():
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    # The shelf doesn't resize here, but the stats would still be in the diff.
    area().spaces.active.overlay.show_text = False
    C = SIM_PT_cols.state
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    yield from park()
    yield from grab("base")
    shelf_w = shelf().width
    yield from tear_center("SIM_PT_cols", rt="TOOLS")
    yield from park()
    yield from grab("m")
    v = need(torn_box("base", "m"), "the shelf tear-off opens")
    region_count = C["popup"].get("region_count")
    log("torn off at", C["popup"])
    check("it has a shelf width", C["popup"].get("width", 0) > 0, C["popup"])
    steps = {92.0, 132.0, 172.0, 212.0, 100.0, 140.0, 180.0, 220.0}

    def on_step(w):
        return w is not None and any(abs(w - s) < 1.0 for s in steps)

    def grip(name, dx):
        nonlocal v
        yield from drag(v[2] + 2, mid_y(v), dx, 0)
        yield from park()
        yield from grab(name)
        v = need(torn_box("base", name), name)
        rec = C["popup"]
        title = (v[0] + 2, v[3] - TITLE_Y - 9, v[2] - PIN_ICON - 8, v[3] - TITLE_Y + 9)
        # Read by hand with the shot, because a screenshot diff can't judge clipping.
        log(name, "width", rec.get("width"), "count", rec.get("count"), "box", v,
            "title ink", ink(name, title))
        return rec.get("width"), rec.get("count")

    def title_moves(name):
        """The header still drags at this width. In its left margin, because at one column the
        pin icon starts right after it."""
        nonlocal v
        yield from drag(v[0] + 5, v[3] - TITLE_Y, 0, -30)
        yield from park()
        yield from grab(name)
        w = need(torn_box("base", name), name)
        check("the title drags: " + name,
              abs(w[3] - v[3] + 30) <= 2 and abs(width(w) - width(v)) <= 2, (v, w))
        v = w

    # Narrowest first, then one column at a time.
    w, n = yield from grip("n1", -300)
    check("far left is the narrowest step", on_step(w) and n == 1, (w, n))
    yield from title_moves("n1_title")
    seen = [n]
    for i in (2, 3, 4):
        w, n = yield from grip(f"n{i}", 40)
        check(f"step {i} is a snap point", on_step(w), w)
        seen.append(n)
        yield from title_moves(f"n{i}_title")
    check("the count goes 1, 2, 3, 4", seen == [1, 2, 3, 4], seen)
    # Free above the last step, as the real shelf's text list.
    w4 = C["popup"]["width"]
    w, n = yield from grip("free", 60)
    check("free above the last step", w is not None and abs(w - w4 - 60) < 2 and not on_step(w),
          (w4, w))
    check("and still 4 columns", n == 4, n)
    # None of this reaches the real shelf.
    check("the shelf keeps its width", shelf().width == shelf_w, (shelf_w, shelf().width))
    check("its own count doesn't change", C["popup"].get("region_count") == region_count,
          C["popup"])
    # Back to one column, where the header is tightest.
    w, n = yield from grip("n1b", -400)
    check("back to the narrowest step", on_step(w) and n == 1, (w, n))
    c = yield from collapse(v, TITLE_Y, "col", box=free_box())
    yield from expand(c, "exp")
    w2 = need(torn_box("base", "exp"), "after expanding")
    check("one column expands to the same box", same_box(v, w2, 1), (v, w2))
    yield from closes(v, TITLE_Y, "closed")


SC["p7_shelf_steps"] = s_p7_shelf_steps


# ---------------------------------------------------------------- Phase 8: the sticky header
def sticky_round(tag, b, strip_h, title_y, base="base"):
    """Frame tag+"m" has the tear-off with box b, at rest. Ends with it closed."""
    m = tag + "m"
    s, rows = strip_box(b, strip_h), rows_box(b, strip_h)
    check(tag + ": the header shows", ink(m, s) is not None, ink(m, s))
    x, y = mid_x(b), mid_y(b)
    yield from wheel(x, y, True, 5)
    yield from park()
    yield from grab(tag + "down")
    moved = box_bbox(m, tag + "down", s)
    check(tag + ": the header doesn't change", moved is None, moved)
    check(tag + ": the content moved", box_bbox(m, tag + "down", rows) is not None,
          box_bbox(m, tag + "down", rows))
    # #menu_scroll_step passes a point above the block, which a clamp to the header would stop.
    yield from wheel(x, y, False, 5)
    yield from park()
    yield from grab(tag + "up")
    n = rdiff(m, tag + "up", b)
    check(tag + ": as many wheel-ups return to the start", n < 30, n)
    # Everything in the header works at a scrolled position.
    yield from wheel(x, y, True, 5)
    yield from park()
    c = yield from collapse(b, title_y, tag + "col", base)
    yield from expand(c, tag + "exp")
    n = rdiff(tag + "down", tag + "exp", b)
    # A row cut by the arrow zone can end one pixel line sooner after a refresh.
    check(tag + ": the pin returns to the same scroll position", n <= width(b) + 30, n)
    yield from closes(b, title_y, tag + "closed", base)


def s_p8_sticky():
    st = SIM_PT_tall.state
    yield from begin(st)
    b = yield from opened(open_menu("SIM_MT_tall"), "menu_m", "the tall menu opens")
    yield from sticky_round("menu_", b, STRIP_MENU, TITLE_MENU)
    b = yield from opened(open_tpanel("SIM_PT_tall"), "panel_m", "the tall panel opens")
    yield from sticky_round("panel_", b, STRIP_PANEL, TITLE_Y)


SC["p8_sticky"] = s_p8_sticky


def s_p8_sticky_kinds():
    """A multi-column menu and an enum tear-off, whose headers are found another way."""
    yield from begin()
    P = SIM_OT_row_probe.state
    ts = bpy.context.tool_settings
    b = yield from opened(open_menu("SIM_MT_cols_tall"), "cols0", "the tall columns open")
    x, y = mid_x(b), mid_y(b)
    row_y = tear_row(b, 2)[1]
    yield from wheel(x, y, True, 3)
    yield from click(b[0] + 30, row_y); yield 0.3
    check("a scrolled row in the first column", P["last"] == 5, P)
    yield from click(b[2] - 30, row_y); yield 0.3
    check("a scrolled row in the last column", P["last"] == 105, P)
    yield from wheel(x, y, False, 3)
    yield from park()
    yield from grab("cols_m")
    yield from sticky_round("cols_", b, STRIP_MENU, TITLE_MENU)

    yield from close_all()
    ts.transform_pivot_point = "ACTIVE_ELEMENT"; yield 0.4
    yield from park()
    yield from grab("b3")
    move(*center()); yield 0.3
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from park()
    yield from grab("enum0")
    e = need_box("b3", "enum0", "the enum tear-off opens")
    yield from crop(e, 30)
    yield from grab("enum_m")
    v = need_box("b3", "enum_m", "the enum tear-off cropped")
    check("the crop applies to an enum", abs(height(e) - 30 - height(v)) <= 2, (e, v))
    yield from wheel(mid_x(v), mid_y(v), True, 1)
    x, y = tear_row(v, 1)
    yield from click(x, y); yield 0.3
    check("a scrolled item applies", ts.transform_pivot_point == PIVOTS[2],
          ts.transform_pivot_point)
    yield from park()
    yield from grab("enum_clicked")
    s = strip_box(v, STRIP_MENU)
    check("its header doesn't change", box_bbox("enum_m", "enum_clicked", s) is None,
          box_bbox("enum_m", "enum_clicked", s))
    yield from closes(v, TITLE_MENU, "enum_closed", "b3")


SC["p8_sticky_kinds"] = s_p8_sticky_kinds


def s_p8_sticky_hit():
    """A row half under the header must not take a press meant for the title. Rows are 60 tall, so
    one can stay highlighted while the cursor moves up onto the title inside its rect."""
    st = SIM_PT_tall.state
    st.update(rows=20, big=True)
    P = SIM_OT_row_probe.state
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_tall"), "m", "the tall panel opens")
    x = b[0] + 60
    # Row 0 runs from 45 to 105 down. Two wheel steps put its top 5 down, under the title.
    yield from wheel(mid_x(b), mid_y(b), True, 2)
    yield from park()
    yield from grab("scrolled")
    y = b[3] - 60
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    yield from grab("hover")
    lit = box_bbox("scrolled", "hover", rows_box(b, STRIP_PANEL))
    check("its visible half highlights", lit is not None, lit)
    runs = P["runs"]
    ty = b[3] - TITLE_Y
    move(x, ty); yield 0.3
    yield from grab("on_title")
    check("over the title it isn't highlighted any more",
          box_bbox("scrolled", "on_title", rows_box(b, STRIP_PANEL)) is None,
          box_bbox("scrolled", "on_title", rows_box(b, STRIP_PANEL)))
    press(x, ty); yield 0.1
    for i in range(1, 5):
        move(x - 100 * i // 4, ty); yield 0.05
    release(x - 100, ty); yield 0.4
    yield from park()
    yield from grab("moved")
    check("the press ran no row", P["runs"] == runs, P)
    v = need_box("base", "moved", "after the press")
    check("it started a title drag", abs(v[0] - b[0] + 100) <= 2 and abs(width(v) - width(b)) <= 2,
          (b, v))


SC["p8_sticky_hit"] = s_p8_sticky_hit


def find_layout_header(st, name, x, top, lo, hi):
    """Click down from lo to hi below top until the layout panel flips, and return that y. Any
    other row this hits only runs the probe. No shot has these headers yet, so this finds them."""
    was = st["open_" + name]
    for off in range(lo, hi, 6):
        yield from click(x, top - off); yield 0.2
        if st["open_" + name] != was:
            log("layout panel", name, "flips at", off, "down")
            return top - off
    return None


def press_at_once(x, y):
    """Move and click with no time for the arrow zone's auto-scroll, then leave the zone."""
    move(x, y); press(x, y); release(x, y)
    move(x, y - 200 if y > 500 else y + 60); yield 0.3


def s_p8_layout_panels():
    st = SIM_PT_tall.state
    st.update(rows=40, layout_panels=True)
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_tall"), "m", "the tall panel opens")
    x = b[0] + 30
    # The baseline: a press on a header does flip it.
    ya = yield from find_layout_header(st, "a", x, b[3], 44, 80)
    check("a layout panel's header flips it", ya is not None, ya)
    yb = None
    if ya is not None:
        yield from click(x, ya); yield 0.3
        yb = yield from find_layout_header(st, "b", x, b[3], b[3] - ya + 30, b[3] - ya + 80)
        check("so does the next one's", yb is not None, yb)
    if ya is None or yb is None:
        raise RuntimeError("no layout panel headers")
    yield from click(x, yb); yield 0.3
    check("both are open again", st["open_a"] and st["open_b"], st)
    cx, cy = mid_x(b), mid_y(b)
    # Under the title: this press is a title press, whatever is under it.
    yield from wheel(cx, cy, True, 2)
    yield from click(x, ya + 40); yield 0.3
    check("a press on the title doesn't flip what's under it", st["open_a"], st)
    # In the top arrow zone, 41 to 55 down.
    yield from wheel(cx, cy, True, 1)
    y = yb + 60
    log("the second header is now", b[3] - y, "down")
    yield from press_at_once(x, b[3] - 47)
    check("a press in the arrow zone doesn't flip what's under it", st["open_b"], st)
    check("nor anything else", st["open_a"], st)
    # Dragging a visible header up past the title flips that one and not the hidden one above it.
    # The press on the arrow already moved up the one row this needs.
    y = yb + 40
    yield from drag(x, y, 0, (b[3] + 5) - y)
    check("the drag flips the visible header", not st["open_b"], st)
    check("the drag doesn't flip the hidden one", st["open_a"], st)
    # Below a crop, in the bottom arrow zone.
    yield from click(x, y); yield 0.3
    yield from wheel(cx, cy, False, 2)
    check("open again before the crop", st["open_b"], st)
    yield from park()
    yield from crop(b, height(b) - 120)
    yield from grab("cropped")
    v = need_box("base", "cropped", "cropped above the second header")
    check("cropped to the asked height", abs(height(v) - 120) <= 3, v)
    yield from press_at_once(x, v[1] + 8)
    check("a press in the bottom arrow zone doesn't flip what's under it", st["open_b"], st)


SC["p8_layout_panels"] = s_p8_layout_panels


def s_p8_curve():
    """A curve replaces the scissor with its own, and leaves the test off afterwards."""
    st = SIM_PT_tall.state
    st.update(rows=60, curve=True)
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_tall"), "m", "the panel with a curve opens")
    s = strip_box(b, STRIP_PANEL)
    x, y = mid_x(b), mid_y(b)
    last = "m"
    for i in range(1, 8):
        yield from wheel(x, y, True, 3, 0.05)
        yield from park()
        name = f"w{i}"
        yield from grab(name)
        n = box_bbox("m", name, s)
        check(f"the header is untouched, {i * 60} px scrolled", n is None, n)
        check(f"the content moved, {i * 60} px scrolled",
              box_bbox(last, name, rows_box(b, STRIP_PANEL)) is not None, name)
        last = name


SC["p8_curve"] = s_p8_curve


def s_p8_scope():
    """A scope's outline comes after its scissor test is off. Without image data, because the
    outline is what this is about. The track preview takes a real clip, so it's a hand test."""
    st = SIM_PT_tall.state
    st.update(rows=60, scope=True)
    area("OUTLINER").type = "IMAGE_EDITOR"; yield 0.8
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_tall"), "m", "the panel with a scope opens")
    s = strip_box(b, STRIP_PANEL)
    x, y = mid_x(b), mid_y(b)
    last = "m"
    for i in range(1, 9):
        yield from wheel(x, y, True, 1, 0.05)
        yield from park()
        name = f"w{i}"
        yield from grab(name)
        n = box_bbox("m", name, s)
        check(f"the header is untouched, {i * 20} px scrolled", n is None, n)
        check(f"the content moved, {i * 20} px scrolled",
              box_bbox(last, name, rows_box(b, STRIP_PANEL)) is not None, name)
        last = name


SC["p8_scope"] = s_p8_scope


def s_p8_header_look():
    """The header is drawn in its own pass once clipped, and must look the same as it did."""
    th = bpy.context.preferences.themes[0]
    th.user_interface.panel_text = (1.0, 0.0, 0.0)
    th.user_interface.wcol_menu_back.text = (0.0, 1.0, 0.0)
    C = SIM_PT_cols.state
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    yield from park()
    yield from grab("base")
    # A menu. The crop adds a gutter that moves its icons, so the title is what's compared.
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, 200)
    yield from grab("mc")
    title = (b[0] + 2, b[3] - STRIP_MENU, b[0] + 70, b[3] - 1)
    n = rdiff("m", "mc", title)
    check("a clipped menu's title looks the same", n < 5, n)
    yield from close_all()
    yield from park()
    # A shelf panel: its title has the regular color, not the menu's. No gutter, so the whole strip.
    yield from tear_center("SIM_PT_cols", rt="TOOLS")
    yield from park()
    yield from grab("s")
    v = need(torn_box("base", "s"), "the shelf tear-off opens")
    # At one column there's room for the grip alone, see #tear_off_header_draw.
    yield from drag(v[2] + 2, mid_y(v), 100, 0)
    yield from park()
    yield from grab("s")
    v = need(torn_box("base", "s"), "the shelf tear-off widened")
    yield from crop(v, 20)
    yield from grab("sc")
    w = need(torn_box("base", "sc"), "the shelf tear-off cropped")
    check("the crop applies", abs(height(v) - 20 - height(w)) <= 2, (v, w))
    n = rdiff("s", "sc", strip_box(v, STRIP_PANEL))
    check("a clipped shelf panel's header looks the same", n < 5, n)
    check("and that header has the regular color",
          count_color("sc", strip_box(v, STRIP_PANEL), 0, 1) > 10,
          count_color("sc", strip_box(v, STRIP_PANEL), 0, 1))


SC["p8_header_look"] = s_p8_header_look


def s_p8_tab_scroll():
    """Tab is the only way to reach a field out of view, and typing into a hidden one is blind."""
    st = SIM_PT_fields.state
    sc = bpy.context.scene
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_fields"), "m", "the fields open")
    yield from crop(b, height(b) - 150)
    yield from grab("cropped")
    v = need_box("base", "cropped", "cropped to a few fields")
    x, y = mid_x(v), v[3] - PANEL_ROW0
    yield from click(x, y); yield 0.3
    yield from grab("edit0")
    for _ in range(6):
        yield from type_key("TAB", x, y)
    yield 0.3
    yield from grab("edit6")
    # The second row is in neither text edit, so only a scroll can change it.
    row_y = v[3] - PANEL_ROW0 - PANEL_ROW
    row = (v[0] + 2, row_y - 9, v[2] - 12, row_y + 9)
    n = rdiff("edit0", "edit6", row)
    check("Tab scrolled to the field", n > 20, n)
    yield from type_key("SEVEN", x, y, "7")
    yield from type_key("SEVEN", x, y, "7")
    yield 0.3
    yield from grab("typed")
    shown = box_bbox("edit6", "typed", rows_box(v, STRIP_PANEL))
    check("what's typed shows", shown is not None, shown)
    yield from type_key("RET", x, y); yield 0.4
    check("it went into the field Tab reached", sc.sim_values[6] == 77, list(sc.sim_values)[:8])
    check("and nothing into the first one", sc.sim_values[0] == 0, list(sc.sim_values)[:8])


SC["p8_tab_scroll"] = s_p8_tab_scroll


def s_p8_pin_bottom():
    """A pin parks near the window bottom, and clipping alone would open a sliver from there."""
    yield from begin()
    P = SIM_OT_row_probe.state
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    c = yield from collapse(b, TITLE_MENU, "col")
    yield from drag(c[0] + 40, mid_y(c), 0, 12 - mid_y(c))
    yield from park()
    yield from grab("parked")
    c2 = need_box("base", "parked", "the pin at the bottom")
    log("pin", c, "->", c2)
    check("the pin went down", c2[1] < c[1] - 100, (c, c2))
    yield from expand(c2, "exp")
    v = need_box("base", "exp", "expanded")
    log("expanded", v)
    # Inferred: the header, one row and both arrow zones are 32 + 20 + 28.
    check("taller than a sliver", height(v) >= 75, v)
    n = patch_diff("m", b[0] + 2, b[3] - 26, "exp", v[0] + 2, v[3] - 26, 60, 24)
    check("the title is whole", n < 20, n)
    # Row 1, because the wheel puts an arrow zone on row 0.
    x, y = mid_x(v), v[3] - TEAR_ROW0 - ROW
    yield from click(x, y); yield 0.3
    first = P["last"]
    check("a row clicks", first == 1, P)
    yield from wheel(x, y, True, 1)
    yield from click(x, y); yield 0.3
    check("wheel-down moves the content the right way", P["last"] == first + 1, P)
    yield from park()
    yield from closes(v, TITLE_MENU, "closed")


SC["p8_pin_bottom"] = s_p8_pin_bottom


def s_p8_wheel_outside():
    yield from begin()
    rv = area().spaces.active.region_3d
    # The baseline: this does zoom the viewport, without a tear-off.
    d0 = rv.view_distance
    yield from wheel(*PARK, True, 2)
    yield 0.4
    d1 = rv.view_distance
    log("baseline zoom", d0, "->", d1)
    yield from park()
    yield from grab("base")
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    d2 = rv.view_distance
    yield from wheel(*PARK, True, 2)
    yield 0.4
    d3 = rv.view_distance
    yield from park()
    yield from grab("outside")
    if d0 == d1:
        log("INCONCLUSIVE: the wheel doesn't zoom here even without a tear-off")
    else:
        check("the viewport gets the wheel", d3 != d2, (d2, d3))
    n = rdiff("c", "outside", v)
    check("the tear-off doesn't scroll", n < 100, n)
    # Inside it does still scroll, and the viewport stays.
    yield from wheel(mid_x(v), mid_y(v), True, 2)
    yield from park()
    yield from grab("inside")
    n = rdiff("outside", "inside", rows_box(v, STRIP_MENU))
    check("inside, the tear-off scrolls", n > 100, n)
    check("inside, the viewport keeps its zoom", rv.view_distance == d3, rv.view_distance)


SC["p8_wheel_outside"] = s_p8_wheel_outside


def s_p8_pan_release():
    """A middle mouse pan released over a newer tear-off still ends. Without the continuous grab,
    because the simulated cursor wouldn't follow a wrapped one."""
    yield from begin()
    bpy.context.preferences.inputs.use_mouse_continuous = False
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    yield from title_drag(v, TITLE_MENU, -300, 0)
    yield from grab("older")
    a = need_box("base", "older", "the older one moved")
    yield from open_tpanel("SIM_PT_field")
    yield from grab("two")
    n = need(box_bbox("older", "two", (a[2] + 4, 0, 1599, 999)), "the newer one opens")
    ax, ay = mid_x(a), mid_y(a)
    tx, ty = mid_x(n), mid_y(n)
    move(ax, ay); yield 0.3
    move(ax, ay); yield 0.3
    press(ax, ay, "MIDDLEMOUSE"); yield 0.1
    move(ax, ay + 30); yield 0.1
    move(tx, ty); yield 0.2
    release(tx, ty, "MIDDLEMOUSE"); yield 0.4
    yield from park()
    yield from grab("panned")
    m = rdiff("two", "panned", rows_box(a, STRIP_MENU))
    check("the pan moved the older one", m > 100, m)
    move(ax, ay); yield 0.2
    move(ax, ay + 40); yield 0.2
    yield from park()
    yield from grab("later")
    m = rdiff("panned", "later", a)
    check("a later move doesn't pan", m < 30, m)


SC["p8_pan_release"] = s_p8_pan_release


def s_p8_pan_hidden():
    """Keys stay with a middle mouse pan, and a hide that comes from elsewhere ends the pan. Without
    the continuous grab, because the simulated cursor wouldn't follow a wrapped one. The grab itself
    letting go during a hide is a hand test."""
    yield from begin()
    bpy.context.preferences.inputs.use_mouse_continuous = False
    ob = bpy.context.view_layer.objects.active
    # The baseline: Tab does switch modes here, without a tear-off.
    yield from type_key("TAB", *PARK)
    yield 0.8
    tab_works = ob.mode == "EDIT"
    log("baseline Tab", ob.mode)
    if tab_works:
        yield from type_key("TAB", *PARK)
        yield 0.8
    yield from park()
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    x, y = mid_x(v), mid_y(v)
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    press(x, y, "MIDDLEMOUSE"); yield 0.1
    move(x, y + 30); yield 0.1
    yield from type_key("TAB", x, y + 30)
    yield 0.8
    if tab_works:
        check("a key stays with the pan", ob.mode == "OBJECT", ob.mode)
    else:
        log("INCONCLUSIVE: Tab doesn't switch modes here even without a tear-off")
    release(x, y + 30, "MIDDLEMOUSE"); yield 0.4
    if ob.mode != "OBJECT":
        with bpy.context.temp_override(**override()):
            bpy.ops.object.mode_set(mode="OBJECT")
        yield 0.8
    # Hidden during a pan by something other than a key. The release goes nowhere.
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    press(x, y, "MIDDLEMOUSE"); yield 0.1
    move(x, y + 10); yield 0.1
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="EDIT")
    yield 0.8
    move(x, y + 20); yield 0.2
    release(x, y + 20, "MIDDLEMOUSE"); yield 0.2
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="OBJECT")
    yield 0.8
    yield from park()
    yield from grab("back")
    move(x, y); yield 0.2
    move(x, y + 40); yield 0.2
    yield from park()
    yield from grab("later")
    n = rdiff("back", "later", v)
    check("back in its mode, a move doesn't pan", n < 30, n)


SC["p8_pan_hidden"] = s_p8_pan_hidden


# ---------------------------------------------------------------- Phase 8: the bottom edge
def crop_round(tag, b, by, strip_h):
    """Frame tag+"m" has the tear-off with box b, at rest. Ends with no crop."""
    x = mid_x(b)
    yield from crop(b, by)
    yield from grab(tag + "crop")
    v = need_box("base", tag + "crop", tag + ": cropped")
    check(tag + ": shorter by the drag", abs(height(b) - by - height(v)) <= 2, (b, v))
    check(tag + ": the top and left stay", abs(v[3] - b[3]) <= 1 and abs(v[0] - b[0]) <= 1, (b, v))
    y = mid_y(v)
    yield from wheel(x, y, True, 2)
    yield from park()
    yield from grab(tag + "wheel")
    moved = box_bbox(tag + "crop", tag + "wheel", rows_box(v, strip_h))
    check(tag + ": the wheel scrolls it", moved is not None, moved)
    yield from wheel(x, y, False, 2)
    yield from park()
    yield from grab(tag + "unwheel")
    n = rdiff(tag + "crop", tag + "unwheel", v)
    check(tag + ": and scrolls it back", n < 30, n)
    # Past its natural height: the crop must be able to grow, then go away.
    yield from uncrop(v, by)
    yield from grab(tag + "back")
    w = popup_box("base", tag + "back")
    check(tag + ": dragging past natural height restores it", same_box(b, w, 1), (b, w))
    n = rdiff(tag + "m", tag + "back", b)
    check(tag + ": with the same pixels", n < 50, n)


def s_p8_crop():
    st = SIM_PT_mid.state
    P = SIM_OT_row_probe.state
    ts = bpy.context.tool_settings
    yield from begin(st)
    ob = bpy.context.view_layer.objects.active
    b = yield from opened(open_menu("SIM_MT_mid"), "menu_m", "the menu opens")
    yield from crop_round("menu_", b, 200, STRIP_MENU)
    # A press in the outer band is over the viewport, which must not see it.
    check("the cube starts selected", ob.select_get(), None)
    yield from click(mid_x(b), b[1] - 2)
    yield from park()
    check("the band keeps the selection", ob.select_get(), None)
    # Canceled over a row with the button down: the restored block is under the cursor.
    runs = P["runs"]
    x, y = mid_x(b), b[1] - 2
    yield from grip_cancel(x, y, x, y + 120)
    yield from park()
    yield from grab("menu_esc")
    v = bbox("base", "menu_esc")
    check("Esc restores the height", same_box(b, v, 1), (b, v))
    check("the release runs no row", P["runs"] == runs, P)
    yield from click(x, y + 120); yield 0.3
    check("a row still clicks after that", P["runs"] == runs + 1, P)
    yield from park()
    yield from closes(b, TITLE_MENU, "menu_closed")

    b = yield from opened(open_tpanel("SIM_PT_mid"), "panel_m", "the panel opens")
    yield from crop_round("panel_", b, 200, STRIP_PANEL)
    yield from closes(b, TITLE_Y, "panel_closed")

    was = ts.transform_pivot_point
    move(*center()); yield 0.3
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from park()
    yield from grab("enum_m")
    b = need_box("base", "enum_m", "the enum opens")
    yield from crop_round("enum_", b, 30, STRIP_MENU)
    check("the grip ran no item", ts.transform_pivot_point == was, ts.transform_pivot_point)


SC["p8_crop"] = s_p8_crop


def keep_round(tag, b, by, title_y, draws):
    """The crop and scroll position survive a refresh, and a collapse with the pin moved."""
    sc = bpy.context.scene
    yield from crop(b, by)
    yield from grab(tag + "crop")
    v = need(box_bbox("base", tag + "crop", VIEW), tag + ": cropped")
    yield from wheel(mid_x(v), mid_y(v), True, 3)
    yield from park()
    yield from grab(tag + "scrolled")
    n0 = draws()
    sc.frame_current += 1; yield 1.0
    yield from park()
    yield from grab(tag + "frame")
    check(tag + ": the frame change did refresh it", draws() > n0, (n0, draws()))
    n = rdiff(tag + "scrolled", tag + "frame", v)
    check(tag + ": the crop and scroll position survive it", n < 100, n)
    c = yield from collapse(v, title_y, tag + "col", box=VIEW)
    yield from drag(c[0] + 40, mid_y(c), 120, -60)
    yield from park()
    yield from grab(tag + "pinned")
    c2 = need(box_bbox("base", tag + "pinned", VIEW), tag + ": the pin moved")
    check(tag + ": the pin did move", abs(c2[0] - c[0] - 120) <= 2, (c, c2))
    yield from expand(c2, tag + "exp")
    e = need(box_bbox("base", tag + "exp", VIEW), tag + ": expanded")
    log(tag, "expanded", e, "from", v)
    check(tag + ": the same size",
          abs(width(e) - width(v)) <= 1 and abs(height(e) - height(v)) <= 1, (v, e))
    check(tag + ": where the pin was", abs(e[0] - c2[0]) <= 2 and abs(e[3] - c2[3]) <= 2, (c2, e))
    n = patch_diff(tag + "scrolled", v[0], v[1], tag + "exp", e[0], e[1], width(v), height(v))
    # As in #sticky_round, at both cuts.
    check(tag + ": the same content", n <= 2 * width(v) + 30, n)
    yield from closes(e, title_y, tag + "closed")


def s_p8_crop_keep():
    st = SIM_PT_mid.state
    yield from begin(st)
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from keep_round("menu_", b, 200, TITLE_MENU, lambda: SIM_MT_mid.state["draws"])
    # The frame change shows in the timeline, which the next whole window diff would catch.
    yield from grab("base")
    b = yield from opened(open_tpanel("SIM_PT_mid"), "p", "the panel opens")
    yield from keep_round("panel_", b, 200, TITLE_Y, lambda: st["draw_popup"])


SC["p8_crop_keep"] = s_p8_crop_keep


def s_p8_crop_limits():
    st = SIM_PT_mid.state
    P = SIM_OT_row_probe.state
    yield from begin(st)
    # The minimum: the header and a row, however hard it's dragged.
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    x, y = mid_x(b), b[1] - 2
    yield from drag(x, y, 0, min(800, 990 - y))
    yield from park()
    yield from grab("min")
    v = need_box("base", "min", "dragged up hard")
    log("at the minimum", v)
    check("the top stays", abs(v[3] - b[3]) <= 1, (b, v))
    check("it stops at the minimum", 75 <= height(v) <= 130, v)
    check("the header stays", title_whole("min", v, "Sim Mid"), v)
    yield from click(mid_x(v), v[3] - TEAR_ROW0); yield 0.3
    check("and its row clicks", P["last"] == 0, P)
    yield from park()
    # A title drag keeps the height.
    yield from title_drag(v, TITLE_MENU, 120, -80)
    yield from grab("moved")
    w = need_box("base", "moved", "after a title drag")
    check("a title drag keeps the size",
          abs(height(w) - height(v)) <= 1 and abs(width(w) - width(v)) <= 1, (v, w))
    check("and moves it", abs(w[0] - v[0] - 120) <= 2 and abs(w[3] - v[3] + 80) <= 2, (v, w))
    yield from close_all()
    yield from park()

    # A panel's corner takes both axes.
    b = yield from opened(open_tpanel("SIM_PT_mid"), "p", "the panel opens")
    yield from drag(b[2] + 2, b[1] - 2, 60, 40)
    yield from park()
    yield from grab("corner")
    v = need_box("base", "corner", "after the corner")
    check("the corner widens it", abs(width(v) - width(b) - 60) <= 2, (b, v))
    check("the corner crops it", abs(height(b) - height(v) - 40) <= 2, (b, v))
    check("the top left stays", abs(v[0] - b[0]) <= 1 and abs(v[3] - b[3]) <= 1, (b, v))
    yield from close_all()
    yield from park()

    # Press on the older and release over the newer.
    a0 = yield from opened(open_menu("SIM_MT_mid"), "a0", "the older one opens")
    yield from title_drag(a0, TITLE_MENU, -300, 0)
    yield from grab("a")
    a = need_box("base", "a", "the older one moved")
    yield from open_tpanel("SIM_PT_field")
    yield from grab("two")
    n = need(box_bbox("a", "two", (a[2] + 4, 0, 1599, 999)), "the newer one opens")
    x, y = mid_x(a), a[1] - 2
    tx, ty = mid_x(n), mid_y(n)
    yield from drag(x, y, tx - x, ty - y)
    yield from park()
    yield from grab("released")
    own = (a[0] - 2, a[1], a[2] + 18, a[3])
    v = need(box_bbox("base", "released", own), "the older one after the drag")
    check("the older one took the drag", height(v) < height(a) - 100, (a, v))
    check("the newer one is untouched", rdiff("two", "released", n) < 50,
          rdiff("two", "released", n))
    move(tx, ty); yield 0.2
    move(x, y + 40); yield 0.2
    move(tx, ty - 10); yield 0.2
    yield from park()
    yield from grab("later")
    check("a later move changes nothing", rdiff("released", "later", own) < 50,
          rdiff("released", "later", own))


SC["p8_crop_limits"] = s_p8_crop_limits


def s_p8_scrolled_click():
    st = SIM_PT_mid.state
    P = SIM_OT_row_probe.state
    ts = bpy.context.tool_settings
    ts.transform_pivot_point = "ACTIVE_ELEMENT"
    yield from begin(st)
    # A menu: its rows are as far apart as a wheel step.
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    x, y = tear_row(v, 3)
    yield from click(x, y); yield 0.3
    check("a row before scrolling", P["last"] == 3, P)
    yield from wheel(x, y, True, 2)
    yield from click(x, y); yield 0.3
    check("the same spot, two wheel steps down", P["last"] == 5, P)
    # A panel: rows are 25 apart, so four take five wheel steps.
    yield from close_all()
    yield from park()
    b = yield from opened(open_tpanel("SIM_PT_mid"), "p", "the panel opens")
    yield from crop(b, 200)
    yield from grab("pc")
    v = need_box("base", "pc", "cropped")
    x, y = mid_x(v), v[3] - PANEL_ROW0 - PANEL_ROW * 2
    yield from click(x, y); yield 0.3
    check("a panel row before scrolling", P["last"] == 2, P)
    yield from wheel(x, y, True, 5)
    yield from click(x, y); yield 0.3
    check("the same spot, a hundred pixels down", P["last"] == 6, P)
    # An enum: the row's click re-resolves its property.
    yield from close_all()
    yield from park()
    yield from grab("b3")
    move(*center()); yield 0.3
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from park()
    yield from grab("e")
    e = need_box("b3", "e", "the enum opens")
    yield from crop(e, 30)
    yield from grab("ec")
    v = need_box("b3", "ec", "cropped")
    yield from wheel(mid_x(v), mid_y(v), True, 1)
    x, y = tear_row(v, 2)
    yield from click(x, y); yield 0.3
    check("an enum item, one wheel step down", ts.transform_pivot_point == PIVOTS[3],
          ts.transform_pivot_point)


SC["p8_scrolled_click"] = s_p8_scrolled_click


def s_p8_tall():
    """Clamped by the window, with no crop: this works without anyone touching a grip."""
    yield from begin()
    P = SIM_OT_row_probe.state
    b = yield from opened(open_menu("SIM_MT_tall"), "m", "the tall menu opens")
    log("clamped", b)
    check("the window clamps it", height(b) > 900, b)
    s = strip_box(b, STRIP_MENU)
    check("its header is in the window from the first frame", title_whole("m", b, "Sim Tall"), b)
    x, y = tear_row(b, 5)
    yield from click(x, y); yield 0.3
    check("a row before scrolling", P["last"] == 5, P)
    yield from wheel(x, y, True, 6)
    yield from click(x, y); yield 0.3
    check("the same spot, six wheel steps down", P["last"] == 11, P)
    # All the way down. The range is about 34 steps, from 80 rows in a 980 tall block.
    yield from wheel(x, mid_y(b), True, 60, 0.04)
    yield from park()
    yield from grab("end")
    moved = box_bbox("m", "end", s)
    check("the header stays at the far end", moved is None, moved)
    yield from click(x, b[1] + MENU_BOTTOM); yield 0.3
    check("the last row can be reached", P["last"] == 79, P)
    yield from wheel(x, mid_y(b), False, 70, 0.04)
    yield from park()
    yield from grab("top")
    n = rdiff("m", "top", b)
    check("all the way back up", n < 30, n)
    # A crop on top of the window's clamp.
    yield from crop(b, 300)
    yield from grab("cropped")
    v = need_box("base", "cropped", "cropped")
    check("the crop applies", abs(height(b) - 300 - height(v)) <= 3, (b, v))
    check("the top stays", abs(v[3] - b[3]) <= 1, (b, v))
    moved = box_bbox("m", "cropped", (b[0] + 2, b[3] - STRIP_MENU, b[0] + 60, b[3] - 1))
    check("and the title too", moved is None, moved)
    c = yield from collapse(v, TITLE_MENU, "col")
    yield from expand(c, "exp")
    w = need_box("base", "exp", "expanded")
    check("the pin brings back the same box", same_box(v, w, 1), (v, w))
    yield from closes(v, TITLE_MENU, "closed")


SC["p8_tall"] = s_p8_tall


# ---------------------------------------------------------------- Phase 8: the scrollbar
def s_p8_scrollbar():
    yield from begin()
    P = SIM_OT_row_probe.state
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    check("fitted while it fits", width(b) < FLOOR, b)
    yield from crop(b, 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    log("cropped", v, "from", b)
    check("the same width when it overflows", v[0] == b[0] and v[2] == b[2], (b, v))
    bar = (b[2] - 13, v[1] + 6, b[2] - 1, v[3] - STRIP_MENU - 4)
    n = color_count("c", bar, (v[0] + 4, mid_y(v)))
    check("the bar shows at rest", n > 20, n)
    line = line_extent("c", v, 28); log("line", line)
    check("the header's line reaches the edge",
          line is not None and line[1] >= v[2] - LINE_GAP, (line, v))
    s = strip_box(v, STRIP_MENU)
    x = v[2] - BAR_X
    runs = P["runs"]
    # The thumb starts at the top of the track.
    y = v[3] - STRIP_MENU - 16
    yield from drag(x, y, 0, -40)
    yield from park()
    yield from grab("d1")
    moved = box_bbox("c", "d1", rows_box((v[0], v[1], b[2], v[3]), STRIP_MENU))
    check("dragging the thumb scrolls", moved is not None, moved)
    check("the header doesn't change", box_bbox("c", "d1", s) is None, box_bbox("c", "d1", s))
    # To the far end.
    yield from drag(x, y - 40, 0, 5 - (y - 40))
    yield from park()
    yield from grab("d2")
    check("dragging the bar ran no row", P["runs"] == runs, P)
    yield from click(mid_x(v), v[1] + MENU_BOTTOM); yield 0.3
    check("the far end shows the last row", P["last"] == 17, P)
    runs = P["runs"]
    yield from park()
    # And back from where the thumb is now.
    y2 = v[1] + 12
    yield from drag(x, y2, 0, 995 - y2)
    yield from park()
    yield from grab("d3")
    n = rdiff("c", "d3", v)
    check("dragging back returns to the start", n < 30, n)
    # A press on the empty track jumps there, and Esc goes back with the release swallowed.
    yield from click(x, y2)
    yield from park()
    yield from grab("jump")
    moved = box_bbox("c", "jump", rows_box((v[0], v[1], b[2], v[3]), STRIP_MENU))
    check("a press on the track jumps", moved is not None, moved)
    yield from drag(x, y2, 0, 995 - y2)
    yield from park()
    yield from grab("d4")
    n = rdiff("c", "d4", v)
    check("back at the start for the next step", n < 30, n)
    yield from grip_cancel(x, y2, x, y2)
    yield from park()
    yield from grab("esc")
    n = rdiff("c", "esc", v)
    check("Esc undoes the jump", n < 30, n)
    check("no press on the bar ran a row", P["runs"] == runs, P)
    # The header follows the gutter.
    c = yield from collapse(v, TITLE_MENU, "col")
    yield from expand(c, "exp")
    w = need_box("base", "exp", "expanded")
    check("the pin brings back the same box", same_box(v, w, 1), (v, w))
    # No crop, no bar and no gutter.
    yield from uncrop(v, 200)
    yield from grab("reset")
    w = popup_box("base", "reset")
    check("back at the natural size", same_box(b, w, 1), (b, w))
    n = rdiff("m", "reset", b)
    check("with nothing of the bar left", n < 30, n)
    yield from closes(b, TITLE_MENU, "closed")


SC["p8_scrollbar"] = s_p8_scrollbar


def s_p8_bar_gutter():
    """The bar sits beside a menu's rows, inside the menu. It must not cover their arrows."""
    yield from begin()
    b = yield from opened(open_menu("SIM_MT_arrows"), "m", "the menu opens")
    yield from crop(b, 150)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    log("cropped", v, "from", b)
    check("the same width when it overflows", v[0] == b[0] and v[2] == b[2], (b, v))
    # Their arrows are the one thing that moves, into the room the bar gave up.
    rows = (b[0] + 2, v[3] - TEAR_ROW0 - ROW * 4, b[2] - 15, v[3] - STRIP_MENU)
    text = (b[0] + 2, rows[1], b[2] - 40, rows[3])
    n = rdiff("m", "c", text)
    check("the rows' text doesn't move", n < 10, n)
    n = color_count("c", (b[2] - 13, v[1] + 6, b[2] - 1, v[3] - STRIP_MENU - 4),
                    (v[0] + 4, v[1] + 12))
    check("the bar shows at rest", n > 20, n)
    # Hovered it's at its widest, and must still stay out of them. On the bar and not beside it,
    # because a row with a submenu can open by itself when hovered, right over the bar.
    x, y = v[2] - BAR_X, mid_y(rows)
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    yield from grab("wide")
    n = rdiff("c", "wide", rows)
    check("the widest bar stays out of the rows and their arrows", n < 10, n)
    gutter = (b[2] - 14, v[1] + 6, v[2], v[3] - STRIP_MENU - 4)
    log("the bar widened by", rdiff("c", "wide", gutter))
    yield from park()
    yield from closes(v, TITLE_MENU, "closed")


SC["p8_bar_gutter"] = s_p8_bar_gutter


def s_p8_panel_bar():
    """A panel gets no gutter, so its bar fits in its margin and leaves the fields alone."""
    st = SIM_PT_fields.state
    sc = bpy.context.scene
    th = bpy.context.preferences.themes[0]
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_fields"), "m", "the fields open")
    yield from crop(b, height(b) - 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    check("no gutter on a panel", abs(width(v) - width(b)) <= 1, (b, v))
    n = color_count("c", (v[2] - 9, v[1] + 8, v[2] - 3, v[3] - STRIP_PANEL - 6),
                    (v[0] + 4, mid_y(v)))
    check("the bar shows at rest", n > 20, n)
    # The arrow of a field that fills the row, 12 in from the edge and beside the bar.
    y = v[3] - PANEL_ROW0
    was = sc.sim_values[0]
    yield from click(v[2] - 12, y); yield 0.3
    check("the field's arrow still works", sc.sim_values[0] == was + 1, sc.sim_values[0])
    yield from park()
    yield from grab("stepped")
    # The bar itself.
    x = v[2] - BAR_X
    y = v[3] - STRIP_PANEL - 14
    yield from drag(x, y, 0, -40)
    yield from park()
    yield from grab("d1")
    moved = box_bbox("stepped", "d1", rows_box(v, STRIP_PANEL))
    check("dragging the thumb scrolls", moved is not None, moved)
    s = strip_box(v, STRIP_PANEL)
    check("the header doesn't change", box_bbox("stepped", "d1", s) is None,
          box_bbox("stepped", "d1", s))
    # A theme whose bar is transparent takes another branch, as in view2d_scrollers_draw.
    ui = th.user_interface.wcol_scroll
    inner = tuple(ui.inner)
    ui.inner = (inner[0], inner[1], inner[2], 0.0)
    area_redraw(); yield 0.4
    move(x, mid_y(v)); yield 0.3
    move(x, mid_y(v)); yield 0.3
    yield from grab("clear_theme")
    ui.inner = inner
    yield from park()
    # Only in the free box, because this color reaches every region's own scrollbars.
    w = torn_box("base", "clear_theme")
    check("it stays whole with a transparent theme", same_box(v, w, 1), (v, w))
    # The width grip gave way to the bar, and works from outside.
    yield from drag(v[2] + 2, mid_y(v), 60, 0)
    yield from park()
    yield from grab("wider")
    w = need(popup_box("base", "wider"), "wider")
    check("the width grip still works beside the bar", abs(width(w) - width(v) - 60) <= 2, (v, w))


SC["p8_panel_bar"] = s_p8_panel_bar


# ---------------------------------------------------------------- Phase 8: everything else
def regular_round(tag, a, strip_h, at=None):
    """A regular popup with box a is open, and stays open: moving out of it would close it, so the
    cursor stays on it and its row highlights in all of these frames. The cursor goes to `at` when
    given, and the reference shots have to be recorded with the same."""
    x, y = at or (mid_x(a), mid_y(a))
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    yield from grab(tag + "hover")
    ref_check(tag + "hover", a)
    win().event_simulate(type="WHEELDOWNMOUSE", value="PRESS", x=x, y=y); yield 0.2
    for _ in range(4):
        win().event_simulate(type="WHEELDOWNMOUSE", value="PRESS", x=x, y=y); yield 0.2
    yield 0.3
    yield from grab(tag + "down")
    ref_check(tag + "down", a)
    s = strip_box(a, strip_h)
    moved = box_bbox(tag + "hover", tag + "down", s)
    check(tag + ": its top scrolls away, as upstream", moved is not None, moved)
    # A menu's rows reach this strip and its lit row moves, so only #ref_check speaks for it.
    if strip_h == STRIP_PANEL:
        bar = (a[2] - 9, a[1] + 30, a[2] - 2, a[3] - 40)
        moved = box_bbox(tag + "hover", tag + "down", bar)
        check(tag + ": it has no scrollbar", moved is None, moved)
    for _ in range(5):
        win().event_simulate(type="WHEELUPMOUSE", value="PRESS", x=x, y=y); yield 0.2
    yield 0.3
    yield from grab(tag + "up")
    n = rdiff(tag + "hover", tag + "up", a)
    # The same in a build without these phases: a menu's lit row can change with the wheel.
    check(tag + ": and returns", strip_h == STRIP_MENU or n < 30, n)


def s_p8_regular():
    st = SIM_PT_tall.state
    yield from begin(st)
    move(*center()); yield 0.3
    call_menu("SIM_MT_tall"); yield 0.8
    yield from grab("att")
    a = need(popup_box("base", "att"), "the attached menu opens")
    check("the window clamps it", height(a) > 900, a)
    ref_check("att", a)
    # Beside the menu, as in the reference shots: a row under the cursor lights up after the wheel.
    yield from regular_round("menu_", a, STRIP_MENU, (354, 496))
    yield from dismiss()
    move(*center()); yield 0.3
    call_panel("SIM_PT_tall"); yield 0.8
    yield from grab("pop")
    p = need_box("base", "pop", "the popover opens")
    check("the window clamps it too", height(p) > 900, p)
    ref_check("pop", p)
    yield from regular_round("pop_", p, STRIP_PANEL)
    yield from dismiss()


SC["p8_regular"] = s_p8_regular


def s_p8_scale():
    """The offsets at 150%. A region's aspect is 1 either way, but the units aren't."""
    S = 1.5
    st = SIM_PT_mid.state
    yield from setup()
    prefs = bpy.context.preferences
    prefs.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    st["show"] = True
    prefs.view.ui_scale = S; yield 1.5
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("base")
    P = SIM_OT_row_probe.state

    def scaled_round(tag, b, strip_h):
        s = strip_box(b, int(strip_h * S))
        check(tag + ": the header shows", ink(tag + "m", s) is not None, ink(tag + "m", s))
        yield from crop(b, 150)
        yield from grab(tag + "c")
        v = need_box("base", tag + "c", tag + ": cropped")
        check(tag + ": shorter by the drag", abs(height(b) - 150 - height(v)) <= 3, (b, v))
        x, y = mid_x(v), mid_y(v)
        yield from wheel(x, y, True, 3)
        yield from park()
        yield from grab(tag + "w")
        check(tag + ": the wheel doesn't touch the header",
              box_bbox(tag + "c", tag + "w", s) is None, box_bbox(tag + "c", tag + "w", s))
        check(tag + ": it moves the content",
              box_bbox(tag + "c", tag + "w", rows_box(v, int(strip_h * S))) is not None, tag)
        yield from click(x, y); yield 0.3
        check(tag + ": a row clicks", P["runs"] > 0, P)
        P["runs"] = 0
        yield from wheel(x, y, False, 3)
        yield from park()
        yield from grab(tag + "u")
        n = rdiff(tag + "c", tag + "u", v)
        check(tag + ": and returns", n < 30, n)
        yield from uncrop(v, 150)
        yield from grab(tag + "back")
        # Not popup_box: at this scale the block reaches below it.
        w = bbox("base", tag + "back")
        check(tag + ": the crop can go", same_box(b, w, 1), (b, w))

    b = yield from opened(open_menu("SIM_MT_mid"), "menu_m", "the menu opens")
    yield from scaled_round("menu_", b, STRIP_MENU)
    yield from close_all()
    yield from park()
    b = yield from opened(open_tpanel("SIM_PT_mid"), "panel_m", "the panel opens")
    yield from scaled_round("panel_", b, STRIP_PANEL)
    prefs.view.ui_scale = 1.0; yield 1.0


SC["p8_scale"] = s_p8_scale


def s_p8_top_band():
    """At 200% a title drag stops 10 px higher than the popup clip allows. The next refresh has to
    move the block down, because trimming it would invent a scroll range and a menu's gutter."""
    S = 2.0
    yield from setup()
    prefs = bpy.context.preferences
    prefs.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    prefs.view.ui_scale = S; yield 1.5
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("base")
    n_draws = lambda: SIM_MT_short.state["draws"]
    b = yield from opened(open_menu("SIM_MT_short"), "m", "the menu opens")
    title_y = int(TITLE_MENU * S)
    yield from title_drag(b, title_y, 0, 999 - (b[3] - title_y))
    yield from grab("dragged")
    around = (max(b[0] - 60, 0), 400, min(b[2] + 60, 1599), 999)
    d = need(box_bbox("base", "dragged", around), "the menu moved up")
    log("dragged", d, "from", b)
    n0 = n_draws()
    bpy.context.scene.frame_current += 1; yield 1.0
    yield from park()
    yield from grab("refreshed")
    check("the frame change did refresh it", n_draws() > n0, (n0, n_draws()))
    r = need(box_bbox("base", "refreshed", around), "the menu after the refresh")
    log("refreshed", r)
    check("it keeps its height", abs(height(r) - height(b)) <= 1, (b, r))
    check("no gutter", abs(width(r) - width(b)) <= 1, (b, r))
    # It fits, so there is nothing to scroll.
    yield from wheel(mid_x(r), mid_y(r), True, 3)
    yield from park()
    yield from grab("wheeled")
    n = rdiff("refreshed", "wheeled", r)
    check("the wheel has nothing to scroll", n < 30, n)
    prefs.view.ui_scale = 1.0; yield 1.0


SC["p8_top_band"] = s_p8_top_band


def s_p8_shadow_band():
    """The theme's shadow margin belongs to the editor under a tear-off, so hovering it at the height
    of an arrow zone doesn't start the auto-scroll. The default theme's width is 0."""
    yield from begin()
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    ui = bpy.context.preferences.themes[0].user_interface
    ui.menu_shadow_width = 12
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("shadow")
    rows = rows_box(v, STRIP_MENU)
    x, y = v[0] - 4, v[1] + 6
    move(x, y); yield 0.3
    move(x, y); yield 1.2
    yield from park()
    yield from grab("beside")
    n = rdiff("shadow", "beside", rows)
    check("beside the block nothing scrolls", n < 30, n)
    # The baseline: a click on the arrow itself does scroll.
    x = mid_x(v)
    yield from click(x, y)
    yield from park()
    yield from grab("inside")
    n = rdiff("beside", "inside", rows)
    check("a click on the arrow scrolls", n > 100, n)
    ui.menu_shadow_width = 0


SC["p8_shadow_band"] = s_p8_shadow_band





def s_p8_fractional_crop():
    """125% makes the arrow zones, so the smallest crop, end on half a pixel. A wheel step's point
    is clamped to the block's bottom, which has to stay inside it."""
    S = 1.25
    yield from setup()
    prefs = bpy.context.preferences
    prefs.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    prefs.view.ui_scale = S; yield 1.5
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("base")
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, height(b))
    yield from grab("c")
    v = need_box("base", "c", "cropped to the minimum")
    log("minimum", v, "from", b)
    yield from wheel(mid_x(v), mid_y(v), True, 3)
    yield from park()
    yield from grab("w")
    n = rdiff("c", "w", rows_box(v, int(STRIP_MENU * S)))
    check("the wheel scrolls down", n > 20, n)
    prefs.view.ui_scale = 1.0; yield 1.0


SC["p8_fractional_crop"] = s_p8_fractional_crop


def s_p8_status_after_grip():
    """A grip drag that crosses another region. The status bar shows what's under the cursor, so it
    has to follow once the cursor is back over the viewport."""
    st = SIM_PT_mid.state
    yield from begin(st)
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    def ink_of(name):
        return int((FRAME[name][4:18, 0:700].max(axis=2) > 0.25).sum())
    base_ink = ink_of("m")
    log("status ink at rest", base_ink)
    yield from crop(b, 200)
    yield from grab("c")
    v = need(popup_box("base", "c"), "cropped")
    yield from uncrop(v, 200)
    yield from grab("st")
    log("right after, parked", ink_of("st"))
    move(PARK[0] + 40, PARK[1] + 40); yield 0.3
    yield from grab("st2")
    log("after one move in the viewport", ink_of("st2"))
    move(PARK[0] + 80, PARK[1] + 80); yield 0.3
    yield from grab("st3")
    log("after a second", ink_of("st3"))
    check("the status bar follows the cursor again", abs(ink_of("st3") - base_ink) < 20,
          (base_ink, ink_of("st"), ink_of("st2"), ink_of("st3")))


SC["p8_status_after_grip"] = s_p8_status_after_grip


def ctrl_click(x, y):
    move(x, y); yield W
    move(x, y); yield W
    win().event_simulate(type="LEFT_CTRL", value="PRESS", x=x, y=y); yield 0.05
    win().event_simulate(type="LEFTMOUSE", value="PRESS", x=x, y=y, ctrl=True); yield 0.05
    win().event_simulate(type="LEFTMOUSE", value="RELEASE", x=x, y=y, ctrl=True); yield 0.05
    win().event_simulate(type="LEFT_CTRL", value="RELEASE", x=x, y=y); yield 0.4


def s_regress_final():
    """The plan's last pass: what shares this code and has no tear-off of its own still works, with
    a clipped tear-off open beside it."""
    st = SIM_PT_mid.state
    yield from begin(st)
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the tear-off opens")
    yield from title_drag(b, TITLE_MENU, 300, 200)
    yield from crop((b[0] + 300, b[1] + 200, b[2] + 300, b[3] + 200), 200)
    yield from grab("torn")
    v = need(popup_box("base", "torn"), "the tear-off moved and cropped")

    # A pie menu.
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.call_menu_pie(name="VIEW3D_MT_shading_pie")
    yield 0.8
    yield from grab("pie")
    n = rdiff("torn", "pie", VIEW)
    check("a pie menu opens", n > 500, n)
    n = rdiff("torn", "pie", v)
    check("the tear-off doesn't change under it", n < 400, n)
    yield from esc(); yield 0.4
    yield from park()
    yield from grab("pie_closed")
    n = rdiff("torn", "pie_closed", VIEW)
    check("Esc closes the pie", n < 30, n)

    # The search popup.
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.search_menu("INVOKE_DEFAULT")
    yield 0.8
    yield from grab("search")
    n = rdiff("torn", "search", VIEW)
    check("the search popup opens", n > 500, n)
    x, y = center()
    yield from type_key("C", x, y, "c"); yield 0.5
    yield from grab("typed")
    n = rdiff("search", "typed", VIEW)
    check("it takes typing", n > 50, n)
    n = rdiff("torn", "typed", v)
    check("the tear-off doesn't take the key", n < 400, n)
    yield from esc(); yield 0.4
    yield from esc(); yield 0.4
    yield from park()
    yield from grab("search_closed")
    n = rdiff("torn", "search_closed", VIEW)
    check("Esc closes the search", n < 30, n)

    # Ctrl+click on a panel header keeps only that panel open.
    r = region_of(area(), "UI")
    before = (r.x, r.y, r.x + r.width - 1, r.y + r.height - 1)
    # An open panel with subpanels toggles those instead, so from a closed one.
    yield from click(r.x + 60, 1000 - 193); yield 0.3
    yield from park()
    yield from grab("closed_one")
    yield from ctrl_click(r.x + 60, 1000 - 193)
    yield from park()
    yield from grab("ctrl")
    n = rdiff("closed_one", "ctrl", before)
    check("Ctrl+click on a header collapses the others", n > 200, n)
    n = rdiff("search_closed", "ctrl", v)
    check("the tear-off stays as it was", n < 30, n)
    yield from closes(v, TITLE_MENU, "closed")


SC["regress_final"] = s_regress_final


# ---------------------------------------------------------------- feedback round after phase 8
def row_y_menu(a):
    """The Tear Off row of a menu with a title and box a. Pressing the title would drag the menu."""
    return a[3] - TEAR_ROW0


def row_y_popover(a):
    """The Tear Off row of an attached popover with box a, which has no title above it."""
    return a[3] - 17


def carried(start, end, frame, what):
    """Press a Tear Off row, move in steps and hold. Returns the frame's box."""
    x, y = start
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.1
    tx, ty = end
    for i in range(1, 9):
        move(x + (tx - x) * i // 8, y + (ty - y) * i // 8); yield 0.08
    yield from grab(frame)
    return need(popup_box("base", frame), what)


def row_carry_round(tag, open_popup, opened_what, row_y):
    yield from open_popup()
    yield from grab(tag + "att")
    a = need(popup_box("base", tag + "att"), opened_what)
    log(tag, "attached", a)
    row = (a[0] + 60, row_y(a))
    # Away from the attached popup, so the frames can't overlap.
    end = (1000, 300)
    v = yield from carried(row, end, tag + "held", "held: " + tag)
    log(tag, "held", v)
    check(tag + ": the source closed and it follows the cursor",
          v[0] > a[2] - 40 or v[1] > a[3] or v[3] < a[1], (a, v))
    check(tag + ": it's near the cursor",
          v[0] - 40 <= end[0] <= v[2] + 40 and v[1] - 40 <= end[1] <= v[3] + 40, (end, v))
    # Still attached to the cursor while the button is held.
    move(end[0] + 60, end[1] + 40); yield 0.15
    move(end[0] + 60, end[1] + 40); yield 0.15
    yield from grab(tag + "held2")
    w = need(popup_box("base", tag + "held2"), "held further: " + tag)
    check(tag + ": a further move carries it",
          abs(w[0] - v[0] - 60) <= 2 and abs(w[3] - v[3] - 40) <= 2, (v, w))
    release(end[0] + 60, end[1] + 40); yield 0.4
    yield from park()
    yield from grab(tag + "landed")
    x = need(popup_box("base", tag + "landed"), "landed: " + tag)
    check(tag + ": it stays where it was released", same_box(w, x, 2), (w, x))
    move(end[0] + 200, end[1]); yield 0.2
    yield from park()
    yield from grab(tag + "after")
    n = rdiff(tag + "landed", tag + "after", VIEW)
    check(tag + ": the release ended the carry", n < 30, n)
    return x


def s_p9_row_drag():
    """A drag on the Tear Off row carries the new tear-off, in a menu and a popover."""
    SIM_PT_small.state["show"] = True
    yield from begin()

    def menu():
        move(*center()); yield 0.3
        call_menu("SIM_MT_short"); yield 0.8
    v = yield from row_carry_round("menu_", menu, "the menu opens", row_y_menu)
    check("menu_: it is a tear-off, with no row to tear off from", height(v) < 123, v)
    yield from close_all()
    yield from park()

    def panel():
        move(*center()); yield 0.3
        call_panel("SIM_PT_small"); yield 0.8
    v = yield from row_carry_round("panel_", panel, "the popover opens", row_y_popover)
    yield from close_all()
    yield from park()

    # A plain click still tears off.
    move(*center()); yield 0.3
    call_menu("SIM_MT_short"); yield 0.8
    yield from grab("click_att")
    a = need(popup_box("base", "click_att"), "the menu opens for a click")
    yield from click(a[0] + 60, row_y_menu(a)); yield 0.4
    yield from park()
    yield from grab("click_torn")
    v = need(popup_box("base", "click_torn"), "a click tears off")
    check("a click makes a tear-off", height(v) > 40, v)
    yield from park()
    yield from grab("click_after")
    n = rdiff("click_torn", "click_after", VIEW)
    check("a click carries nothing", n < 30, n)
    yield from close_all()


SC["p9_row_drag"] = s_p9_row_drag


def s_p9_row_drag_small():
    """A move below the threshold is still a click."""
    yield from begin()
    move(*center()); yield 0.3
    call_menu("SIM_MT_short"); yield 0.8
    yield from grab("att")
    a = need(popup_box("base", "att"), "the menu opens")
    x, y = a[0] + 60, row_y_menu(a)
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.1
    move(x + 1, y); yield 0.1
    release(x + 1, y); yield 0.4
    yield from park()
    yield from grab("torn")
    v = need(popup_box("base", "torn"), "a small move is a click")
    log("torn", v)
    yield from park()
    yield from grab("torn2")
    n = rdiff("torn", "torn2", VIEW)
    check("it isn't carried", n < 30, n)
    yield from close_all()


SC["p9_row_drag_small"] = s_p9_row_drag_small


def s_p9_shelf_selector():
    """The asset shelf's Catalog Selector, torn off from its real popover row, keeps its content."""
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="SCULPT")
    yield 1.5
    area().spaces.active.overlay.show_text = False
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("base")
    h = region_of(area(), "ASSET_SHELF_HEADER")
    yield from click(33, h.y + h.height // 2); yield 0.8
    yield from park()
    yield from grab("att")
    a = need(box_bbox("base", "att", (5, 140, 1100, 850)), "the popover opens")
    check("the attached one has its content", height(a) > 150, a)
    yield from click(a[0] + 90, row_y_popover(a)); yield 0.8
    yield from park()
    yield from grab("torn")
    v = need(box_bbox("base", "torn", (5, 140, 1100, 850)), "it tears off")
    log("torn", v, "from", a)
    check("the torn-off one keeps its content", height(v) > 150, v)
    # A redraw from a toggle in its tree, and another from the shelf.
    yield from click(v[2] - 33, v[1] + 22); yield 0.6
    yield from park()
    yield from grab("toggled")
    w = need(box_bbox("base", "toggled", (5, 140, 1100, 850)), "still there after a toggle")
    check("the content stays after a toggle", height(w) > 150, w)
    move(300, 60); yield 0.5
    yield from park()
    yield from grab("hovered")
    w = need(box_bbox("base", "hovered", (5, 140, 1100, 850)), "still there after the shelf redraws")
    check("the content stays after the shelf redraws", height(w) > 150, w)
    yield from close_all()


SC["p9_shelf_selector"] = s_p9_shelf_selector





def s_p9_width_min():
    """The grip goes down to what the content needs, and no further. No dead space beside it."""
    SIM_PT_small.state["show"] = True
    SIM_PT_mid.state["show"] = True
    yield from begin()
    b = yield from opened(open_tpanel("SIM_PT_small"), "s", "the panel opens")
    log("small panel", b)
    check("it hugs its layout, narrower than the popup minimum", width(b) < FLOOR, b)
    yield from close_all()
    yield from park()
    b = yield from opened(open_tpanel("SIM_PT_mid"), "m", "the mid panel opens")
    log("mid panel", b)
    y = mid_y(b)
    yield from drag(b[2] + 2, y, -400, 0)
    yield from park()
    yield from grab("min")
    v = need_box("base", "min", "dragged left")
    log("at the minimum", v)
    check("it can go narrower than designed", width(v) < width(b) - 20, (b, v))
    check("the left edge stays", abs(v[0] - b[0]) <= 1, (b, v))
    check("it stops before nothing is left", width(v) > 60, v)
    yield from drag(v[2] + 2, y, -100, 0)
    yield from park()
    yield from grab("min2")
    w = need_box("base", "min2", "dragged again")
    check("a second drag stops at the same place", same_box(v, w, 1), (v, w))
    # The way back to the designed width lands exactly on it.
    yield from drag(w[2] + 2, y, b[2] - w[2], 0)
    yield from park()
    yield from grab("reset")
    x = need_box("base", "reset", "reset")
    check("dragging back returns to the designed width", same_box(b, x, 2), (b, x))
    yield from drag(x[2] + 2, y, 60, 0)
    yield from park()
    yield from grab("wide")
    x2 = need_box("base", "wide", "widened")
    check("it can still go wider", abs(width(x2) - width(b) - 60) <= 3, (b, x2))
    yield from close_all()


SC["p9_width_min"] = s_p9_width_min


def s_p9_gutter_solid():
    """A menu's width never changes with the crop. The bar appears inside."""
    yield from begin()
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    log("full", b)
    for by in (5, 40, 150):
        yield from crop(b, by)
        yield from grab(f"c{by}")
        v = need_box("base", f"c{by}", "cropped")
        check(f"by {by}: the same width", v[0] == b[0] and v[2] == b[2], (b, v))
        title = (b[0] + 2, v[3] - STRIP_MENU, b[2] - 2, v[3] - 2)
        n = rdiff("m", f"c{by}", title)
        check(f"by {by}: the header doesn't move", n < 5, n)
        yield from uncrop(v, by)
        yield from grab(f"r{by}")
        w = need(popup_box("base", f"r{by}"), "reset")
        check(f"by {by}: and back to the same box", same_box(b, w, 1), (b, w))
    yield from close_all()


SC["p9_gutter_solid"] = s_p9_gutter_solid


class SIM_PT_root_items(bpy.types.Panel):
    """Items placed straight on a panel's layout, whose result depends on the layout's direction."""
    bl_idname = "SIM_PT_root_items"; bl_label = "Sim Root Items"
    bl_space_type = "VIEW_3D"; bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.render.image_settings, "color_mode", expand=True)
        layout.prop(context.object, "location", index=-1, icon_only=True)
        layout.prop(context.scene, "frame_current")


bpy.utils.register_class(SIM_PT_root_items)


def attached_vs_torn(name, tag, rt="HEADER", t="VIEW_3D"):
    """Open a panel attached and torn off. Returns their boxes, or None if it can't open here. Both
    at the viewport's center, so a tall one isn't trimmed by the bottom of the window."""
    cx, cy = center()
    at = (cx, cy + 250)
    move(*at); yield 0.3
    move(*at); yield 0.3
    try:
        with bpy.context.temp_override(**override(t, rt)):
            bpy.ops.wm.call_panel(name=name, keep_open=True)
    except Exception as ex:
        log(tag, "can't open", str(ex)[:80])
        return None
    yield 0.8
    yield from grab(tag + "a")
    a = popup_box("base", tag + "a")
    yield from dismiss()
    move(*at); yield 0.3
    move(*at); yield 0.3
    with bpy.context.temp_override(**override(t, rt)):
        bpy.ops.wm.panel_tear_off(panel_idname=name)
    yield 0.8
    yield from park()
    yield from grab(tag + "t")
    t = popup_box("base", tag + "t")
    yield from close_all()
    yield from park()
    return a, t


def s_p9_root_items():
    """The panel's items keep their arrangement when torn off."""
    yield from begin()
    r = yield from attached_vs_torn("SIM_PT_root_items", "root_")
    a, t = need(r, "it opens")
    log("attached", a, "torn", t)
    # The row of the attached popover and the header of the tear-off are within a few pixels.
    check("the same arrangement", abs(height(a) - height(t)) <= 14, (a, t))


SC["p9_root_items"] = s_p9_root_items


def s_p9_popover_sweep():
    """Every real popover of the 3D View header stays the same height when torn off. One that
    stacks a row or loses its content would be off by more than the header's difference."""
    yield from begin()
    names = ("VIEW3D_PT_overlay", "VIEW3D_PT_shading", "VIEW3D_PT_object_type_visibility",
             "VIEW3D_PT_gizmo_display", "VIEW3D_PT_snapping", "VIEW3D_PT_proportional_edit",
             "VIEW3D_PT_transform_orientations", "VIEW3D_PT_pivot_point", "VIEW3D_PT_collections",
             "VIEW3D_PT_grease_pencil_origin", "VIEW3D_PT_sculpt_dyntopo")
    seen = 0
    for name in names:
        r = yield from attached_vs_torn(name, name + "_")
        if r is None or r[0] is None or r[1] is None:
            log(name, "skipped", r)
            continue
        a, t = r
        seen += 1
        log(name, "attached", a, "torn", t)
        check(name + ": the same height when torn off", abs(height(a) - height(t)) <= 14, (a, t))
    check("most of them could open", seen >= 5, seen)


SC["p9_popover_sweep"] = s_p9_popover_sweep


def s_p9_asset_display():
    """The report: the Asset Browser's Display Settings, with Tiny to Large in one row."""
    props = area("PROPERTIES")
    props.ui_type = "ASSETS"
    yield 1.5
    yield from begin()
    r = yield from attached_vs_torn("ASSETBROWSER_PT_display", "disp_", t="FILE_BROWSER")
    a, t = need(r, "it opens")
    log("attached", a, "torn", t)
    check("the row stays a row when torn off", abs(height(a) - height(t)) <= 14, (a, t))


SC["p9_asset_display"] = s_p9_asset_display


class SIM_PT_left_row(bpy.types.Panel):
    """Short rows, and one row sized to its text: that row doesn't narrow with the panel."""
    bl_idname = "SIM_PT_left_row"; bl_label = "Sim Left Row"
    bl_space_type = "VIEW_3D"; bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(context.scene.render, "use_border", text="Border")
        layout.label(text="Short")
        layout.operator("wm.redraw_timer", text="Run")


class SIM_PT_hdr_plain(bpy.types.Panel):
    bl_idname = "SIM_PT_hdr_plain"; bl_label = "Sim Long Header Title"
    bl_space_type = "VIEW_3D"; bl_region_type = "HEADER"
    bl_ui_units_x = 4

    def draw(self, context):
        self.layout.label(text="a")


class SIM_PT_hdr_check(bpy.types.Panel):
    bl_idname = "SIM_PT_hdr_check"; bl_label = "Sim Long Header Title"
    bl_space_type = "VIEW_3D"; bl_region_type = "HEADER"
    bl_ui_units_x = 4

    def draw_header(self, context):
        self.layout.prop(context.scene.render, "use_border", text="")

    def draw(self, context):
        self.layout.label(text="a")


for sim_cls in (SIM_PT_left_row, SIM_PT_hdr_plain, SIM_PT_hdr_check):
    bpy.utils.register_class(sim_cls)


def s_p9_flick():
    """A fast drag from a popover's row, onto the neighbouring header dropdown. The neighbour must
    not open, and the carry must end at the release."""
    yield from begin()
    # The Shading dropdown, then the Overlays dropdown beside it.
    shading, overlays = (1156, 933), (1028, 933)
    yield from click(*shading); yield 0.8
    yield from park_over_nothing()
    yield from grab("att")
    a = need(popup_box("base", "att"), "the popover opens")
    log("attached", a)
    # The box reaches up to the lit header button. The row is under the popover's arrow.
    x, y = a[0] + 90, 895
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.1
    # Both moves reach the queue before the tear-off's synthetic move, as in a real flick.
    move(x, y + 6)
    move(*overlays)
    yield 0.5
    move(*overlays); yield 0.3
    yield from grab("flicked")
    release(*overlays); yield 0.5
    yield from park()
    yield from grab("released")
    t = popup_box("base", "released")
    log("released", t)
    yield from park()
    move(PARK[0] + 200, PARK[1] + 100); yield 0.2
    yield from park()
    yield from grab("after")
    n = rdiff("released", "after", VIEW)
    check("the release ended the carry", n < 30, n)
    move(*center()); yield 0.3
    yield from close_all()
    yield from esc(); yield 0.3
    yield from park()
    yield from grab("end")
    n = rdiff("base", "end", (30, 140, 1100, 850))
    check("nothing is left open", n < 300, n)


SC["p9_flick"] = s_p9_flick


def park_over_nothing():
    """Beside the popover, with no hover switch: over the viewport."""
    yield from park()


def s_p9_row_memory():
    """Tearing off doesn't become what a popup menu remembers. It would reopen on the Tear Off row."""
    yield from begin()

    def opened_at(name):
        move(*center()); yield 0.3
        move(*center()); yield 0.3
        call_menu("SIM_MT_short"); yield 0.8
        yield from grab(name)
        return need(popup_box("base", name), "the menu opens: " + name)
    a = yield from opened_at("first")
    # Remember the last row, which is what makes the menu open somewhere else.
    yield from click(a[0] + 60, a[1] + 16); yield 0.5
    yield from park()
    b = yield from opened_at("again")
    check("the baseline: it reopens on the remembered row", abs(b[3] - a[3]) > 10, (a, b))
    yield from click(b[0] + 60, b[3] - TEAR_ROW0); yield 0.6
    yield from park()
    yield from close_all()
    yield from park()
    c = yield from opened_at("after")
    check("it still reopens on that row, not the Tear Off row", same_box(b, c, 1), (b, c))
    yield from dismiss()


SC["p9_row_memory"] = s_p9_row_memory


def grip_to_min(name, tag):
    """Tear off a panel, drag its grip far left. Returns the box before and after."""
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override("VIEW_3D", "HEADER")):
        bpy.ops.wm.panel_tear_off(panel_idname=name)
    yield 0.8
    yield from park()
    yield from grab(tag + "o")
    b = need(popup_box("base", tag + "o"), "it opens: " + name)
    yield from drag(b[2] + 2, mid_y(b), -500, 0)
    yield from park()
    yield from grab(tag + "m")
    v = need(popup_box("base", tag + "m"), "after the drag: " + name)
    log(name, "opens", b, "minimum", v)
    return b, v


def s_p9_width_text_sized():
    """A row sized to its text doesn't scale with the panel, and must not stop the grip."""
    yield from begin()
    b, v = yield from grip_to_min("SIM_PT_left_row", "left_")
    check("a text-sized row doesn't stop the grip", width(v) < width(b) - 20, (b, v))
    # It's still a limit, at its own width: a checkbox and "Border" are about 70 wide.
    check("and its text still fits", width(v) >= 70, v)
    yield from close_all()
    yield from park()
    b1, v1 = yield from grip_to_min("SIM_PT_hdr_plain", "plain_")
    yield from close_all()
    yield from park()
    b2, v2 = yield from grip_to_min("SIM_PT_hdr_check", "check_")
    yield from close_all()
    check("the header's checkbox gets its room at the opening width",
          width(b2) >= width(b1) + 18, (b1, b2))
    check("and at the minimum", width(v2) >= width(v1) + 18, (v1, v2))


SC["p9_width_text_sized"] = s_p9_width_text_sized


class SIM_PT_long_row(bpy.types.Panel):
    """A text-sized row longer than the panel, as with a long collection name. It clips anyway."""
    bl_idname = "SIM_PT_long_row"; bl_label = "Sim Long Row"
    bl_space_type = "VIEW_3D"; bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        row.operator("wm.redraw_timer", text="A very long name in a row sized to its own text, past the panel")
        layout.operator("wm.redraw_timer", text="Run")


bpy.utils.register_class(SIM_PT_long_row)


def s_p9_width_clipped():
    """Clipped text doesn't stop the grip. Pressing again at the stop doesn't move the edge."""
    yield from begin()
    b, v = yield from grip_to_min("SIM_PT_long_row", "long_")
    check("a clipped text-sized row doesn't stop the grip", width(v) < width(b) - 20, (b, v))
    # Again at the stop, one pixel in and the edge stays. Measured from a held frame, as a jump
    # shows on the first move and a release wouldn't bring it back anyway.
    x, y = v[2] + 2, mid_y(v)
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.1
    move(x - 3, y); yield 0.2
    move(x - 3, y); yield 0.2
    yield from grab("regrab")
    release(x - 3, y); yield 0.4
    w = need(popup_box("base", "regrab"), "pressed again")
    check("pressing at the stop doesn't push the edge out", w[2] <= v[2], (v, w))
    yield from close_all()


SC["p9_width_clipped"] = s_p9_width_clipped


def s_p9_prefs_margins():
    """A torn-off Preferences panel has no centering margins, and doesn't follow the window."""
    props = area("PROPERTIES")
    props.ui_type = "PREFERENCES"
    yield 1.5
    bpy.context.preferences.active_section = "INTERFACE"
    area_redraw(); yield 1.0
    yield from begin()
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override("PREFERENCES", "WINDOW")):
        bpy.ops.wm.panel_tear_off(panel_idname="USERPREF_PT_interface_display", from_region_panel=True)
    yield 1.0
    yield from park()
    yield from grab("torn")
    v = need(popup_box("base", "torn"), "it tears off")
    log("torn", v)
    # Fields reach the right margin: something other than the panel color near the right edge.
    px = FRAME["torn"][v[1] + 10:v[3] - 40, v[2] - 16]
    bg = FRAME["torn"][v[1] + 6, v[0] + 6]
    n = int((np.abs(px - bg).max(axis=1) > 0.04).sum())
    check("its fields reach the right edge", n > 15, n)
    yield from close_all()


SC["p9_prefs_margins"] = s_p9_prefs_margins


def s_p9_child_preset():
    """A child panel's preset button shows in a torn-off parent."""
    props = area("PROPERTIES")
    props.spaces.active.context = "RENDER"
    bpy.context.scene.view_settings.use_white_balance = True
    yield 1.0
    yield from begin()
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override("PROPERTIES", "WINDOW")):
        bpy.ops.wm.panel_tear_off(panel_idname="RENDER_PT_color_management", from_region_panel=True)
    yield 1.0
    yield from park()
    yield from grab("torn")
    v = need(popup_box("base", "torn"), "it tears off")
    log("torn", v)
    check("it opens", height(v) > 60, v)
    yield from close_all()


SC["p9_child_preset"] = s_p9_child_preset


def s_p9_shortcut_popover():
    """The asset shelf popover opened by shortcut has no Tear Off row: it couldn't redraw."""
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="SCULPT")
    yield 1.5
    area().spaces.active.overlay.show_text = False
    area_redraw(); yield 0.6
    # The same cursor position in both frames, or the brush circle is in the difference.
    at = center()
    move(*at); yield 0.3
    move(*at); yield 0.3
    yield from grab("base")
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.call_asset_shelf_popover("INVOKE_DEFAULT", name="VIEW3D_AST_brush_sculpt")
    yield 1.5
    yield from grab("open")
    a = popup_box("base", "open")
    log("open", a)
    check("it opens", a is not None and height(a) > 100, a)
    yield from dismiss()


SC["p9_shortcut_popover"] = s_p9_shortcut_popover


def tear_props(name, tab):
    props = area("PROPERTIES")
    props.spaces.active.context = tab
    area_redraw(); yield 0.5
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override("PROPERTIES", "WINDOW")):
        bpy.ops.wm.panel_tear_off(panel_idname=name, from_region_panel=True)
    yield 1.0


def s_p10_looks():
    """What is torn off keeps the look it had: panel colors, popup color, menu color."""
    th = bpy.context.preferences.themes[0]
    SIM_PT_tear.state["show"] = True
    SIM_PT_small.state["show"] = True
    yield from begin()
    # A popover through its row keeps the popup color.
    p = yield from opened(open_tpanel("SIM_PT_small"), "pop", "the popover opens")
    popup_col = FRAME["pop"][p[1] + 8, p[0] + 6]
    yield from close_all()
    yield from park()
    # A panel from the region has a header color, and another color below it.
    yield from tear_center("SIM_PT_tear")
    yield from park()
    yield from grab("reg")
    v = need(popup_box("base", "reg"), "the panel opens")
    log("region panel", v)
    head = FRAME["reg"][v[3] - 8, v[0] + 40]
    body = FRAME["reg"][v[1] + 8, v[0] + 6]
    log("header", head, "body", body, "popup", popup_col)
    check("the popover has the popup color",
          near(popup_col, th.user_interface.wcol_menu_back.inner[:3], 0.1), popup_col)
    check("the panel's body isn't the popup color", not near(body, popup_col, 0.05), (body, popup_col))
    check("its header differs from its body", not near(head, body, 0.01), (head, body))
    yield from close_all()
    yield from park()
    # A menu has no header color, and stays the menu color.
    m = yield from opened(open_menu("SIM_MT_short"), "menu", "the menu opens")
    check("a menu keeps the menu color",
          near(FRAME["menu"][m[1] + 3, m[0] + 3], th.user_interface.wcol_menu_back.inner[:3], 0.1),
          FRAME["menu"][m[1] + 3, m[0] + 3])
    yield from close_all()
    yield from park()
    # Subpanels, in the panel from the report. A shot to look at.
    bpy.context.scene.view_settings.use_white_balance = True
    yield from tear_props("RENDER_PT_color_management", "RENDER")
    yield from park()
    yield from grab("subs")
    yield from close_all()


SC["p10_looks"] = s_p10_looks


def s_p10_preset_arrow():
    """The arrow of a popover opened in a tear-off points at its button."""
    yield from begin()
    yield from tear_props("RENDER_PT_format", "OUTPUT")
    yield from park()
    yield from grab("torn")
    v = need(popup_box("base", "torn"), "it tears off")
    log("torn", v)
    # The preset button sits left of the pin and X, in the header's centered row.
    x, y = v[2] - 54, v[3] - 12
    yield from click(x, y); yield 0.8
    yield from grab("open")
    t = popup_box("torn", "open")
    log("preset", (x, y), t)
    # The arrow is the only part of the popup above its body: the topmost pixels of the difference.
    d = np.abs(FRAME["torn"] - FRAME["open"]).max(axis=2) > 0.04
    d[:, :30] = False
    d[:25, :] = False
    ys = np.where(d[:y + 1].any(axis=1))[0]
    check("the popup opens", t is not None, t)
    tip_y = int(ys.max()) if len(ys) else None
    if tip_y is not None:
        xs = np.where(d[tip_y - 2])[0]
        tip_x = int(xs.mean()) if len(xs) else None
        log("arrow at", tip_x, tip_y)
        check("the arrow is at the button", tip_x is not None and abs(tip_x - x) <= 12, (tip_x, x))
    yield from esc(); yield 0.3
    yield from close_all()


SC["p10_preset_arrow"] = s_p10_preset_arrow


def s_p10_shelf_narrow():
    """One column torn off is as narrow as the column, and still drags."""
    C = SIM_PT_cols.state
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    yield from park()
    yield from grab("base")
    yield from tear_center("SIM_PT_cols", rt="TOOLS")
    yield from park()
    yield from grab("m")
    v = need(torn_box("base", "m"), "it opens")
    yield from drag(v[2] + 2, mid_y(v), -300, 0)
    yield from park()
    yield from grab("one")
    w = need(torn_box("base", "one"), "at one column")
    log("one column", w, C["popup"])
    check("it's about as narrow as the column", width(w) <= 64, w)
    # The margin above the icons drags it.
    yield from drag(mid_x(w), w[3] - 3, 40, -30)
    yield from park()
    yield from grab("moved")
    x = need(torn_box("base", "moved"), "dragged")
    check("the margin above the icons drags it", abs(x[0] - w[0] - 40) <= 2 and abs(x[3] - w[3] + 30) <= 2, (w, x))
    # The X is reachable.
    yield from close_all()
    yield from park()


SC["p10_shelf_narrow"] = s_p10_shelf_narrow


def hold_round(tag, open_popup, row_y):
    yield from open_popup()
    yield from grab(tag + "att")
    a = need(popup_box("base", tag + "att"), "it opens: " + tag)
    yield from click(a[0] + 60, row_y(a)); yield 0.6
    yield from park()
    yield from grab(tag + "torn")
    v = need(popup_box("base", tag + "torn"), "it tears off: " + tag)
    log(tag, "attached", a, "torn", v)
    check(tag + ": the left edge holds", abs(v[0] - a[0]) <= 2, (a, v))
    check(tag + ": the top edge holds", abs(v[3] - a[3]) <= 2, (a, v))
    yield from close_all()
    yield from park()


def s_p10_hold():
    """Clicking Tear Off holds the popup's place."""
    SIM_PT_small.state["show"] = True
    yield from begin()

    def menu():
        move(*center()); yield 0.3
        call_menu("SIM_MT_short"); yield 0.8

    def panel():
        move(*center()); yield 0.3
        call_panel("SIM_PT_small"); yield 0.8
    yield from hold_round("menu_", menu, row_y_menu)
    yield from hold_round("panel_", panel, row_y_popover)


SC["p10_hold"] = s_p10_hold


def s_p10_ctx_addon():
    """The Tear Off entry shows on a panel an add-on registers, in its own sidebar tab."""
    A = SIM_PT_tear.state
    A["show"] = True
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    yield from open_tab("UI", "SimTear", A)
    yield from park()
    yield from grab("base")
    r = region_of(area(), "UI")
    x, y = r.x + 70, r.y + r.height - 26
    move(x, y); yield W
    move(x, y); yield W
    press(x, y, "RIGHTMOUSE"); yield 0.05
    release(x, y, "RIGHTMOUSE"); yield 0.6
    yield from grab("menu")
    b = popup_box("base", "menu")
    log("menu", b)
    yield from esc(); yield 0.3


SC["p10_ctx_addon"] = s_p10_ctx_addon


def s_p10_tall_low():
    """A corner low in the window doesn't crop a tall panel. Its left edge still holds."""
    SIM_PT_mid.state["show"] = True
    yield from begin()
    with bpy.context.temp_override(**override("VIEW_3D", "UI")):
        bpy.ops.wm.panel_tear_off(panel_idname="SIM_PT_mid", from_region_panel=True)
    yield 0.8
    yield from park()
    yield from grab("full")
    b = need(popup_box("base", "full"), "it opens")
    yield from close_all()
    yield from park()
    with bpy.context.temp_override(**override("VIEW_3D", "UI")):
        bpy.ops.wm.panel_tear_off(panel_idname="SIM_PT_mid", from_region_panel=True,
                                  source_xy=(500, 150))
    yield 0.8
    yield from park()
    yield from grab("low")
    v = need(popup_box("base", "low"), "it opens low")
    log("full", b, "low", v)
    check("the whole panel shows", abs(height(v) - height(b)) <= 2, (b, v))
    check("the left edge holds", abs(v[0] - 500) <= 2, v)
    yield from close_all()


SC["p10_tall_low"] = s_p10_tall_low


def s_p11_arrows():
    """A pinned menu's arrows act on a click only. Crossing them changes nothing."""
    P = SIM_OT_row_probe.state
    yield from begin()
    b = yield from opened(open_menu("SIM_MT_mid"), "m", "the menu opens")
    yield from crop(b, 200)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    rows = rows_box(v, STRIP_MENU)
    x = mid_x(v) - 20
    bottom = v[1] + 8
    # Scrolled on purpose, so both arrows show.
    yield from wheel(x, mid_y(v), True, 3)
    yield from park()
    yield from grab("pos")
    top = v[3] - STRIP_MENU - 8
    runs = P["runs"]
    for name, y in (("bottom", bottom), ("top", top)):
        move(x, y); yield 0.3
        move(x, y); yield 1.2
        yield from grab(name + "_over")
        yield from park()
        yield from grab(name + "_left")
        n = rdiff("pos", name + "_left", rows)
        check("hovering the " + name + " arrow doesn't scroll", n < 30, n)
    # A slow crossing, as on the way to a row: nothing moves and nothing runs.
    for i in range(6):
        move(x, bottom + i); yield 0.1
    for i in range(6):
        move(x, top - i); yield 0.1
    yield from park()
    yield from grab("crossed")
    n = rdiff("pos", "crossed", rows)
    check("crossing them doesn't scroll", n < 30, n)
    check("and runs no row", P["runs"] == runs, P)
    # One click, one row, and the release runs nothing.
    yield from click(x, bottom)
    yield from park()
    yield from grab("down1")
    n = rdiff("pos", "down1", rows)
    check("a click on the bottom arrow scrolls", n > 100, n)
    check("the click runs no row", P["runs"] == runs, P)
    yield from park()
    yield from grab("down1b")
    n = rdiff("down1", "down1b", rows)
    check("and only moves once", n < 30, n)
    yield from click(x, top)
    yield from park()
    yield from grab("up1")
    n = rdiff("pos", "up1", rows)
    check("a click on the top arrow moves back the same row", n < 30, n)
    check("still no row ran", P["runs"] == runs, P)
    # The other ways still work, and a row outside the arrows still runs.
    yield from wheel(x, mid_y(v), True, 1)
    yield from park()
    yield from grab("wheel")
    n = rdiff("pos", "wheel", rows)
    check("the wheel still scrolls", n > 100, n)
    yield from click(x, mid_y(v)); yield 0.3
    check("a row in the middle still runs", P["runs"] == runs + 1, P)
    yield from close_all()


SC["p11_arrows"] = s_p11_arrows


def s_p11_arrow_submenu():
    """A submenu row cut by an arrow doesn't open from under it."""
    yield from begin()
    b = yield from opened(open_menu("SIM_MT_arrows"), "m", "the menu opens")
    yield from crop(b, 150)
    yield from grab("c")
    v = need_box("base", "c", "cropped")
    move(mid_x(v) - 20, v[1] + 7); yield 0.3
    move(mid_x(v) - 20, v[1] + 7); yield 1.5
    yield from grab("over")
    outside = (v[2] + 2, 30, 1340, 900)
    n = rdiff("c", "over", outside)
    check("no submenu opens over the arrow", n < 30, n)
    yield from close_all()


SC["p11_arrow_submenu"] = s_p11_arrow_submenu


def strip_height(frame, v, x):
    """Rows from the block's top with the header's color at column x, from just inside the outline."""
    col = FRAME[frame][v[3] - 2, x]
    n = 0
    for y in range(v[3] - 2, v[1], -1):
        if np.abs(FRAME[frame][y, x] - col).max() > 0.02:
            break
        n += 1
    return n


def s_p12_header_metrics():
    """A pinned panel's header matches the source panel's."""
    yield from begin()
    with bpy.context.temp_override(**override("VIEW_3D", "UI")):
        move(*center()); yield 0.3
        bpy.ops.wm.panel_tear_off(panel_idname="VIEW3D_PT_tools_active", from_region_panel=True)
    yield 0.8
    yield from park()
    yield from grab("torn")
    v = need(popup_box("base", "torn"), "it opens")
    log("torn", v)
    # A free column near the middle of the header, away from its title and icons.
    h = strip_height("torn", v, v[0] + width(v) * 3 // 5)
    log("strip height", h)
    check("the header is as tall as a region's", 22 <= h <= 25, h)
    # The X icon's ink is centered about 14 from the edge, as the source's grip.
    bg = FRAME["torn"][v[3] - 2, v[0] + width(v) * 3 // 5]
    row = np.abs(FRAME["torn"][v[3] - h:v[3] - 1, v[2] - 26:v[2] - 3] - bg).max(axis=2) > 0.25
    ys, xs = np.where(row)
    log("x icon ink", None if len(xs) == 0 else (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())))
    check("the X has ink", len(xs) > 5, len(xs))
    x_center = (v[2] - 26) + (int(xs.min()) + int(xs.max())) / 2
    y_center = (v[3] - h) + (int(ys.min()) + int(ys.max())) / 2
    check("the X is about 14 from the edge", 11 <= v[2] - x_center <= 17, v[2] - x_center)
    check("and centered in the header", abs((v[3] - h / 2) - y_center) <= 2, (v[3] - h / 2, y_center))
    # The X closes it, and the pin collapses it.
    yield from click(v[2] - 14, v[3] - h // 2)
    yield from park()
    yield from grab("closed")
    n = rdiff("base", "closed", (30, 140, 1100, 850))
    check("the X closes it", n < 300, n)


SC["p12_header_metrics"] = s_p12_header_metrics


def ink(frame, box):
    """The box of what's brighter than any header color: icons and text."""
    x0, y0, x1, y1 = box
    d = FRAME[frame][y0:y1 + 1, x0:x1 + 1].mean(axis=2) > 0.6
    if not d.any():
        return None
    ys, xs = np.where(d)
    return int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0, int(ys.max()) + y0


def near(a, b, tolerance=1):
    return a is not None and b is not None and all(abs(i - j) <= tolerance for i, j in zip(a, b))


def corner_mismatch(open_name, col_name, v, base="base"):
    """Pixels whose difference from the base isn't shared, in the block's top corners. The same
    outline and shadow give the same mask, even with another fill."""
    n = 0
    for x0 in (v[0], v[2] - 11):
        box = (slice(v[3] - 11, v[3] + 1), slice(x0, x0 + 12))
        a = np.abs(FRAME[base][box] - FRAME[open_name][box]).max(axis=2) > 0.04
        b = np.abs(FRAME[base][box] - FRAME[col_name][box]).max(axis=2) > 0.04
        n += int((a != b).sum())
    return n


def collapses_in_place(name, title_y, has_plain_title=True, title_end=48, base="base",
                       box=(30, 25, 1340, 999), free_x=None):
    """Collapsing only moves the bottom edge up, and the header stays under the cursor."""
    yield from park()
    open_name, col_name = name + "_open", name + "_col"
    yield from grab(open_name)
    v = need(box_bbox(base, open_name, box), "it opens: " + name)
    log(name, "open", v)
    pin_x, x_x, y = v[2] - PIN_ICON, v[2] - X_ICON, v[3] - title_y
    # A column free of text and icons, in the header's row.
    free_x = v[0] + (width(v) * 3 // 5 if free_x is None else free_x)

    yield from click(pin_x, y)
    # It collapsed under the cursor, so it hasn't faded yet.
    yield from grab(name + "_just")
    n = float(np.abs(FRAME[open_name][y, free_x] - FRAME[name + "_just"][y, free_x]).max())
    check(name + ": still solid right after collapsing", n <= 0.03, n)
    # On the strip, but on no icon.
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    yield from grab(col_name)
    c = need(box_bbox(base, col_name, box), "it collapses: " + name)
    log(name, "collapsed", c)
    check(name + ": collapsed", height(c) < min(45, height(v) + 1), c)
    check(name + ": the left edge stays", abs(c[0] - v[0]) <= 1, (v, c))
    check(name + ": the right edge stays", abs(c[2] - v[2]) <= 1, (v, c))
    check(name + ": the top edge stays", abs(c[3] - v[3]) <= 1, (v, c))

    # Around the row only, as the collapsed strip shows what's below it.
    row = (y - 8, y + 8)
    x_open = ink(open_name, (v[2] - 26, row[0], v[2] - 3, row[1]))
    x_col = ink(col_name, (v[2] - 26, row[0], v[2] - 3, row[1]))
    log(name, "x ink", x_open, x_col)
    check(name + ": the X stays", near(x_open, x_col), (x_open, x_col))
    if has_plain_title:
        t_open = ink(open_name, (v[0] + 3, row[0], v[2] - title_end, row[1]))
        t_col = ink(col_name, (v[0] + 3, row[0], v[2] - title_end, row[1]))
        log(name, "title ink", t_open, t_col)
        check(name + ": the title stays", near(t_open, t_col), (t_open, t_col))
    n = float(np.abs(FRAME[open_name][y, free_x] - FRAME[col_name][y, free_x]).max())
    check(name + ": the same color", n <= 0.03, (n, FRAME[open_name][y, free_x], FRAME[col_name][y, free_x]))
    n = corner_mismatch(open_name, col_name, v, base)
    log(name, "corner mismatch", n)
    check(name + ": the same top corners", n <= 12, n)

    # Hovering lights the icon, as on the open header.
    for hover_x, label in ((pin_x, "pin"), (x_x, "x")):
        move(hover_x, y); yield 0.3
        move(hover_x, y); yield 0.3
        yield from grab(name + "_hover_" + label)
        n = rdiff(col_name, name + "_hover_" + label, (hover_x - 10, y - 10, hover_x + 10, y + 10))
        check(name + ": hovering " + label + " shows", n > 20, n)

    # At rest it recedes, as one layer, with the color and outline further down.
    yield from park()
    rest_name = name + "_rest"
    yield from grab(rest_name)
    hot, rest, under = (FRAME[f][y, free_x] for f in (col_name, rest_name, base))
    want = PIN_REST_BACK * hot + (1.0 - PIN_REST_BACK) * under
    n = float(np.abs(rest - want).max())
    log(name, "rest", rest, "want", want, "hot", hot, "under", under)
    check(name + ": the color recedes by the set amount", n <= 0.03, n)
    # Against the background, because a theme's header can be close to the viewport's color.
    if float(np.abs(hot - under).max()) > 0.1:
        check(name + ": and it shows", float(np.abs(rest - hot).max()) > 0.03, (rest, hot))
    # Hit areas and position don't change, and returning restores it exactly.
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    yield from grab(name + "_back")
    n = rdiff(col_name, name + "_back", (v[0], v[3] - 40, v[2], v[3]))
    check(name + ": back at full strength on hover", n < 30, n)

    # The same spot expands it, so clicking the pin twice is a no-op.
    yield from click(pin_x, y)
    yield from park()
    yield from grab(name + "_exp")
    n = rdiff(open_name, name + "_exp", v)
    check(name + ": the same spot expands it", n < 100, n)

    # And the same spot as the open X closes it.
    yield from click(pin_x, y)
    yield from park()
    yield from click(x_x, y)
    yield from park()
    yield from grab(name + "_closed")
    n = rdiff(base, name + "_closed", box)
    check(name + ": the same spot closes it", n < 300, n)


def s_p13_collapse_in_place():
    """A menu, a popover and panels with and without header controls."""
    yield from begin()
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    yield from collapses_in_place("menu", TITLE_MENU)

    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from collapses_in_place("popover", TITLE_Y)

    with bpy.context.temp_override(**override("VIEW_3D", "UI")):
        move(*center()); yield 0.3
        bpy.ops.wm.panel_tear_off(panel_idname="VIEW3D_PT_tools_active", from_region_panel=True)
    yield 0.8
    yield from collapses_in_place("panel", 12)

    yield from tear_center("VIEW3D_PT_tools_active", rt="TOOLS")
    # Narrow, with no grip. Only the start of its row is free.
    yield from collapses_in_place("shelf", TITLE_Y, has_plain_title=False, free_x=7)

    yield from tear_props("RENDER_PT_format", "OUTPUT")
    # Past the preset's icon, which a collapsed pin doesn't draw.
    yield from collapses_in_place("preset", 12, title_end=90)

    # Its title comes after the checkbox. Another tab changes the Properties editor, which a box
    # reaching it would count, so this is measured against the tab it needs.
    area("PROPERTIES").spaces.active.context = "RENDER"
    area_redraw(); yield 0.5
    yield from park()
    yield from grab("render_base")
    yield from tear_props("RENDER_PT_eevee_motion_blur", "RENDER")
    yield from collapses_in_place("checkbox", 12, base="render_base", box=(30, 25, 1590, 999))


SC["p13_collapse_in_place"] = s_p13_collapse_in_place


class SIM_PT_checkbox_title(bpy.types.Panel):
    """As Stabilize Stroke and Cavity: the checkbox carries the title when in a popover."""
    bl_idname = "SIM_PT_checkbox_title"; bl_label = "Checkbox Title"
    bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "Sim"
    def draw_header(self, context):
        self.layout.prop(context.scene, "use_gravity", text=self.bl_label if self.is_popover else "")
    def draw(self, context):
        self.layout.label(text="Body")


def s_p13_checkbox_title():
    """The collapsed pin can't draw the checkbox, so it keeps the title on its own."""
    bpy.utils.register_class(SIM_PT_checkbox_title)
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_checkbox_title"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    y = v[3] - TITLE_Y
    # Past the grip and the checkbox's box, which the collapsed pin doesn't draw.
    band = (v[0] + 50, y - 8, v[2] - 48, y + 8)
    t_open = ink("open", band)
    yield from click(v[2] - PIN_ICON, y)
    # On the title, so it's at full strength.
    move(v[0] + 60, y); yield 0.3
    move(v[0] + 60, y); yield 0.3
    yield from grab("col")
    c = need(popup_box("base", "col"), "it collapses")
    t_col = ink("col", band)
    log("title", t_open, t_col, "box", v, c)
    check("the row stays", abs(c[2] - v[2]) <= 1 and abs(c[3] - v[3]) <= 1, (v, c))
    check("the title shows", t_col is not None and t_col[2] - t_col[0] > 40, t_col)
    check("in the same place", near(t_open, t_col), (t_open, t_col))
    x0, y0, x1, y1 = band
    bright = [float(FRAME[f][y0:y1 + 1, x0:x1 + 1].mean(axis=2).max()) for f in ("open", "col")]
    check("and as bright", abs(bright[0] - bright[1]) <= 0.03, bright)
    yield from click(v[2] - X_ICON, y)
    yield from park()
    yield from grab("closed")
    n = rdiff("base", "closed", (30, 25, 1340, 999))
    check("the X closes it", n < 300, n)
    bpy.utils.unregister_class(SIM_PT_checkbox_title)


SC["p13_checkbox_title"] = s_p13_checkbox_title


# TEAR_OFF_PIN_REST_ALPHA and TEAR_OFF_PIN_REST_BACK_ALPHA.
PIN_REST_LAYER = 0.8
PIN_REST_BACK = 0.8 * 0.75


def pin_state(frame, x, y, hot, base="base"):
    """'hot' or 'rest' by the pin's color at this pixel, with what's behind it from `base`."""
    now = FRAME[frame][y, x]
    if float(np.abs(now - hot).max()) <= 0.03:
        return "hot"
    want = PIN_REST_BACK * hot + (1.0 - PIN_REST_BACK) * FRAME[base][y, x]
    return "rest" if float(np.abs(now - want).max()) <= 0.03 else None


def s_p13_pin_fade_stale():
    """Each way a pin could stay bright with the cursor gone, or stay faded under the cursor."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    y = v[3] - TITLE_Y
    # At the row's start, left of the grip.
    free_x = v[0] + 8
    x_x = v[2] - X_ICON
    yield from click(v[2] - PIN_ICON, y)
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    yield from grab("hot")
    hot = FRAME["hot"][y, free_x].copy()
    yield from park()
    yield from grab("rest")
    check("parked: at rest", pin_state("rest", free_x, y, hot) == "rest", FRAME["rest"][y, free_x])

    # Mid drag it stays solid, and released with the cursor away it fades.
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    press(free_x, y); yield 0.1
    dx, dy = 40, -30
    move(free_x + dx, y + dy); yield 0.3
    move(free_x + dx, y + dy); yield 0.3
    yield from grab("dragging")
    check("while dragging: solid", pin_state("dragging", free_x + dx, y + dy, hot) == "hot",
          FRAME["dragging"][y + dy, free_x + dx])
    release(free_x + dx, y + dy); yield 0.3
    yield from park()
    yield from grab("dropped")
    check("dropped, cursor away: at rest",
          pin_state("dropped", free_x + dx, y + dy, hot) == "rest",
          FRAME["dropped"][y + dy, free_x + dx])
    # Back in place for the rest.
    move(free_x + dx, y + dy); yield 0.3
    move(free_x + dx, y + dy); yield 0.3
    press(free_x + dx, y + dy); yield 0.1
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    release(free_x, y); yield 0.3

    # Dropped past the window's edge, the clamped pin isn't under the cursor.
    move(free_x, y); yield 0.3
    press(free_x, y); yield 0.1
    move(free_x, 5); yield 0.3
    move(free_x, 5); yield 0.3
    release(free_x, 5); yield 0.3
    yield from grab("edge")
    edge = popup_box("base", "edge")
    log("edge drop", edge)
    move(free_x, 5); yield 0.3
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    # Back in place, from wherever it stopped.
    if edge:
        ex, ey = free_x, (edge[1] + edge[3]) // 2
        move(ex, ey); yield 0.3
        move(ex, ey); yield 0.3
        press(ex, ey); yield 0.1
        move(free_x, y); yield 0.3
        move(free_x, y); yield 0.3
        release(free_x, y); yield 0.3

    # The focus goes while it's lit. The X must not stay lit either.
    yield from park()
    yield from grab("x_rest")
    move(x_x, y); yield 0.3
    move(x_x, y); yield 0.3
    yield from grab("x_lit")
    win().event_simulate(type="WINDOW_DEACTIVATE", value="NOTHING", x=int(x_x), y=int(y)); yield 0.4
    yield from grab("deactivated")
    check("focus gone: at rest", pin_state("deactivated", free_x, y, hot) == "rest",
          FRAME["deactivated"][y, free_x])
    n = rdiff("x_rest", "deactivated", (x_x - 10, y - 10, x_x + 10, y + 10))
    check("focus gone: the X isn't lit", n < 30, n)
    n = rdiff("x_rest", "x_lit", (x_x - 10, y - 10, x_x + 10, y + 10))
    check("and it was lit before", n > 20, n)
    # The window's return sends a mouse move.
    move(x_x, y); yield 0.3
    move(x_x, y); yield 0.3
    yield from grab("returned")
    check("focus back, on the pin: solid", pin_state("returned", free_x, y, hot) == "hot",
          FRAME["returned"][y, free_x])
    yield from park()

    # A regular popup above it takes the mouse, so the pin can't be used. It opens where the strip
    # is, so the strip moves out from under it first.
    away = (free_x + 320, y + 200)
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    press(free_x, y); yield 0.1
    move(*away); yield 0.3
    move(*away); yield 0.3
    release(*away); yield 0.3
    yield from park()
    yield from grab("before_regular")
    with bpy.context.temp_override(**override("VIEW_3D", "WINDOW")):
        bpy.ops.wm.call_panel(name="SIM_PT_field", keep_open=True)
    yield 0.8
    yield from grab("regular")
    r = need(bbox("before_regular", "regular"), "the regular popup opens")
    log("regular popup", r)
    check("it doesn't cover the strip", not (r[0] <= away[0] <= r[2] and r[1] <= away[1] <= r[3]), r)
    move(*away); yield 0.3
    move(*away); yield 0.3
    yield from grab("under_regular")
    check("under a regular popup: at rest",
          pin_state("under_regular", away[0], away[1], hot) == "rest",
          FRAME["under_regular"][away[1], away[0]])
    yield from esc(); yield from esc()
    move(*away); yield 0.3
    move(*away); yield 0.3
    press(*away); yield 0.1
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    release(free_x, y); yield 0.3
    yield from park()

    # A workspace change with the cursor on the pin, moved away while it's hidden.
    move(free_x, y); yield 0.3
    move(free_x, y); yield 0.3
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    move(*PARK); yield 0.3
    move(*PARK); yield 0.3
    w.workspace = home; yield 0.6
    yield from grab("returned_workspace")
    check("back from a workspace, cursor away: at rest",
          pin_state("returned_workspace", free_x, y, hot) == "rest",
          FRAME["returned_workspace"][y, free_x])

    # Covered by a newer tear-off, it fades where it still shows.
    yield from park()
    yield from grab("before_covered")
    move(center()[0] + 130, center()[1]); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("covered")
    n_box = bbox("before_covered", "covered")
    log("newer tear-off", n_box)
    if n_box and n_box[0] < v[2] and n_box[0] > free_x and n_box[1] <= y <= n_box[3]:
        over = (n_box[0] + v[2]) // 2
        move(over, y); yield 0.3
        move(over, y); yield 0.3
        yield from grab("covered_hover")
        check("cursor on what covers it: at rest",
              pin_state("covered_hover", free_x, y, hot) == "rest",
              FRAME["covered_hover"][y, free_x])
    else:
        check("the newer tear-off overlaps the pin", False, n_box)


SC["p13_pin_fade_stale"] = s_p13_pin_fade_stale


def rel_lum(c):
    """WCAG relative luminance of a display color."""
    lin = [(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4) for v in c]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def peak_contrast(frame, box):
    """Contrast between the box's median color and the color furthest from it."""
    x0, y0, x1, y1 = box
    px = FRAME[frame][y0:y1 + 1, x0:x1 + 1].reshape(-1, 3)
    med = np.median(px, axis=0)
    far = px[int(np.abs(px - med).sum(axis=1).argmax())]
    a, b = rel_lum(med), rel_lum(far)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def s_p13_pin_fade_bright():
    """Readable over a white viewport at rest, and the shadow only shows at full strength."""
    yield from setup()
    bpy.context.preferences.view.show_tooltips = False
    area().spaces.active.overlay.show_text = False
    area().spaces.active.overlay.show_floor = False
    area().spaces.active.overlay.show_axis_x = False
    area().spaces.active.overlay.show_axis_y = False
    area().spaces.active.overlay.show_cursor = False
    shading = area().spaces.active.shading
    shading.background_type = "VIEWPORT"
    shading.background_color = (1.0, 1.0, 1.0)
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("base")

    floors = (("menu", 2.4), ("panel", 2.6))
    for name, floor in floors:
        move(*center()); yield 0.3
        if name == "menu":
            tear_menu("VIEW3D_MT_object"); title_y = TITLE_MENU
        else:
            with bpy.context.temp_override(**override("VIEW_3D", "UI")):
                bpy.ops.wm.panel_tear_off(panel_idname="VIEW3D_PT_tools_active",
                                          from_region_panel=True)
            title_y = 12
        yield 0.8
        yield from park()
        yield from grab(name + "_open")
        v = need(popup_box("base", name + "_open"), "it opens: " + name)
        y = v[3] - title_y
        yield from click(v[2] - PIN_ICON, y)
        yield from park()
        yield from grab(name + "_rest")
        band = (v[0] + 10, y - 6, v[0] + 70, y + 6)
        n = peak_contrast(name + "_rest", band)
        log(name, "rest contrast", n, band)
        check(name + ": readable at rest on white", n >= floor, n)
        yield from click(v[2] - X_ICON, y)
        yield from park()

    # The strip is measured before a shadow can widen its box.
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("sh_open")
    v = need(popup_box("base", "sh_open"), "it opens")
    y = v[3] - TITLE_Y
    yield from click(v[2] - PIN_ICON, y)
    yield from park()
    # The factory theme has no shadow to see, so this sets one.
    ui = bpy.context.preferences.themes[0].user_interface
    ui.menu_shadow_width = 12
    ui.menu_shadow_fac = 0.5
    area_redraw(); yield 0.6
    yield from park()
    yield from grab("sh_rest")
    move(v[0] + 8, y); yield 0.3
    move(v[0] + 8, y); yield 0.3
    yield from grab("sh_hot")
    rest_box = need(box_bbox("base", "sh_rest", (30, 25, 1340, 999), 0.015), "rest box")
    hot_box = need(box_bbox("base", "sh_hot", (30, 25, 1340, 999), 0.015), "hot box")
    log("shadow boxes", rest_box, hot_box)
    check("a shadow only at full strength", height(hot_box) > height(rest_box) + 2,
          (rest_box, hot_box))


SC["p13_pin_fade_bright"] = s_p13_pin_fade_bright


# Saving pins, see _misc/6821-tear-off-saving-plan.md.
ID_OB_NAME = "Cube"
SIM_ID_SCREEN = 21075  # MAKE_ID2('S', 'R') in DNA_ID_enums.h.


def store_path(name):
    return os.path.join(os.environ["BLENDER_USER_CONFIG"], "store_" + name + ".blend")


def stored(ws=None):
    """The list on a workspace, as plain data. Empty if there is none."""
    group = (ws or win().workspace).bl_system_properties_get(do_create=False)
    value = group.get("bfa_tear_offs") if group is not None else None
    return value.to_dict() if value is not None else {}


def save_file(path):
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)
    yield 0.5


def open_file(path, load_ui=True):
    """No override: a load can free the override's window."""
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=load_ui)
    yield 1.5
    move(*center()); yield 0.3


def read_file(path, load_ui=True):
    """What's stored in a file, with the preference off so nothing is restored from it."""
    prefs = bpy.context.preferences
    prefs.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    yield from open_file(path, load_ui)


def entry_of(entries, kind):
    return next((e for e in entries.values() if e.get("kind") == kind), None)


def s_store_smoke():
    """Save and open work in the harness, and a file with no pins has no list."""
    yield from begin()
    path = store_path("smoke")
    yield from save_file(path)
    yield from open_file(path)
    check("the file opens", os.path.basename(bpy.data.filepath) == os.path.basename(path),
          bpy.data.filepath)
    check("no pins, no list", stored() == {}, stored())
    yield from save_file(path)
    yield from open_file(path)
    check("and after saving it again", stored() == {}, stored())


SC["store_smoke"] = s_store_smoke


def s_store_fields():
    """Every kind and every field, and the session's list stays what's still to restore."""
    yield from begin()
    ob = bpy.context.view_layer.objects.active
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    move(center()[0] - 200, center()[1]); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    move(center()[0] + 200, center()[1]); yield 0.3
    with bpy.context.temp_override(**override("VIEW_3D", "UI")):
        bpy.ops.wm.panel_tear_off(panel_idname="VIEW3D_PT_tools_active", from_region_panel=True)
    yield 0.8
    move(center()[0] + 200, center()[1] - 150); yield 0.3
    with bpy.context.temp_override(**override("VIEW_3D", "TOOLS")):
        bpy.ops.wm.panel_tear_off(panel_idname="VIEW3D_PT_tools_active", from_region_panel=True)
    yield 0.8
    tear_enum(id_type=ID_OB, session_uid=ob.session_uid, data_path="rotation_mode"); yield 0.8
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from park()

    path = store_path("fields")
    yield from save_file(path)
    check("the session's list stays empty", stored() == {}, stored())
    yield from read_file(path)
    entries = stored()
    log("entries", len(entries))
    for key, entry in entries.items():
        log(key, {k: v for k, v in entry.items()})
    check("every pin is stored", len(entries) == 6, len(entries))
    check("named by a counter, oldest first", list(entries) == [str(i) for i in range(6)],
          list(entries))
    kinds = [e.get("kind") for e in entries.values()]
    check("in the order they were made", kinds[:4] == ["MENU", "PANEL", "PANEL", "PANEL"], kinds)
    check("enums last", kinds[4:] == ["ENUM", "ENUM"], kinds)

    menu = entries["0"]
    check("a menu's name", menu["idname"] == "VIEW3D_MT_object", menu)
    check("a version", all(e["version"] == 1 for e in entries.values()))
    check("a mode", menu["mode"] == "objectmode", menu["mode"])
    check("its editor", menu["space"] > 0 and menu["area_index"] >= 0, menu)
    check("not collapsed", not menu["collapsed"], menu["collapsed"])
    check("no crop", menu["height"] == 0.0, menu["height"])

    popover, region, shelf = entries["1"], entries["2"], entries["3"]
    check("a row popover", popover["idname"] == "SIM_PT_field" and not popover["from_region"], popover)
    check("a region panel", region["from_region"] and region["width_default"] == 0.0, region)
    check("a shelf panel", shelf["from_region"] and shelf["width_default"] > 0.0, shelf)
    check("its width and what's not layout",
          shelf["width"] > 0.0 and 0.0 <= shelf["width_chrome"] <= shelf["width"], shelf)
    check("a position in the window",
          all(0 <= e["x"] < 1600 and 0 <= e["y"] < 1000 for e in entries.values()),
          [(e["x"], e["y"]) for e in entries.values()])

    by_id, by_context = entries["4"], entries["5"]
    check("an enum on an ID, by name",
          by_id["id_name"] == ID_OB_NAME and by_id["data_path"] == "rotation_mode"
          and by_id["lib_name"] == "" and not by_id["use_context"], by_id)
    check("no session UID", "session_uid" not in by_id, list(by_id))
    check("an enum on the context",
          by_context["use_context"]
          and by_context["data_path"] == "tool_settings.transform_pivot_point", by_context)


SC["store_fields"] = s_store_fields


def s_store_collapsed():
    """The collapsed state, a position that's the pin's, and scale free values."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    yield from click(v[2] - PIN_ICON, v[3] - TITLE_Y)
    yield from park()
    path = store_path("collapsed")
    yield from save_file(path)
    yield from read_file(path)
    entry = entry_of(stored(), "PANEL")
    log("entry", entry)
    check("collapsed", entry is not None and entry["collapsed"], entry)
    check("its left", abs(entry["x"] - v[0]) <= 2, (entry["x"], v))
    # Screenshots count from the bottom, on a window 1000 high.
    top = 1000 - entry["y"]
    check("its top", abs(top - v[3]) <= 2, (top, v))

    # Twice the scale, half the numbers.
    bpy.context.preferences.view.ui_scale = 2.0
    bpy.context.preferences.use_tear_off = True
    yield 0.8
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from save_file(path)
    bpy.context.preferences.view.ui_scale = 1.0
    yield from read_file(path)
    entries = stored()
    log("at scale 2", entries)
    # The one from the open above is still on the list, as nothing restores yet.
    entry = list(entries.values())[-1] if entries else None
    log("the new one", entry)
    check("scale free", entry is not None and entry["x"] < 400 and entry["y"] < 400, entry)


SC["store_collapsed"] = s_store_collapsed


def s_store_twice():
    """Saving doesn't add up, and closing with the X between saves removes it."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    first, second, third = (store_path("twice" + n) for n in "123")
    yield from save_file(first)
    yield from save_file(second)
    check("the session's list stays empty", stored() == {}, stored())
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    yield from park()
    yield from save_file(third)
    yield from read_file(first)
    check("first save: one", len(stored()) == 1, stored())
    yield from open_file(second)
    check("second save: still one", len(stored()) == 1, stored())
    yield from open_file(third)
    check("after the X: none", len(stored()) == 0, stored())


SC["store_twice"] = s_store_twice


def s_store_failed_save():
    """A save that fails leaves everything as it was."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    # A folder can't be written as a file.
    folder = os.path.join(os.environ["BLENDER_USER_CONFIG"], "store_folder.blend")
    os.makedirs(folder, exist_ok=True)
    failed = False
    try:
        with bpy.context.temp_override(window=win()):
            bpy.ops.wm.save_as_mainfile(filepath=folder, check_existing=False)
    except RuntimeError as ex:
        failed = True
        log("failed as expected", str(ex)[:100])
    yield 0.5
    check("the save failed", failed)
    check("the session's list stays empty", stored() == {}, stored())
    path = store_path("failed")
    yield from save_file(path)
    yield from read_file(path)
    check("and the next save still has the pin", len(stored()) == 1, stored())


SC["store_failed_save"] = s_store_failed_save


def s_store_pending():
    """What's still to restore goes before the open pins, keeps its data, and stays on the list.
    Sound groups are all Python can write, see the plan."""
    yield from begin()
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = {
        "7": {"version": 1, "kind": "MENU", "idname": "SIM_MT_gone"},
        "8": {"version": 99, "kind": "FUTURE", "new_field": 5},
        "9": "not a group",
    }
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    path = store_path("pending")
    yield from save_file(path)
    now = stored()
    check("the session's list keeps its own names", list(now) == ["7", "8", "9"], list(now))
    yield from read_file(path)
    entries = stored()
    log("saved", entries)
    check("renumbered, without what isn't a group", list(entries) == ["0", "1", "2"], list(entries))
    check("the pending one first", entries["0"].get("idname") == "SIM_MT_gone", entries)
    check("an unknown version kept whole",
          entries["1"].get("version") == 99 and entries["1"].get("new_field") == 5, entries)
    check("then the open pin", entries["2"].get("idname") == "SIM_PT_field", entries)

    # A list of the wrong type is replaced, with no error.
    bpy.context.preferences.use_tear_off = True
    yield 0.5
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = 5
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from save_file(path)
    value = win().workspace.bl_system_properties_get(do_create=False)["bfa_tear_offs"]
    check("the session keeps what it had", value == 5, value)
    yield from read_file(path)
    names = [e.get("idname") for e in stored().values()]
    # With the one that was restored by turning the preference on above.
    check("the file has the pins", names == ["SIM_PT_field", "SIM_PT_field"], stored())


SC["store_pending"] = s_store_pending


def s_close_load_ui_off():
    """Load UI off keeps the session's workspaces, so their pins stay, and the file's don't come."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    path = store_path("load_off")
    yield from save_file(path)
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    yield from read_file(path, load_ui=False)
    kinds = [e.get("kind") for e in stored().values()]
    log("kept", stored())
    check("the session's pin is on the kept workspace, and the file's isn't", kinds == ["MENU"], kinds)


SC["close_load_ui_off"] = s_close_load_ui_off


def s_close_load_ui_on():
    """Load UI on takes the file's workspaces, with the file's pins and none of the session's."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    path = store_path("load_on")
    yield from save_file(path)
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    yield from read_file(path, load_ui=True)
    kinds = [e.get("kind") for e in stored().values()]
    log("from the file", stored())
    check("only the file's pin", kinds == ["PANEL"], kinds)


SC["close_load_ui_on"] = s_close_load_ui_on


def s_close_failed_open():
    """An open that fails closes nothing and stores nothing."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    failed = False
    try:
        bpy.ops.wm.open_mainfile(filepath=store_path("does_not_exist"))
    except RuntimeError as ex:
        failed = True
        log("failed as expected", str(ex)[:100])
    yield 1.0
    check("the open failed", failed)
    check("nothing stored", stored() == {}, stored())
    yield from park()
    yield from grab("after")
    n = rdiff("open", "after", v)
    check("the pin is still there", n < 100, n)
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    yield from park()
    yield from grab("closed")
    n = rdiff("base", "closed", (30, 25, 1340, 999))
    check("and closes", n < 300, n)


SC["close_failed_open"] = s_close_failed_open


def s_close_pref_off():
    """Turning the preference off keeps them on the list, oldest first. Saving keeps them too."""
    yield from begin()
    prefs = bpy.context.preferences
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    move(center()[0] - 200, center()[1]); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    move(center()[0] + 200, center()[1]); yield 0.3
    with bpy.context.temp_override(**override("VIEW_3D", "UI")):
        bpy.ops.wm.panel_tear_off(panel_idname="VIEW3D_PT_tools_active", from_region_panel=True)
    yield 0.8
    prefs.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    yield from park()
    yield from grab("off")
    n = rdiff("base", "off", (30, 25, 1340, 999))
    check("they close", n < 300, n)
    names = [e.get("idname") for e in stored().values()]
    log("on the list", names)
    check("oldest first",
          names == ["VIEW3D_MT_object", "SIM_PT_field", "VIEW3D_PT_tools_active"], names)
    path = store_path("pref_off")
    yield from save_file(path)
    check("saving doesn't change it", len(stored()) == 3, stored())
    yield from read_file(path)
    names = [e.get("idname") for e in stored().values()]
    check("and they're in the file",
          names == ["VIEW3D_MT_object", "SIM_PT_field", "VIEW3D_PT_tools_active"], names)


SC["close_pref_off"] = s_close_pref_off


def s_close_x():
    """The X removes it for good, collapsed or not."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    yield from park()
    check("open: not stored", stored() == {}, stored())
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from click(v[2] - PIN_ICON, v[3] - TITLE_Y)
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    yield from park()
    check("collapsed: not stored", stored() == {}, stored())
    path = store_path("x")
    yield from save_file(path)
    yield from read_file(path)
    check("and not in the file", stored() == {}, stored())


SC["close_x"] = s_close_x


class SIM_PT_goes_away(bpy.types.Panel):
    bl_idname = "SIM_PT_goes_away"; bl_label = "Goes Away"
    bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "Sim"
    def draw(self, context):
        self.layout.label(text="Body")


def s_close_unregister():
    """An add-on going away takes the type, but the pin stays on the list."""
    yield from begin()
    bpy.utils.register_class(SIM_PT_goes_away)
    yield 0.3
    move(*center()); yield 0.3
    tear_panel("SIM_PT_goes_away"); yield 0.8
    yield from park()
    yield from grab("open")
    check("it opens", popup_box("base", "open") is not None)
    bpy.utils.unregister_class(SIM_PT_goes_away)
    yield 0.5
    yield from park()
    yield from grab("gone")
    n = rdiff("base", "gone", (30, 25, 1340, 999))
    check("it closes", n < 300, n)
    names = [e.get("idname") for e in stored().values()]
    check("it's on the list", names == ["SIM_PT_goes_away"], names)


SC["close_unregister"] = s_close_unregister


def s_close_undo():
    """Undo doesn't load the UI: nothing moves, closes or goes on the list."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    with bpy.context.temp_override(**override()):
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=(1, 1, 1))
        bpy.ops.ed.undo_push(message="sim")
    yield 0.5
    with bpy.context.temp_override(**override()):
        bpy.ops.ed.undo()
    yield 1.0
    yield from park()
    yield from grab("undone")
    # The box only: the viewport can differ, and the panel's on the name field of the active object.
    n = rdiff("open", "undone", (v[0], v[3] - 40, v[2], v[3]))
    check("the header didn't move", n < 60, n)
    check("nothing on the list", stored() == {}, stored())


SC["close_undo"] = s_close_undo


def header_box(v):
    return (v[0], v[3] - 40, v[2], v[3])


def pin_and_save(path):
    """A panel and a menu side by side, saved. Returns their boxes."""
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("one")
    panel = need(popup_box("base", "one"), "the panel opens")
    move(center()[0] + 280, center()[1]); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    yield from park()
    yield from grab("two")
    menu = need(popup_box("one", "two"), "the menu opens")
    yield from save_file(path)
    return panel, menu


def closes_to(name, boxes_titles, compare_box, base="base"):
    """The X of each, and only what was there before is left. A duplicate would still show."""
    for v, title_y in boxes_titles:
        yield from click(v[2] - X_ICON, v[3] - title_y)
    yield from park()
    yield from grab(name)
    return rdiff(base, name, compare_box)


def s_restore_round_trip():
    """Open with Load UI on: back in place, one of each, and off the list."""
    yield from begin()
    path = store_path("round_trip")
    panel, menu = yield from pin_and_save(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("two", "restored", header_box(panel))
    check("the panel's back in place", n < 60, n)
    n = rdiff("two", "restored", header_box(menu))
    check("the menu's back in place", n < 60, n)
    both = (min(panel[0], menu[0]), min(panel[1], menu[1]), max(panel[2], menu[2]), max(panel[3], menu[3]))
    n = yield from closes_to("closed", ((menu, TITLE_MENU), (panel, TITLE_Y)), both)
    check("one of each: the X leaves nothing", n < 300, n)


SC["restore_round_trip"] = s_restore_round_trip


def s_restore_once():
    """Saving again and switching away and back don't make another."""
    yield from begin()
    path = store_path("once")
    panel, menu = yield from pin_and_save(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from save_file(path)
    check("off the list after a save", stored() == {}, stored())
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 0.6
    yield from park()
    yield from open_file(path, load_ui=True)
    yield from park()
    both = (min(panel[0], menu[0]), min(panel[1], menu[1]), max(panel[2], menu[2]), max(panel[3], menu[3]))
    n = yield from closes_to("closed", ((menu, TITLE_MENU), (panel, TITLE_Y)), both)
    check("still one of each after a second open", n < 300, n)


SC["restore_once"] = s_restore_once


def s_restore_closed_stays():
    """Closed after saving: it isn't on the list, so a workspace change doesn't bring it back."""
    yield from begin()
    path = store_path("closed")
    panel, menu = yield from pin_and_save(path)
    yield from closes_to("closed", ((menu, TITLE_MENU), (panel, TITLE_Y)), panel)
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 0.6
    yield from park()
    yield from grab("after")
    n = rdiff("base", "after", (30, 25, 1340, 999))
    check("it stays closed", n < 300, n)


SC["restore_closed_stays"] = s_restore_closed_stays


def s_restore_load_ui_off():
    """Load UI off: yours come back, in place, and the file's don't come."""
    yield from begin()
    path = store_path("restore_off")
    panel, menu = yield from pin_and_save(path)
    yield from closes_to("closed", ((menu, TITLE_MENU),), menu)
    yield from park()
    yield from grab("only_panel")
    yield from open_file(path, load_ui=False)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("only_panel", "restored", header_box(panel))
    check("your pin's back in place", n < 60, n)
    n = rdiff("only_panel", "restored", header_box(menu))
    check("the file's other pin didn't come", n < 60, n)


SC["restore_load_ui_off"] = s_restore_load_ui_off


def s_restore_load_ui_on():
    """Load UI on: the file's come back, and yours go with your workspaces."""
    yield from begin()
    path = store_path("restore_on")
    panel, menu = yield from pin_and_save(path)
    yield from grab("saved")
    yield from closes_to("closed", ((menu, TITLE_MENU), (panel, TITLE_Y)), panel)
    move(center()[0] - 280, center()[1] - 200); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("mine")
    mine = need(popup_box("closed", "mine"), "a new pin")
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    n = rdiff("saved", "restored", header_box(panel))
    check("the file's pins are back", n < 60, n)
    n = rdiff("closed", "restored", header_box(mine))
    check("the session's isn't", n < 60 and not (mine[0] < panel[2] and panel[0] < mine[2]), n)


SC["restore_load_ui_on"] = s_restore_load_ui_on


def s_restore_file_new():
    """File > New with Load UI off keeps the workspaces too, and so the pins."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    bpy.ops.wm.read_homefile(load_ui=False)
    yield 1.5
    move(*center()); yield 0.3
    yield from park()
    yield from grab("new")
    check("off the list", stored() == {}, stored())
    n = rdiff("open", "new", header_box(v))
    check("it's still there", n < 60, n)


SC["restore_file_new"] = s_restore_file_new


def s_restore_workspace_first_switch():
    """A pin on a workspace that isn't showing stays on the list until it shows."""
    yield from begin()
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces
                 if ws != home and any(a.type == "VIEW_3D" for a in ws.screens[0].areas))
    log("other workspace", other.name)
    w.workspace = other; yield 0.8
    yield from park()
    yield from grab("other_base")
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.menu_tear_off(menu_idname="VIEW3D_MT_object")
    yield 0.8
    yield from park()
    yield from grab("other_open")
    v = need(box_bbox("other_base", "other_open", (30, 25, 1340, 999)), "it opens")
    other_name = other.name
    w.workspace = home; yield 0.6
    path = store_path("first_switch")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    other = bpy.data.workspaces[other_name]
    check("the active workspace has nothing to restore", stored() == {}, stored())
    check("the other one still has it", len(stored(other)) == 1, stored(other))
    win().workspace = other; yield 0.8
    yield from park()
    yield from grab("restored")
    check("off the list once it shows", stored(other) == {}, stored(other))
    n = rdiff("other_open", "restored", header_box(v))
    check("and it's back", n < 60, n)


SC["restore_workspace_first_switch"] = s_restore_workspace_first_switch


def s_restore_temp_override():
    """A script's override only looks at a workspace, so its pins wait."""
    yield from begin()
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    group = other.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = {"0": {
        "version": 1, "kind": "MENU", "idname": "VIEW3D_MT_object", "winid": 1, "space": 1,
        "region": 1, "area_index": -1, "mode": "objectmode", "x": 300.0, "y": 300.0,
        "collapsed": False, "height": 0.0, "scroll": 0.0}}
    screen = other.screens[0]
    with bpy.context.temp_override(window=w, screen=screen):
        pass
    yield 0.8
    check("back on the home workspace", win().workspace == home)
    check("it stays on the list", len(stored(other)) == 1, stored(other))


SC["restore_temp_override"] = s_restore_temp_override


def s_restore_pref_on():
    """Turning the preference off and on brings them back right away, in order."""
    yield from begin()
    prefs = bpy.context.preferences
    path = store_path("pref_on")
    panel, menu = yield from pin_and_save(path)
    prefs.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    yield from park()
    yield from grab("off")
    n = rdiff("base", "off", (30, 25, 1340, 999))
    check("they close", n < 300, n)
    names = [e.get("idname") for e in stored().values()]
    check("on the list, oldest first", names == ["SIM_PT_field", "VIEW3D_MT_object"], names)
    prefs.use_tear_off = True; yield 0.8
    yield from park()
    yield from grab("on")
    check("off the list", stored() == {}, stored())
    n = rdiff("two", "on", header_box(panel))
    check("the panel's back", n < 60, n)
    n = rdiff("two", "on", header_box(menu))
    check("the menu's back", n < 60, n)


SC["restore_pref_on"] = s_restore_pref_on


def s_restore_pref_restored():
    """Restored from a file, then off, saved and on: nothing lost, which the first draft got wrong."""
    yield from begin()
    prefs = bpy.context.preferences
    path = store_path("pref_restored")
    panel, menu = yield from pin_and_save(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    check("restored", stored() == {}, stored())
    prefs.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    yield from save_file(path)
    check("on the list", len(stored()) == 2, stored())
    prefs.use_tear_off = True; yield 0.8
    yield from park()
    yield from grab("on")
    check("back right away", stored() == {}, stored())
    n = rdiff("two", "on", header_box(panel))
    check("in place", n < 60, n)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("reopened")
    check("and after reopening", stored() == {}, stored())
    n = rdiff("two", "reopened", header_box(menu))
    check("in place", n < 60, n)


SC["restore_pref_restored"] = s_restore_pref_restored


def s_restore_missing_type():
    """A type that's gone stays on the list with no error, and returns with its type."""
    yield from begin()
    bpy.utils.register_class(SIM_PT_goes_away)
    yield 0.3
    move(*center()); yield 0.3
    tear_panel("SIM_PT_goes_away"); yield 0.8
    yield from park()
    bpy.utils.unregister_class(SIM_PT_goes_away)
    yield 0.8
    yield from park()
    yield from grab("gone")
    names = [e.get("idname") for e in stored().values()]
    check("on the list", names == ["SIM_PT_goes_away"], names)
    n = rdiff("base", "gone", (30, 25, 1340, 999))
    check("no pin and no error popup", n < 300, n)
    bpy.utils.register_class(SIM_PT_goes_away)
    yield 0.5
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 0.8
    yield from park()
    check("back with its type", stored() == {}, stored())
    yield from grab("back")
    n = rdiff("base", "back", (30, 25, 1340, 999))
    check("and it shows", n > 300, n)
    bpy.utils.unregister_class(SIM_PT_goes_away)
    yield 0.3


SC["restore_missing_type"] = s_restore_missing_type


def s_restore_reload():
    """Reload Scripts closes Python's pins, and they come straight back."""
    yield from begin()
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    with bpy.context.temp_override(window=win()):
        bpy.ops.script.reload()
    yield 2.0
    yield from park()
    yield from grab("reloaded")
    check("off the list", stored() == {}, stored())
    n = rdiff("open", "reloaded", header_box(v))
    check("it's back", n < 60, n)


SC["restore_reload"] = s_restore_reload


def s_restore_mode():
    """A pin from another mode waits for it."""
    yield from begin()
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="EDIT")
    yield 0.6
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="OBJECT")
    yield 0.6
    path = store_path("mode")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("object_mode")
    modes = [e.get("mode") for e in stored().values()]
    log("modes", modes)
    check("waiting on the list", modes == ["mesh_edit"], modes)
    with bpy.context.temp_override(**override()):
        bpy.ops.object.mode_set(mode="EDIT")
    yield 0.8
    yield from park()
    check("off the list in its mode", stored() == {}, stored())


SC["restore_mode"] = s_restore_mode


def s_restore_bad_panel():
    """Entries a good file wouldn't have: no crash, and what could become valid stays."""
    yield from begin()
    common = {"version": 1, "from_region": False, "width": 0.0, "width_default": 0.0,
              "width_chrome": 0.0, "winid": 1, "space": 1, "region": 1, "area_index": -1,
              "mode": "objectmode", "x": 300.0, "y": 300.0, "collapsed": False, "height": 0.0,
              "scroll": 0.0}
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = {
        # Another editor's panel, whose C poll needs that editor.
        "0": dict(common, kind="PANEL", idname="PROPERTIES_PT_context"),
        # An unknown version, kept for whatever wrote it.
        "1": dict(common, version=99, kind="PANEL", idname="SIM_PT_field"),
        # Each of these is invalid, so it's dropped.
        "2": dict(common, kind="PANEL", idname="SIM_PT_field", x="not a number"),
        "3": dict(common, kind="PANEL", idname="SIM_PT_field", x=float("nan")),
        "4": dict(common, kind="PANEL", idname="SIM_PT_field", y=1e30),
        "5": dict(common, kind="PANEL", idname="SIM_PT_field", space=-3),
        "6": dict(common, kind="PANEL", idname="SIM_PT_field", height=-5.0),
        "7": dict(common, kind="PANEL"),
        "8": dict(common, kind="PANEL", idname="SIM_PT_field", width=10.0, width_chrome=50.0),
    }
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 1.0
    yield from park()
    yield from grab("after")
    names = sorted(stored())
    log("left", names, stored())
    check("what could work stays, and what's invalid goes", names == ["0", "1"], names)
    n = rdiff("base", "after", (30, 25, 1340, 999))
    check("and nothing opens", n < 300, n)


SC["restore_bad_panel"] = s_restore_bad_panel


def s_restore_region_panel():
    """A panel torn off a region keeps its look and its header."""
    yield from begin()
    # No yield inside the override: the context would be gone by the time the operator runs.
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override("VIEW_3D", "UI")):
        bpy.ops.wm.panel_tear_off(panel_idname="VIEW3D_PT_tools_active", from_region_panel=True)
    yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    path = store_path("region")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("open", "restored", v)
    check("the same in every pixel, nearly", n < 60, n)
    yield from click(v[2] - X_ICON, v[3] - 12)
    yield from park()
    yield from grab("closed")
    n = rdiff("base", "closed", v)
    check("one of it", n < 300, n)


SC["restore_region_panel"] = s_restore_region_panel


def s_restore_shelf_columns():
    """A shelf panel keeps its own width and column count, whatever the shelf is by then."""
    yield from setup()
    area().spaces.active.overlay.show_text = False
    C = SIM_PT_cols.state
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    w = yield from shelf_resize(170)
    log("shelf width", w)
    C["popup"].clear()
    r = yield from tear_center("SIM_PT_cols", rt="TOOLS")
    check("it opens", r == {"INTERFACE"}, r)
    width0, count0 = C["popup"].get("width"), C["popup"].get("count")
    log("pinned", C["popup"])
    path = store_path("shelf")
    yield from save_file(path)
    # A shelf that's narrower by the time it comes back.
    w2 = yield from shelf_resize(70)
    log("shelf now", w2)
    C["popup"].clear()
    yield from open_file(path, load_ui=False)
    yield from to_rest()
    check("off the list", stored() == {}, stored())
    log("restored", C["popup"])
    check("the same width", abs(C["popup"].get("width", 0) - width0) <= 1, (C["popup"], width0))
    check("the same columns", C["popup"].get("count") == count0, (C["popup"], count0))


SC["restore_shelf_columns"] = s_restore_shelf_columns


def s_restore_crop_scroll():
    """A cropped and scrolled panel comes back showing the same rows."""
    st = SIM_PT_mid.state
    yield from begin(st)
    b = yield from opened(open_tpanel("SIM_PT_mid"), "p", "the panel opens")
    yield from crop(b, 200)
    yield from grab("crop")
    v = need(box_bbox("base", "crop", VIEW), "cropped")
    yield from wheel(mid_x(v), mid_y(v), True, 3)
    yield from park()
    yield from grab("scrolled")
    path = store_path("crop")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("scrolled", "restored", v)
    log("difference", n)
    check("the same rows, at the same crop", n < 100, n)


SC["restore_crop_scroll"] = s_restore_crop_scroll


def s_restore_collapsed():
    """A collapsed pin comes back collapsed, in place, and expands to the same panel."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    y = v[3] - TITLE_Y
    yield from click(v[2] - PIN_ICON, y)
    yield from park()
    yield from grab("collapsed")
    path = store_path("restore_collapsed")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("collapsed", "restored", (v[0], v[3] - 40, v[2], v[3]))
    check("the same strip, at rest", n < 60, n)
    n = rdiff("open", "restored", (v[0], v[1], v[2], v[3] - 45))
    check("with nothing open below it", n > 300, n)
    yield from click(v[2] - PIN_ICON, y)
    yield from park()
    yield from grab("expanded")
    n = rdiff("open", "expanded", v)
    check("the pin expands it to the same panel", n < 60, n)


SC["restore_collapsed"] = s_restore_collapsed


def s_restore_poll_false():
    """A panel whose poll fails in its own mode shows Not available, like a live pin."""
    st = SIM_PT_tear.state
    yield from begin(st)
    yield from open_tab("UI", "SimTear", st)
    yield from park()
    yield from grab("base_tab")
    move(*center()); yield 0.3
    tear_panel("SIM_PT_tear"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base_tab", "open"), "it opens")
    path = store_path("poll_false")
    yield from save_file(path)
    st["show"] = False
    area_redraw(); yield 0.5
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("open", "restored", (v[0], v[3] - 40, v[2], v[3]))
    check("its header is there", n < 300, n)
    n = rdiff("open", "restored", (v[0], v[1], v[2], v[3] - 40))
    check("with no content", n > 100, n)
    st["show"] = True
    bpy.context.scene.frame_current += 1
    area_redraw(); yield 0.8
    yield from park()
    yield from grab("back")
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    yield from park()
    yield from grab("closed")
    n = rdiff("restored", "closed", (v[0], v[3] - 40, v[2], v[3]))
    check("its X works", n > 100, n)


SC["restore_poll_false"] = s_restore_poll_false


def enum_entry(**kw):
    entry = {"version": 1, "kind": "ENUM", "winid": 1, "space": 1, "region": 1, "area_index": -1,
             "mode": "objectmode", "x": 300.0, "y": 300.0, "collapsed": False, "height": 0.0,
             "scroll": 0.0, "use_context": False, "id_type": 0, "id_name": "", "lib_name": "",
             "data_path": "", "op_idname": "", "op_propname": "", "op_context": 1}
    entry.update(kw)
    return entry


def s_restore_enum_id():
    """An enum on an ID finds it again by name, and changes the real data."""
    yield from begin()
    ob = bpy.context.view_layer.objects.active
    tear_enum(id_type=ID_OB, session_uid=ob.session_uid, data_path="rotation_mode"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    path = store_path("enum_id")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("open", "restored", v)
    check("back in place", n < 60, n)
    # A row of the pin works on the object in this file.
    ob = bpy.data.objects[ID_OB_NAME]
    yield from click(*tear_row(v, 3))
    yield from park()
    check("and works", ob.rotation_mode == "YXZ", ob.rotation_mode)


SC["restore_enum_id"] = s_restore_enum_id


def s_restore_enum_context():
    """An enum on the context."""
    yield from begin()
    tear_enum(use_context=True, data_path="tool_settings.transform_pivot_point"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    path = store_path("enum_context")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("open", "restored", v)
    check("back in place", n < 60, n)


SC["restore_enum_context"] = s_restore_enum_context


def s_restore_enum_operator():
    """An operator enum comes back, and runs its operator."""
    yield from begin()
    bpy.utils.register_class(SIM_OT_enum); yield 0.3
    r = tear_enum(op_idname="SIM_OT_enum", op_propname="type", op_context=1); yield 0.8
    check("it opens", r == {"INTERFACE"}, r)
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "its box")
    path = store_path("enum_operator")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    check("off the list", stored() == {}, stored())
    n = rdiff("open", "restored", v)
    check("back in place", n < 60, n)
    yield from click(*tear_row(v, 0))
    yield from park()
    check("and its item runs", SIM_OT_enum.state["type"] == "FIRST", SIM_OT_enum.state)
    bpy.utils.unregister_class(SIM_OT_enum); yield 0.3


SC["restore_enum_operator"] = s_restore_enum_operator


def s_restore_enum_missing_id():
    """With Load UI off, an ID that isn't in the new file waits for it."""
    yield from begin()
    ob = bpy.context.view_layer.objects.active
    keep = store_path("enum_keep")
    yield from save_file(keep)
    # Another file, with no such object.
    other = store_path("enum_other")
    bpy.data.objects.remove(ob)
    yield 0.3
    yield from save_file(other)
    yield from open_file(keep, load_ui=True)
    yield from park()
    ob = bpy.data.objects[ID_OB_NAME]
    tear_enum(id_type=ID_OB, session_uid=ob.session_uid, data_path="rotation_mode"); yield 0.8
    yield from park()
    yield from open_file(other, load_ui=False)
    yield from park()
    kinds = [e.get("kind") for e in stored().values()]
    check("on the list with its ID gone", kinds == ["ENUM"], stored())
    yield from open_file(keep, load_ui=False)
    yield from park()
    check("back with its ID", stored() == {}, stored())


SC["restore_enum_missing_id"] = s_restore_enum_missing_id


def s_restore_enum_bad():
    """Entries a good file wouldn't have."""
    yield from begin()
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = {
        # These could become valid, so they stay.
        "0": enum_entry(id_type=ID_OB, id_name="No Such Object", data_path="rotation_mode"),
        "1": enum_entry(id_type=ID_OB, id_name=ID_OB_NAME, data_path="not_a_property"),
        "2": enum_entry(id_type=ID_OB, id_name=ID_OB_NAME, data_path="location"),
        "3": enum_entry(op_idname="SIM_OT_no_such_operator", op_propname="type"),
        "4": enum_entry(id_type=12345, id_name="Whatever", data_path="x"),
        # A screen and a window manager are refused, whichever way they're reached.
        "5": enum_entry(id_type=SIM_ID_SCREEN, id_name="Layout", data_path="areas[0].type"),
        "6": enum_entry(use_context=True, data_path="area.type"),
        # An out of range context is invalid, so it goes.
        "7": enum_entry(op_idname="SIM_OT_enum", op_propname="type", op_context=9999),
    }
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 1.0
    yield from park()
    yield from grab("after")
    names = sorted(stored())
    log("left", names)
    check("no pin came from them", rdiff("base", "after", (30, 25, 1340, 999)) < 300,
          rdiff("base", "after", (30, 25, 1340, 999)))
    check("the invalid one went, and the rest wait", names == [str(i) for i in range(7)], names)


SC["restore_enum_bad"] = s_restore_enum_bad


def s_review_name_collision():
    """A waiting entry named above what's free must not cost a closing pin its place."""
    yield from begin()
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    move(center()[0] - 200, center()[1]); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    group = win().workspace.bl_system_properties_get(do_create=True)
    # What's left of a list of three, with the last one waiting for its mode.
    group["bfa_tear_offs"] = {"2": {
        "version": 1, "kind": "MENU", "idname": "VIEW3D_MT_edit_mesh", "winid": 1, "space": 1,
        "region": 1, "area_index": -1, "mode": "mesh_edit", "x": 300.0, "y": 300.0,
        "collapsed": False, "height": 0.0, "scroll": 0.0}}
    path = store_path("collision")
    yield from save_file(path)
    bpy.context.preferences.use_tear_off = True
    yield from open_file(path, load_ui=False)
    yield from park()
    names = [e.get("idname") for e in stored().values()]
    log("left", stored().keys())
    check("the waiting one stays", names == ["VIEW3D_MT_edit_mesh"], names)
    yield from grab("back")
    n = rdiff("base", "back", (30, 25, 1340, 999))
    check("and both pins are back", n > 300, n)
    # Both are open again, so a save has all three.
    yield from save_file(path)
    yield from read_file(path)
    names = sorted(e.get("idname") for e in stored().values())
    log("in the file", names)
    check("nothing was lost",
          names == ["SIM_PT_field", "VIEW3D_MT_edit_mesh", "VIEW3D_MT_object"], names)


SC["review_name_collision"] = s_review_name_collision


def s_review_no_source():
    """Entries with no real source wait, instead of drawing with nothing to draw for."""
    yield from begin()
    common = {"version": 1, "from_region": False, "width": 0.0, "width_default": 0.0,
              "width_chrome": 0.0, "winid": 1, "area_index": -1, "mode": "", "x": 300.0, "y": 300.0,
              "collapsed": False, "height": 0.0, "scroll": 0.0}
    props_space = 4  # SPACE_PROPERTIES
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = {
        # Dereferences the area's space.
        "0": dict(common, kind="MENU", idname="SCREEN_MT_user_menu", space=0, region=-1),
        # Dereferences the region.
        "1": dict(common, kind="PANEL", idname="DATA_PT_modifiers", space=0, region=-1),
        "2": dict(common, kind="PANEL", idname="DATA_PT_modifiers", space=1, region=-1),
        # An instanced panel needs custom data, in the editor that really has it.
        "3": dict(common, kind="PANEL", idname="MOD_PT_Mirror", space=props_space, region=1),
        # A context menu gets no header, so nothing could close it.
        "4": dict(common, kind="MENU", idname="VIEW3D_MT_object_context_menu", space=1, region=1),
    }
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 1.0
    yield from park()
    yield from grab("after")
    check("all still waiting", sorted(stored()) == ["0", "1", "2", "3", "4"], sorted(stored()))
    n = rdiff("base", "after", (30, 25, 1340, 999))
    check("no pin, and no crash", n < 300, n)


SC["review_no_source"] = s_review_no_source


def s_review_unmaximize():
    """A pin waiting for its editor returns when leaving a maximized area brings it back."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    # Maximize another editor, so the 3D View isn't in the screen. A fixed point, as center() needs
    # a 3D View.
    other = next(a for a in win().screen.areas if a.type == "OUTLINER")
    with bpy.context.temp_override(window=win(), area=other):
        bpy.ops.screen.screen_full_area()
    yield 0.8
    bpy.context.preferences.use_tear_off = False; yield 0.6
    move(800, 500); yield 0.5
    bpy.context.preferences.use_tear_off = True; yield 0.8
    check("waiting while its editor is away", len(stored()) == 1, stored())
    area_now = next(a for a in win().screen.areas if a.type == "OUTLINER")
    with bpy.context.temp_override(window=win(), area=area_now):
        bpy.ops.screen.screen_full_area()
    yield 0.8
    yield from park()
    check("back with its editor", stored() == {}, stored())


SC["review_unmaximize"] = s_review_unmaximize


def s_review_editor_change():
    """The same when an area changes to the editor it waits for."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    bpy.context.preferences.use_tear_off = False; yield 0.6
    move(*center()); yield 0.5
    area().type = "OUTLINER"; yield 0.6
    views = [a for a in win().screen.areas if a.type == "VIEW_3D"]
    log("3D views left", len(views))
    for a in views:
        a.type = "OUTLINER"
    yield 0.4
    bpy.context.preferences.use_tear_off = True; yield 0.8
    check("waiting while its editor is away", len(stored()) == 1, stored())
    next(a for a in win().screen.areas if a.type == "OUTLINER").type = "VIEW_3D"; yield 0.8
    yield from park()
    check("back with its editor", stored() == {}, stored())


SC["review_editor_change"] = s_review_editor_change


def s_review_register_returns():
    """Enabling an add-on again brings its pin back with no other action."""
    yield from begin()
    bpy.utils.register_class(SIM_PT_goes_away)
    yield 0.3
    move(*center()); yield 0.3
    tear_panel("SIM_PT_goes_away"); yield 0.8
    yield from park()
    bpy.utils.unregister_class(SIM_PT_goes_away)
    yield 0.8
    check("on the list", len(stored()) == 1, stored())
    bpy.utils.register_class(SIM_PT_goes_away)
    yield 0.8
    yield from park()
    check("back as soon as the type is", stored() == {}, stored())
    bpy.utils.unregister_class(SIM_PT_goes_away)
    yield 0.3


SC["review_register_returns"] = s_review_register_returns


def s_review_many():
    """More than a pass creates: the rest follow, and waiting ones don't starve them."""
    yield from begin()
    entries = {}
    common = {"version": 1, "from_region": False, "width": 0.0, "width_default": 0.0,
              "width_chrome": 0.0, "winid": 1, "space": 1, "region": 1, "area_index": -1,
              "collapsed": False, "height": 0.0, "scroll": 0.0, "kind": "PANEL",
              "idname": "SIM_PT_field"}
    # Waiting for a mode, at the head of the list, more than a pass's worth.
    for i in range(70):
        entries[str(i)] = dict(common, mode="sculpt", x=300.0, y=300.0)
    for i in range(70, 150):
        entries[str(i)] = dict(common, mode="objectmode", x=100.0 + i, y=100.0 + i)
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = entries
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 2.5
    yield from park()
    modes = [e.get("mode") for e in stored().values()]
    log("left", len(modes))
    check("only the waiting ones are left", modes == ["sculpt"] * 70, len(modes))


SC["review_many"] = s_review_many


def s_review_deleted_workspace():
    """A workspace deleted as an ID takes its hidden pins with it."""
    yield from begin()
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces
                 if ws != home and any(a.type == "VIEW_3D" for a in ws.screens[0].areas))
    w.workspace = other; yield 0.8
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.menu_tear_off(menu_idname="VIEW3D_MT_object")
    yield 0.8
    w.workspace = home; yield 0.8
    yield from park()
    bpy.data.batch_remove([other]); yield 0.8
    yield from park()
    path = store_path("deleted")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    entries = [e for ws in bpy.data.workspaces for e in stored(ws).values()]
    check("nothing left of it", entries == [], entries)


SC["review_deleted_workspace"] = s_review_deleted_workspace


def s_review_datatransfer():
    """A pinned Data Transfer dropdown, with an object active that has no vertex groups."""
    yield from begin()
    ob = bpy.context.view_layer.objects.active
    ob.vertex_groups.new(name="Group")
    mod = ob.modifiers.new("DT", "DATA_TRANSFER")
    mod.use_vert_data = True
    mod.data_types_verts = {"VGROUP_WEIGHTS"}
    with bpy.context.temp_override(**override()):
        bpy.ops.object.empty_add(location=(2, 2, 2))
    empty = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = ob
    yield 0.3
    r = tear_enum(id_type=ID_OB, session_uid=ob.session_uid,
                  data_path='modifiers["DT"].layers_vgroup_select_dst')
    log("tear", r)
    yield 0.8
    bpy.context.view_layer.objects.active = empty
    area_redraw(); yield 0.5
    bpy.context.scene.frame_current += 1; yield 1.0
    yield from park()
    check("it survives another object being active", True)


SC["review_datatransfer"] = s_review_datatransfer


def s_review_collapsed_edge():
    """A collapsed pin at the right edge is clamped with its real width, so it stays there."""
    yield from begin()
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    y = v[3] - TITLE_MENU
    yield from click(v[2] - PIN_ICON, y)
    x = v[0] + 8
    move(x, y); yield 0.3
    press(x, y); yield 0.1
    move(1590, y); yield 0.3
    move(1590, y); yield 0.3
    release(1590, y); yield 0.3
    yield from park()
    yield from grab("at_edge")
    edge = need(box_bbox("base", "at_edge", (30, y - 15, 1599, y + 15)), "the strip")
    log("at the edge", edge)
    path = store_path("collapsed_edge")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("restored")
    now = need(box_bbox("base", "restored", (30, y - 15, 1599, y + 15)), "the restored strip")
    log("restored", now)
    check("the same right edge", abs(now[2] - edge[2]) <= 2, (edge, now))
    check("the same left edge", abs(now[0] - edge[0]) <= 2, (edge, now))


SC["review_collapsed_edge"] = s_review_collapsed_edge


class SIM_OT_delete_workspace(bpy.types.Operator):
    """Deletes a workspace from a timer, with the event loop in the modal handlers."""
    bl_idname = "sim.delete_workspace"; bl_label = "Sim Delete Workspace"
    target = None
    done = False
    _timer = None

    def invoke(self, context, event):
        wm = context.window_manager
        SIM_OT_delete_workspace._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "TIMER" and SIM_OT_delete_workspace.target:
            bpy.data.batch_remove([SIM_OT_delete_workspace.target])
            SIM_OT_delete_workspace.target = None
            SIM_OT_delete_workspace.done = True
            context.window_manager.event_timer_remove(SIM_OT_delete_workspace._timer)
            return {"FINISHED", "PASS_THROUGH"}
        return {"PASS_THROUGH"}


def s_review2_modal_delete():
    """The pin's handler is next in line when its workspace goes."""
    yield from begin()
    bpy.utils.register_class(SIM_OT_delete_workspace)
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces
                 if ws != home and any(a.type == "VIEW_3D" for a in ws.screens[0].areas))
    w.workspace = other; yield 0.8
    move(*center()); yield 0.3
    with bpy.context.temp_override(**override()):
        bpy.ops.wm.menu_tear_off(menu_idname="VIEW3D_MT_object")
    yield 0.8
    w.workspace = home; yield 0.8
    yield from park()
    SIM_OT_delete_workspace.target = other
    with bpy.context.temp_override(**override()):
        bpy.ops.sim.delete_workspace("INVOKE_DEFAULT")
    yield 1.5
    yield from park()
    check("it ran", SIM_OT_delete_workspace.done)
    # What's tagged has to survive what walks over the handlers next.
    path = store_path("modal_delete")
    yield from save_file(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    entries = [e for ws in bpy.data.workspaces for e in stored(ws).values()]
    check("nothing left of it", entries == [], entries)
    bpy.utils.unregister_class(SIM_OT_delete_workspace)


SC["review2_modal_delete"] = s_review2_modal_delete


def s_review2_hidden_scale():
    """A pin hidden while the scale changes keeps its place on the screen."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    w = win()
    home = w.workspace
    home_name = home.name
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.8
    bpy.context.preferences.view.ui_scale = 1.5
    yield 0.8
    path = store_path("hidden_scale")
    yield from read_store_hidden(path)
    entry = next(iter(stored(bpy.data.workspaces[home_name]).values()), None)
    log("stored", entry)
    # 1.5 times this is where it was on the screen.
    check("x counts for the scale now", entry is not None and abs(entry["x"] * 1.5 - v[0]) <= 2, entry)
    check("y too", entry is not None and abs(entry["y"] * 1.5 - (1000 - v[3])) <= 2, entry)
    bpy.context.preferences.view.ui_scale = 1.0
    yield 0.3


def read_store_hidden(path):
    yield from save_file(path)
    yield from read_file(path)


SC["review2_hidden_scale"] = s_review2_hidden_scale


class SIM_MT_waits(bpy.types.Menu):
    bl_idname = "SIM_MT_waits"; bl_label = "Sim Waits"
    ready = False
    polls = 0

    @classmethod
    def poll(cls, context):
        SIM_MT_waits.polls += 1
        return SIM_MT_waits.ready

    def draw(self, context):
        self.layout.label(text="Ready")


def s_review2_poll_retry():
    """A menu waiting on its poll returns on the next change, and an idle window costs nothing."""
    yield from begin()
    bpy.utils.register_class(SIM_MT_waits)
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = {"0": {
        "version": 1, "kind": "MENU", "idname": "SIM_MT_waits", "winid": 1, "space": 1, "region": 1,
        "area_index": -1, "mode": "objectmode", "x": 300.0, "y": 300.0, "collapsed": False,
        "height": 0.0, "scroll": 0.0}}
    # The list was written by hand, so this is the first chance.
    bpy.context.view_layer.objects.active.select_set(True)
    with bpy.context.temp_override(**override()):
        bpy.ops.object.select_all(action="DESELECT")
    yield 0.8
    check("waiting", len(stored()) == 1, stored())
    polls = SIM_MT_waits.polls
    log("polls so far", polls)
    check("its poll was tried", polls > 0, polls)
    # Idle: nothing changes, so nothing runs it. A pass that made its own notifiers would.
    yield 3.0
    now = SIM_MT_waits.polls
    log("after idling", now)
    check("no polling while idle", now - polls <= 2, (polls, now))
    SIM_MT_waits.ready = True
    with bpy.context.temp_override(**override()):
        bpy.ops.object.select_all(action="SELECT")
    yield 0.8
    check("back on the next change", stored() == {}, stored())
    bpy.utils.unregister_class(SIM_MT_waits)


SC["review2_poll_retry"] = s_review2_poll_retry


def s_review2_hidden_grab():
    """A title drag that ends while the pin is hidden doesn't stick to the cursor afterwards."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    x, y = v[0] + 40, v[3] - TITLE_Y
    move(x, y); yield 0.3
    move(x, y); yield 0.3
    press(x, y); yield 0.1
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    move(x, y); yield 0.3
    release(x, y); yield 0.3
    w.workspace = home; yield 0.8
    # Far from where it was pressed. A stuck drag would carry it along.
    move(x + 200, y - 100); yield 0.3
    move(x + 200, y - 100); yield 0.3
    yield from park()
    yield from grab("after")
    n = rdiff("open", "after", v)
    check("it stayed where it was", n < 100, n)


SC["review2_hidden_grab"] = s_review2_hidden_grab


def s_review2_narrow_shelf():
    """From a very narrow shelf, what isn't layout can be more than the width. That's still valid."""
    yield from setup()
    area().spaces.active.overlay.show_text = False
    C = SIM_PT_cols.state
    yield from open_tab("TOOLS", "SimTear", SIM_PT_cols_anchor.state, C)
    yield from park()
    yield from grab("base")
    group = win().workspace.bl_system_properties_get(do_create=True)
    group["bfa_tear_offs"] = {"0": {
        "version": 1, "kind": "PANEL", "idname": "SIM_PT_cols", "from_region": True, "width": 45.0,
        "width_default": 45.0, "width_chrome": 52.0, "winid": 1, "space": 1, "region": 5,
        "area_index": -1, "mode": "objectmode", "x": 500.0, "y": 300.0, "collapsed": False,
        "height": 0.0, "scroll": 0.0}}
    w = win()
    home = w.workspace
    other = next(ws for ws in bpy.data.workspaces if ws != home)
    w.workspace = other; yield 0.6
    w.workspace = home; yield 1.0
    yield from park()
    check("it's restored, not thrown away", stored() == {}, stored())
    yield from grab("after")
    n = rdiff("base", "after", (30, 25, 1340, 999))
    check("and it shows", n > 300, n)


SC["review2_narrow_shelf"] = s_review2_narrow_shelf


def s_restore_scale():
    """Another UI scale: a stored position means the same thing."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    path = store_path("scale")
    yield from save_file(path)
    yield from click(v[2] - X_ICON, v[3] - TITLE_Y)
    bpy.context.preferences.view.ui_scale = 1.5
    yield 0.8
    yield from park()
    yield from grab("base15")
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from grab("scaled")
    check("off the list", stored() == {}, stored())
    bpy.context.preferences.view.ui_scale = 1.0
    yield 0.3


SC["restore_scale"] = s_restore_scale


def s_restore_memory():
    """No leak from storing, restoring and closing, in a real quit."""
    yield from begin()
    path = store_path("memory")
    panel, menu = yield from pin_and_save(path)
    yield from open_file(path, load_ui=True)
    yield from park()
    yield from save_file(path)
    yield from open_file(path, load_ui=False)
    yield from park()
    yield from finish_with_memory_report()


SC["restore_memory"] = s_restore_memory


def s_restore_startup_a():
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    with open(os.path.join(os.environ["BLENDER_USER_CONFIG"], "state.txt"), "w") as f:
        f.write(",".join(str(i) for i in v))
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.save_homefile()
    yield 0.5


def s_restore_startup_b():
    """A saved startup file: after the splash, the pin is back."""
    with open(os.path.join(os.environ["BLENDER_USER_CONFIG"], "state.txt")) as f:
        v = [int(i) for i in f.read().split(",")]
    yield 2.0
    check("waiting while the splash shows", len(stored()) == 1, stored())
    yield from grab("splash")
    yield from esc()
    x, y = center()
    move(x, y); yield 0.8
    move(*PARK); yield 0.8
    yield from grab("after")
    check("off the list after the splash", stored() == {}, stored())
    n = rdiff("splash", "after", header_box(v))
    check("and it shows, in place", n > 100, n)


SC["restore_startup_a"] = s_restore_startup_a
SC["restore_startup_b"] = s_restore_startup_b


def s_restore_small_a():
    """Saved on a big window, collapsed at the far right and at the bottom."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    yield from grab("open")
    v = need(popup_box("base", "open"), "it opens")
    yield from click(v[2] - PIN_ICON, v[3] - TITLE_Y)
    move(v[0] + 8, v[3] - TITLE_Y); yield 0.3
    press(v[0] + 8, v[3] - TITLE_Y); yield 0.1
    move(1450, 40); yield 0.3
    move(1450, 40); yield 0.3
    release(1450, 40); yield 0.3
    yield from save_file(store_path("small"))


def s_restore_small_b():
    """The same file on a small window: the strip is pulled inside it."""
    yield from setup(cube=False)
    yield from open_file(store_path("small"), load_ui=True)
    yield from park()
    yield from grab("small")
    check("off the list", stored() == {}, stored())
    h, w_px = FRAME["small"].shape[:2]
    log("window", w_px, h)
    check("the window is small", w_px < 1000, w_px)
    entries = stored()
    yield 0.2


SC["restore_small_a"] = s_restore_small_a
SC["restore_small_b"] = s_restore_small_b


def s_store_startup_a():
    yield from begin()
    move(*center()); yield 0.3
    tear_menu("VIEW3D_MT_object"); yield 0.8
    move(center()[0] - 200, center()[1]); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.save_homefile()
    yield 0.5
    check("the session's list stays empty", stored() == {}, stored())


def s_store_startup_b():
    yield 1.0
    entries = stored()
    log("startup", entries)
    check("both are in the startup file", len(entries) == 2, entries)
    kinds = [e.get("kind") for e in entries.values()]
    check("menu, then panel", kinds == ["MENU", "PANEL"], kinds)


SC["store_startup_a"] = s_store_startup_a
SC["store_startup_b"] = s_store_startup_b


def s_store_quit_a():
    """Quits for real, because that's what writes quit.blend."""
    yield from begin()
    move(*center()); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from park()
    check("a pin is open", True)
    yield from finish_with_memory_report()


def s_store_quit_b():
    yield 1.0
    path = os.path.join(os.environ["TEMP"], "quit.blend")
    check("quit.blend is in the sim's own folder", os.path.exists(path), os.environ["TEMP"])
    # Load UI is off in factory settings, and recovering follows it: the session's workspaces stay.
    prefs = bpy.context.preferences.filepaths
    check("Load UI starts off", not prefs.use_load_ui)
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.recover_last_session()
    yield 1.5
    entries = [e for ws in bpy.data.workspaces for e in stored(ws).values()]
    check("recovered with Load UI off: not in the kept workspaces", len(entries) == 0, entries)
    prefs.use_load_ui = True
    # Off, so the list can be read before it restores.
    bpy.context.preferences.use_tear_off = False
    with bpy.context.temp_override(window=win()):
        bpy.ops.wm.recover_last_session()
    yield 1.5
    entries = [e for ws in bpy.data.workspaces for e in stored(ws).values()]
    log("recovered", entries)
    check("recovered with Load UI on: the pin", len(entries) == 1, entries)


SC["store_quit_a"] = s_store_quit_a
SC["store_quit_b"] = s_store_quit_b
