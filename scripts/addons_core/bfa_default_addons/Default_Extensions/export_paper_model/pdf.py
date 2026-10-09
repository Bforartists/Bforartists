# pdf.py: export to PDF written in plain Python

from itertools import chain, repeat
from zlib import compress
from mathutils import Vector
from .unfolder import Sticker, Arrow, NumberAlone, Exporter

class Pdf(Exporter):
    """Simple PDF exporter"""

    mm_to_pt = 72 / 25.4
    character_width_packed = {
        191: "'", 222: 'ijl\x82\x91\x92', 278: '|¦\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !,./:;I[\\]ft\xa0·ÌÍÎÏìíîï',
        333: '()-`r\x84\x88\x8b\x93\x94\x98\x9b¡¨\xad¯²³´¸¹{}', 350: '\x7f\x81\x8d\x8f\x90\x95\x9d', 365: '"ºª*°', 469: '^', 500: 'Jcksvxyz\x9a\x9eçýÿ', 584: '¶+<=>~¬±×÷', 611: 'FTZ\x8e¿ßø',
        667: '&ABEKPSVXY\x8a\x9fÀÁÂÃÄÅÈÉÊËÝÞ', 722: 'CDHNRUwÇÐÑÙÚÛÜ', 737: '©®', 778: 'GOQÒÓÔÕÖØ', 833: 'Mm¼½¾', 889: '%æ', 944: 'W\x9c', 1000: '\x85\x89\x8c\x97\x99Æ', 1015: '@', }
    character_width = {c: value for (value, chars) in character_width_packed.items() for c in chars}

    def __init__(self, properties):
        self.styles = {}
        super().__init__(properties)

    def text_width(self, text, scale=None):
        return (scale or self.text_size) * sum(self.character_width.get(c, 556) for c in text) / 1000

    def styling(self, name, do_stroke=True):
        s, m, l = (length * self.style.line_width * 1000 for length in (1, 4, 9))
        format_style = {'SOLID': [], 'DOT': [s, m], 'DASH': [m, l], 'LONGDASH': [l, m], 'DASHDOT': [l, m, s, m]}
        style, color, width = (getattr(self.style, f"{name}_{arg}", None) for arg in ("style", "color", "width"))
        style = style or 'SOLID'
        result = ["q"]
        if do_stroke:
            result += [
                "[ " + " ".join("{:.3f}".format(num) for num in format_style[style]) + " ] 0 d",
                "{0:.3f} {1:.3f} {2:.3f} RG".format(*color),
                "{:.3f} w".format(self.style.line_width * 1000 * width),
                ]
        else:
            result.append("{0:.3f} {1:.3f} {2:.3f} rg".format(*color))
        if color[3] < 1:
            style_name = "R{:03}".format(round(1000 * color[3]))
            result.append("/{} gs".format(style_name))
            if style_name not in self.styles:
                self.styles[style_name] = {"CA": color[3], "ca": color[3]}
        return result

    @classmethod
    def encode_image(cls, bpy_image):
        data = bytes(int(255 * px) for (i, px) in enumerate(bpy_image.pixels) if i % 4 != 3)
        image = {
            "Type": "XObject", "Subtype": "Image", "Width": bpy_image.size[0], "Height": bpy_image.size[1],
            "ColorSpace": "DeviceRGB", "BitsPerComponent": 8, "Interpolate": True,
            "Filter": ["ASCII85Decode", "FlateDecode"], "stream": data}
        return image

    def write(self, mesh, filename):
        def format_dict(obj, refs=tuple()):
            content = "".join(f"/{key} {format_value(value, refs)}\n" for (key, value) in obj.items())
            return f"<< {content} >>"

        def line_through(seq):
            fmt = "{0.x:.6f} {0.y:.6f} {1} ".format
            return "".join(fmt(1000*co, cmd) for (co, cmd) in zip(seq, chain("m", repeat("l"))))

        def format_value(value, refs=tuple()):
            if value in refs:
                return f"{refs.index(value) + 1} 0 R"
            if type(value) is dict:
                return format_dict(value, refs)
            if type(value) in (list, tuple):
                return "[ " + " ".join(format_value(item, refs) for item in value) + " ]"
            if type(value) is int:
                return str(value)
            if type(value) is float:
                return f"{value:.6f}"
            if type(value) is bool:
                return "true" if value else "false"
            return f"/{value}"  # this script can output only PDF names, no strings

        def write_object(index, obj, refs, f, stream=None):
            byte_count = f.write(f"{index} 0 obj\n".encode())
            if type(obj) is not dict:
                stream, obj = obj, {}
            elif "stream" in obj:
                stream = obj.pop("stream")
            if stream:
                obj["Filter"] = "FlateDecode"
                stream = encode(stream)
                obj["Length"] = len(stream)
            byte_count += f.write(format_dict(obj, refs).encode())
            if stream:
                byte_count += f.write(b"\nstream\n")
                byte_count += f.write(stream)
                byte_count += f.write(b"\nendstream")
            return byte_count + f.write(b"\nendobj\n")

        def encode(data):
            if hasattr(data, "encode"):
                data = data.encode()
            return compress(data)

        page_size_pt = 1000 * self.mm_to_pt * self.page_size
        reset_style = ["Q"]  # graphic command for later use
        root = {"Type": "Pages", "MediaBox": [0, 0, page_size_pt.x, page_size_pt.y], "Kids": []}
        catalog = {"Type": "Catalog", "Pages": root}
        font = {
            "Type": "Font", "Subtype": "Type1", "Name": "F1",
            "BaseFont": "Helvetica", "Encoding": "MacRomanEncoding"}
        objects = [root, catalog, font]

        for page in mesh.pages:
            commands = ["{0:.6f} 0 0 {0:.6f} 0 0 cm".format(self.mm_to_pt)]
            resources = {"Font": {"F1": font}, "ExtGState": self.styles, "ProcSet": ["PDF"]}
            if any(island.embedded_image for island in page.islands):
                resources["XObject"] = {}
                resources["ProcSet"].append("ImageC")
            for island in page.islands:
                commands.append("q 1 0 0 1 {0.x:.6f} {0.y:.6f} cm".format(1000*(self.margin + island.pos)))
                if island.embedded_image:
                    identifier = f"I{len(resources['XObject']) + 1}"
                    commands.append(self.command_image.format(1000 * island.bounding_box, identifier))
                    objects.append(island.embedded_image)
                    resources["XObject"][identifier] = island.embedded_image

                if island.title:
                    commands += self.styling("text", do_stroke=False)
                    commands.append(self.command_label.format(
                        size=1000*self.text_size,
                        x=500 * (island.bounding_box.x - self.text_width(island.title)),
                        y=1000 * 0.2 * self.text_size,
                        label=island.title))
                    commands += reset_style

                data_markers, data_stickerfill = [], []
                for marker in island.markers:
                    if isinstance(marker, Sticker):
                        data_stickerfill.append(line_through(marker.points) + "f")
                        if marker.text:
                            data_markers.append(self.command_sticker.format(
                                label=marker.text,
                                pos=1000*marker.center,
                                mat=marker.rot,
                                align=-500 * self.text_width(marker.text, marker.width),
                                size=1000*marker.width))
                    elif isinstance(marker, Arrow):
                        size = 1000 * marker.size
                        position = 1000 * (marker.center + marker.size * marker.rot @ Vector((0, -0.9)))
                        data_markers.append(self.command_arrow.format(
                            index=marker.text,
                            arrow_pos=1000 * marker.center,
                            pos=position - 1000 * Vector((0.5 * self.text_width(marker.text), 0.4 * self.text_size)),
                            mat=size * marker.rot,
                            size=size))
                    elif isinstance(marker, NumberAlone):
                        position = 1000*marker.center - 1000 * marker.rot @ Vector((0.5 * self.text_width(marker.text), 0))
                        data_markers.append(self.command_number.format(
                            label=marker.text,
                            pos=position,
                            mat=marker.rot,
                            size=1000*marker.size))

                data_outer, data_convex, data_concave, data_freestyle = ([] for i in range(4))
                outer_edges = set(island.boundary)
                while outer_edges:
                    data_loop = []
                    uvedge = outer_edges.pop()
                    while 1:
                        if uvedge.sticker:
                            data_loop.extend(uvedge.sticker.points[1:])
                        else:
                            vertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                            data_loop.append(vertex.co)
                        uvedge = uvedge.neighbor_right
                        try:
                            outer_edges.remove(uvedge)
                        except KeyError:
                            break
                    data_outer.append(line_through(data_loop) + "s")

                for loop, uvedge in island.edges.items():
                    edge = mesh.edges[loop.edge]
                    if edge.is_cut(uvedge.uvface.face) and not uvedge.sticker:
                        continue
                    data_uvedge = line_through((uvedge.va.co, uvedge.vb.co)) + "S"
                    if edge.freestyle:
                        data_freestyle.append(data_uvedge)
                    # each uvedge exists in two opposite-oriented variants; we want to add each only once
                    if uvedge.sticker or uvedge.uvface.flipped != (id(uvedge.va) > id(uvedge.vb)):
                        if abs(edge.angle) > self.angle_epsilon:
                            edge_group = data_convex if edge.is_convex() else data_concave
                            edge_group.append(data_uvedge)
                if island.is_inside_out:
                    data_convex, data_concave = data_concave, data_convex

                if data_stickerfill and self.style.sticker_color[3] > 0:
                    commands += chain(self.styling("sticker", do_stroke=False), data_stickerfill, reset_style)
                if data_freestyle:
                    commands += chain(self.styling("freestyle"), data_freestyle, reset_style)
                if (data_convex or data_concave) and not self.pure_net and self.style.use_inbg:
                    commands += chain(self.styling("inbg"), data_convex, data_concave, reset_style)
                if data_convex:
                    commands += chain(self.styling("convex"), data_convex, reset_style)
                if data_concave:
                    commands += chain(self.styling("concave"), data_concave, reset_style)
                if data_outer:
                    if not self.pure_net and self.style.use_outbg:
                        commands += chain(self.styling("outbg"), data_outer, reset_style)
                    commands += chain(self.styling("outer"), data_outer, reset_style)
                if data_markers:
                    commands += chain(self.styling("text", do_stroke=False), data_markers, reset_style)
                commands += reset_style  # return from island to page coordinates
            content = "\n".join(commands)
            page = {"Type": "Page", "Parent": root, "Contents": content, "Resources": resources}
            root["Kids"].append(page)
            objects += page, content
            objects.extend(self.styles.values())

        root["Count"] = len(root["Kids"])
        with open(filename, "wb+") as f:
            xref_table = []
            position = 0
            position += f.write(b"%PDF-1.4\n")
            position += f.write(b"%\xde\xad\xbe\xef\n")
            for index, obj in enumerate(objects, 1):
                xref_table.append(position)
                position += write_object(index, obj, objects, f)
            xref_pos = position
            f.write("xref\n0 {}\n".format(len(xref_table) + 1).encode())
            f.write("{:010} {:05} f\r\n".format(0, 65535).encode())
            for position in xref_table:
                f.write("{:010} {:05} n\r\n".format(position, 0).encode())
            f.write(b"trailer\n")
            f.write(format_dict({"Size": len(xref_table) + 1, "Root": catalog}, objects).encode())
            f.write("\nstartxref\n{}\n%%EOF\n".format(xref_pos).encode())

    command_label = "q /F1 {size:.6f} Tf BT {x:.6f} {y:.6f} Td ({label}) Tj ET Q"
    command_image = "q {0.x:.6f} 0 0 {0.y:.6f} 0 0 cm 1 0 0 -1 0 1 cm /{1} Do Q"
    command_sticker = "q /F1 {size:.6f} Tf {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {pos.x:.6f} {pos.y:.6f} cm BT {align:.6f} 0 Td ({label}) Tj ET Q"
    command_arrow = "q /F1 {size:.6f} Tf BT {pos.x:.6f} {pos.y:.6f} Td ({index}) Tj ET {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {arrow_pos.x:.6f} {arrow_pos.y:.6f} cm 0 0 m 1 -1 l 0 -0.25 l -1 -1 l f Q"
    command_number = "q /F1 {size:.6f} Tf {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {pos.x:.6f} {pos.y:.6f} cm BT ({label}) Tj ET Q"
