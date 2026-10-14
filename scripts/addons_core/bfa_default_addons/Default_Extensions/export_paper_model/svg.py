# svg.py: export to SVG

import os.path as os_path
from mathutils import Vector
from .unfolder import Sticker, Arrow, NumberAlone, Exporter

class Svg(Exporter):
    """Simple SVG exporter"""

    @staticmethod
    def encode_image(bpy_image):
        import tempfile
        import base64
        with tempfile.TemporaryDirectory() as directory:
            filename = directory + "/i.png"
            bpy_image.filepath_raw = filename
            bpy_image.save()
            return base64.encodebytes(open(filename, "rb").read()).decode('ascii')

    def format_vertex(self, vector):
        """Return a string with both coordinates of the given vertex."""
        return "{:.6f} {:.6f}".format((vector.x + self.margin.x) * 1000, (self.page_size.y - vector.y - self.margin.y) * 1000)

    def write(self, mesh, filename):
        """Write data to a file given by its name."""
        line_through = " L ".join  # used for formatting of SVG path data
        rows = "\n".join

        dl = ["{:.2f}".format(length * self.style.line_width * 1000) for length in (2, 5, 10)]
        format_style = {
            'SOLID': "none", 'DOT': "{0},{1}".format(*dl), 'DASH': "{1},{2}".format(*dl),
            'LONGDASH': "{2},{1}".format(*dl), 'DASHDOT': "{2},{1},{0},{1}".format(*dl)}

        def format_color(vec):
            return "#{:02x}{:02x}{:02x}".format(round(vec[0] * 255), round(vec[1] * 255), round(vec[2] * 255))

        def format_matrix(matrix):
            return " ".join("{:.6f}".format(cell) for column in matrix for cell in column)

        def path_convert(string, relto=os_path.dirname(filename)):
            assert(os_path)  # check the module was imported
            string = os_path.relpath(string, relto)
            if os_path.sep != '/':
                string = string.replace(os_path.sep, '/')
            return string

        styleargs = {
            name: format_color(getattr(self.style, name)) for name in (
                "outer_color", "outbg_color", "convex_color", "concave_color", "freestyle_color",
                "inbg_color", "sticker_color", "text_color")}
        styleargs.update({
            name: format_style[getattr(self.style, name)] for name in
            ("outer_style", "convex_style", "concave_style", "freestyle_style")})
        styleargs.update({
            name: getattr(self.style, attr)[3] for name, attr in (
                ("outer_alpha", "outer_color"), ("outbg_alpha", "outbg_color"),
                ("convex_alpha", "convex_color"), ("concave_alpha", "concave_color"),
                ("freestyle_alpha", "freestyle_color"),
                ("inbg_alpha", "inbg_color"), ("sticker_alpha", "sticker_color"),
                ("text_alpha", "text_color"))})
        styleargs.update({
            name: getattr(self.style, name) * self.style.line_width * 1000 for name in
            ("outer_width", "convex_width", "concave_width", "freestyle_width", "outbg_width", "inbg_width")})
        for num, page in enumerate(mesh.pages):
            page_filename = "{}_{}.svg".format(filename[:filename.rfind(".svg")], page.name) if len(mesh.pages) > 1 else filename
            with open(page_filename, 'w') as f:
                print(self.svg_base.format(width=self.page_size.x*1000, height=self.page_size.y*1000), file=f)
                print(self.css_base.format(**styleargs), file=f)
                if page.image_path:
                    print(
                        self.image_linked_tag.format(
                            pos="{0:.6f} {0:.6f}".format(self.margin.x*1000),
                            width=(self.page_size.x - 2 * self.margin.x)*1000,
                            height=(self.page_size.y - 2 * self.margin.y)*1000,
                            path=path_convert(page.image_path)),
                        file=f)
                if len(page.islands) > 1:
                    print("<g>", file=f)

                for island in page.islands:
                    print("<g>", file=f)
                    if island.image_path:
                        print(
                            self.image_linked_tag.format(
                                pos=self.format_vertex(island.pos + Vector((0, island.bounding_box.y))),
                                width=island.bounding_box.x*1000,
                                height=island.bounding_box.y*1000,
                                path=path_convert(island.image_path)),
                            file=f)
                    elif island.embedded_image:
                        print(
                            self.image_embedded_tag.format(
                                pos=self.format_vertex(island.pos + Vector((0, island.bounding_box.y))),
                                width=island.bounding_box.x*1000,
                                height=island.bounding_box.y*1000,
                                path=island.image_path),
                            island.embedded_image, "'/>",
                            file=f, sep="")
                    if island.title:
                        print(
                            self.text_tag.format(
                                size=1000 * self.text_size,
                                x=1000 * (island.bounding_box.x*0.5 + island.pos.x + self.margin.x),
                                y=1000 * (self.page_size.y - island.pos.y - self.margin.y - 0.2 * self.text_size),
                                label=island.title),
                            file=f)

                    data_markers, data_stickerfill = [], []
                    for marker in island.markers:
                        if isinstance(marker, Sticker):
                            data_stickerfill.append("M {} Z".format(
                                line_through(self.format_vertex(co + island.pos) for co in marker.points)))
                            if marker.text:
                                data_markers.append(self.text_transformed_tag.format(
                                    label=marker.text,
                                    pos=self.format_vertex(marker.center + island.pos),
                                    mat=format_matrix(marker.rot),
                                    size=marker.width * 1000))
                        elif isinstance(marker, Arrow):
                            size = marker.size * 1000
                            position = marker.center + marker.size * marker.rot @ Vector((0, -0.9))
                            data_markers.append(self.arrow_marker_tag.format(
                                index=marker.text,
                                arrow_pos=self.format_vertex(marker.center + island.pos),
                                scale=size,
                                pos=self.format_vertex(position + island.pos - marker.size * Vector((0, 0.4))),
                                mat=format_matrix(size * marker.rot)))
                        elif isinstance(marker, NumberAlone):
                            data_markers.append(self.text_transformed_tag.format(
                                label=marker.text,
                                pos=self.format_vertex(marker.center + island.pos),
                                mat=format_matrix(marker.rot),
                                size=marker.size * 1000))
                    if data_stickerfill and self.style.sticker_color[3] > 0:
                        print("<path class='sticker' d='", rows(data_stickerfill), "'/>", file=f)

                    data_outer, data_convex, data_concave, data_freestyle = ([] for i in range(4))
                    outer_edges = set(island.boundary)
                    while outer_edges:
                        data_loop = []
                        uvedge = outer_edges.pop()
                        while 1:
                            if uvedge.sticker:
                                data_loop.extend(self.format_vertex(co + island.pos) for co in uvedge.sticker.points[1:])
                            else:
                                vertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                                data_loop.append(self.format_vertex(vertex.co + island.pos))
                            uvedge = uvedge.neighbor_right
                            try:
                                outer_edges.remove(uvedge)
                            except KeyError:
                                break
                        data_outer.append("M {} Z".format(line_through(data_loop)))

                    visited_edges = set()
                    for loop, uvedge in island.edges.items():
                        edge = mesh.edges[loop.edge]
                        if edge.is_cut(uvedge.uvface.face) and not uvedge.sticker:
                            continue
                        data_uvedge = "M {}".format(
                            line_through(self.format_vertex(v.co + island.pos) for v in (uvedge.va, uvedge.vb)))
                        if edge.freestyle:
                            data_freestyle.append(data_uvedge)
                        # each uvedge is in two opposite-oriented variants; we want to add each only once
                        vertex_pair = frozenset((uvedge.va, uvedge.vb))
                        if vertex_pair not in visited_edges:
                            visited_edges.add(vertex_pair)
                            if abs(edge.angle) > self.angle_epsilon:
                                edge_group = data_convex if edge.is_convex() else data_concave
                                edge_group.append(data_uvedge)
                    if island.is_inside_out:
                        data_convex, data_concave = data_concave, data_convex

                    if data_freestyle:
                        print("<path class='freestyle' d='", rows(data_freestyle), "'/>", file=f)
                    if (data_convex or data_concave) and not self.pure_net and self.style.use_inbg:
                        print("<path class='inner_background' d='", rows(data_convex + data_concave), "'/>", file=f)
                    if data_convex:
                        print("<path class='convex' d='", rows(data_convex), "'/>", file=f)
                    if data_concave:
                        print("<path class='concave' d='", rows(data_concave), "'/>", file=f)
                    if data_outer:
                        if not self.pure_net and self.style.use_outbg:
                            print("<path class='outer_background' d='", rows(data_outer), "'/>", file=f)
                        print("<path class='outer' d='", rows(data_outer), "'/>", file=f)
                    if data_markers:
                        print(rows(data_markers), file=f)
                    print("</g>", file=f)

                if len(page.islands) > 1:
                    print("</g>", file=f)
                print("</svg>", file=f)

    image_linked_tag = "<image transform='translate({pos})' width='{width:.6f}' height='{height:.6f}' xlink:href='{path}'/>"
    image_embedded_tag = "<image transform='translate({pos})' width='{width:.6f}' height='{height:.6f}' xlink:href='data:image/png;base64,"
    text_tag = "<text transform='translate({x} {y})' style='font-size:{size:.2f}'><tspan>{label}</tspan></text>"
    text_transformed_tag = "<text transform='matrix({mat} {pos})' style='font-size:{size:.2f}'><tspan>{label}</tspan></text>"
    arrow_marker_tag = "<g><path transform='matrix({mat} {arrow_pos})' class='arrow' d='M 0 0 L 1 1 L 0 0.25 L -1 1 Z'/>" \
        "<text transform='translate({pos})' style='font-size:{scale:.2f}'><tspan>{index}</tspan></text></g>"

    svg_base = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1'
    width='{width:.2f}mm' height='{height:.2f}mm' viewBox='0 0 {width:.2f} {height:.2f}'>"""

    css_base = """<style type="text/css">
    path {{
        fill: none;
        stroke-linecap: butt;
        stroke-linejoin: bevel;
        stroke-dasharray: none;
    }}
    path.outer {{
        stroke: {outer_color};
        stroke-dasharray: {outer_style};
        stroke-dashoffset: 0;
        stroke-width: {outer_width:.2};
        stroke-opacity: {outer_alpha:.2};
    }}
    path.convex {{
        stroke: {convex_color};
        stroke-dasharray: {convex_style};
        stroke-dashoffset:0;
        stroke-width:{convex_width:.2};
        stroke-opacity: {convex_alpha:.2}
    }}
    path.concave {{
        stroke: {concave_color};
        stroke-dasharray: {concave_style};
        stroke-dashoffset: 0;
        stroke-width: {concave_width:.2};
        stroke-opacity: {concave_alpha:.2}
    }}
    path.freestyle {{
        stroke: {freestyle_color};
        stroke-dasharray: {freestyle_style};
        stroke-dashoffset: 0;
        stroke-width: {freestyle_width:.2};
        stroke-opacity: {freestyle_alpha:.2}
    }}
    path.outer_background {{
        stroke: {outbg_color};
        stroke-opacity: {outbg_alpha};
        stroke-width: {outbg_width:.2}
    }}
    path.inner_background {{
        stroke: {inbg_color};
        stroke-opacity: {inbg_alpha};
        stroke-width: {inbg_width:.2}
    }}
    path.sticker {{
        fill: {sticker_color};
        stroke: none;
        fill-opacity: {sticker_alpha:.2};
    }}
    path.arrow {{
        fill: {text_color};
    }}
    text {{
        font-style: normal;
        fill: {text_color};
        fill-opacity: {text_alpha:.2};
        stroke: none;
    }}
    text, tspan {{
        text-anchor:middle;
    }}
    </style>"""

