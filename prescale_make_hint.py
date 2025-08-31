# prescale_make_hint.py
import json, argparse
from p3_to_meters import scale_p3_to_site

def load_by_id(items, id_):
    id_ = int(id_)
    for it in items:
        if int(it["id"]) == id_: return it
    raise ValueError("ID {} not found".format(id_))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p3_file", default="P3_planning.json")
    ap.add_argument("--p4_file", default="P4_sites.json")
    ap.add_argument("--p3_id", required=True, type=int, help="Planning type id (P3)")
    ap.add_argument("--p4_id", required=True, type=int, help="Site id (P4)")
    ap.add_argument("--out", default=None, help="Output hint JSON path")
    ap.add_argument("--no_corridor", action="store_true", help="Skip corridor in hint")
    args = ap.parse_args()

    P3 = json.load(open(args.p3_file, "r"))["P3_PlanningTypes"]
    P4 = json.load(open(args.p4_file, "r"))["P4_SiteBoundaries"]
    p3 = load_by_id(P3, args.p3_id)
    p4 = load_by_id(P4, args.p4_id)

    hint = scale_p3_to_site(p3, p4, return_corridor=(not args.no_corridor))

    out_path = args.out or f"hint_p3_{args.p3_id}_p4_{args.p4_id}.json"
    with open(out_path, "w") as f:
        json.dump(hint, f, indent=2)
    print("✓ Wrote", out_path)

if __name__ == "__main__":
    main()
