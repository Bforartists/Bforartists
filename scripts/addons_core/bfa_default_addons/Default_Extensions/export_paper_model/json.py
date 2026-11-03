import json
from .unfolder import Exporter

def fround(x):
    return round(x, 6)

class Json(Exporter):
    """JSON exporter for cutting and folding edges"""

    def format_vertex(self, vector):
        return [
            fround(vector.x + self.margin.x),
            fround(self.page_size.y - vector.y - self.margin.y)
        ]

    def format_uvedge(self, loop, uvedge, island):
        a = self.format_vertex(uvedge.va.co + island.pos)
        b = self.format_vertex(uvedge.vb.co + island.pos)
        face1 = loop.face
        face2 = loop.link_loop_radial_next.face
        return [
            [a[0], a[1]], [b[0], b[1]],
            uvedge in island.boundary,
            bool(uvedge.sticker),
            [fround(v) for v in face1.normal],
            [fround(v) for v in face2.normal] if face2 is not face1 else None
        ]

    def write(self, mesh, filename):
        with open(filename, "w") as f:
            indent = 0
            def writeline(line):
                nonlocal indent
                if line[:1] == "}":
                    indent -= 1
                print("  " * indent + line, file=f)
                if line == "{":
                    indent += 1

            def separate(seq, separator=","):
                nonlocal indent
                indent += 1
                for i, item in enumerate(seq):
                    yield item, (separator if i < len(seq) - 1 else "")
                indent -= 1

            writeline("{")
            writeline('"fields": "[x1, y1], [x2, y2], is_boundary, has_sticker, self_normal, other_normal",')
            writeline(f'"page_size": [{fround(self.page_size.x)}, {fround(self.page_size.y)}],')
            writeline('"pages": [')
            for page, psep in separate(mesh.pages):
                writeline('[')
                for island, isep in separate(page.islands):
                    writeline("{")
                    writeline(f'"name": "{island.title or ""}",')
                    writeline('"edges": [')
                    for (loop, uvedge), esep in separate(island.edges.items()):
                         # each uvedge exists in two opposite-oriented variants; we want to add each only once
                        if uvedge.uvface.flipped != (id(uvedge.va) > id(uvedge.vb)):
                            edge_data = self.format_uvedge(loop, uvedge, island)
                            writeline(f'{json.dumps(edge_data)}{esep}')
                    writeline("]")  # edges
                    writeline(f'}}{isep}')  # island
                writeline(f']{psep}')  # page
            writeline("]")  # pages
            writeline("}")
