# p3_to_meters.py
import math

def _dot(a,b): return a[0]*b[0] + a[1]*b[1]
def _sub(a,b): return [a[0]-b[0], a[1]-b[1]]
def _add(a,b): return [a[0]+b[0], a[1]+b[1]]
def _mul(a,s): return [a[0]*s, a[1]*s]

class SiteFrame(object):
    def __init__(self, origin, xaxis, yaxis, width, height):
        self.origin = origin
        self.xaxis  = xaxis
        self.yaxis  = yaxis
        self.width  = float(width)
        self.height = float(height)
    def map_uv(self, u, v, margin=0.0):
        iu = margin + u * (1.0 - 2.0*margin)
        iv = margin + v * (1.0 - 2.0*margin)
        px = iu * self.width
        py = iv * self.height
        return _add(self.origin, _add(_mul(self.xaxis, px), _mul(self.yaxis, py)))
    def scale_w(self, wu):  return wu * self.width
    def scale_h(self, hv):  return hv * self.height
    def scale_w_clear(self, wnorm): return wnorm * min(self.width, self.height)

def _unit(v):
    n = math.hypot(v[0], v[1])
    return [v[0]/n, v[1]/n] if n>0 else [1.0, 0.0]

def siteframe_from_P4_site(site, use_oriented_bbox=True):
    b = site.get("buildable", {})
    bt = b.get("type", "")
    if bt == "rectangle":
        w = float(b.get("width_m") or site["boundary"]["width_m"])
        h = float(b.get("height_m") or site["boundary"]["height_m"])
        return SiteFrame([0.0,0.0], [1.0,0.0], [0.0,1.0], w, h)

    boundary = site.get("boundary", {})
    verts = boundary.get("vertices_xy")
    if not verts:
        return SiteFrame([0,0],[1,0],[0,1], 20.0, 20.0)

    if not use_oriented_bbox:
        xs = [p[0] for p in verts]; ys = [p[1] for p in verts]
        minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
        return SiteFrame([minx,miny], [1,0], [0,1], maxx-minx, maxy-miny)

    cx = sum(p[0] for p in verts)/len(verts)
    cy = sum(p[1] for p in verts)/len(verts)
    sxx = syy = sxy = 0.0
    for x,y in verts:
        dx, dy = x-cx, y-cy
        sxx += dx*dx; syy += dy*dy; sxy += dx*dy
    t = sxx + syy
    d = math.sqrt(max(0.0, (sxx - syy)**2 + 4*sxy*sxy))
    lmax = 0.5*(t + d)
    vx = 1.0
    vy = 0.0 if abs(sxy) < 1e-9 else -(sxx - lmax)/sxy
    xaxis = _unit([vx, vy]); yaxis = [-xaxis[1], xaxis[0]]
    projs_x = []; projs_y = []
    for x,y in verts:
        p = [x - cx, y - cy]
        projs_x.append(_dot(p, xaxis)); projs_y.append(_dot(p, yaxis))
    minX, maxX = min(projs_x), max(projs_x)
    minY, maxY = min(projs_y), max(projs_y)
    w = maxX - minX; h = maxY - minY
    corner = _add([cx, cy], _add(_mul(xaxis, minX), _mul(yaxis, minY)))
    return SiteFrame(corner, xaxis, yaxis, w, h)

def scale_p3_to_site(p3_obj, p4_site, return_corridor=True):
    sf = siteframe_from_P4_site(p4_site, use_oriented_bbox=True)
    bounds = p3_obj.get("bounds", {})
    margin = float(bounds.get("margin", 0.0))

    rooms_out = []
    for n in p3_obj.get("nodes", []):
        name = n.get("role") or n.get("id")
        u,v   = n.get("center", [0.5,0.5])
        wu,hv = n.get("size", [0.2,0.2])
        ctr = sf.map_uv(u, v, margin)
        w_m = sf.scale_w(wu); h_m = sf.scale_h(hv)
        ox = ctr[0] - 0.5*w_m; oy = ctr[1] - 0.5*h_m
        rooms_out.append({
            "name": name,
            "w": round(w_m, 3),
            "h": round(h_m, 3),
            "origin": [round(ox, 3), round(oy, 3)]
        })

    result = {"rooms": rooms_out}

    if return_corridor:
        routing = p3_obj.get("routing", {}) or {}
        if "polyline" in routing:
            pts_xy = [ sf.map_uv(u,v, margin) for (u,v) in routing["polyline"] ]
            width_norm = float(routing.get("width", 0.08))
            width_m    = sf.scale_w_clear(width_norm)
            result["corridor"] = {
                "centerline": [[round(x,3), round(y,3)] for (x,y) in pts_xy],
                "width": round(width_m, 3)
            }
    return result
