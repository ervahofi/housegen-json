import json
from copy import deepcopy

# ---- load datasets from files ----
with open("P1_locations.json","r") as f: P1 = json.load(f)["P1_Locations"]
with open("P2_families.json","r")  as f: P2 = json.load(f)["P2_FamilyTypologies"]
with open("P3_planning.json","r")  as f: P3 = json.load(f)["P3_PlanningTypes"]
with open("P4_sites.json","r")     as f: P4 = json.load(f)["P4_SiteBoundaries"]
with open("oat_template.json","r") as f: T  = json.load(f)

def index_by_id(items): return {int(it["id"]): it for it in items}

IDX = {
  "P1_Locations":        index_by_id(P1),
  "P2_FamilyTypologies": index_by_id(P2),
  "P3_PlanningTypes":    index_by_id(P3),
  "P4_SiteBoundaries":   index_by_id(P4),
}

BL = T["baseline"]
sel = {
  "location": IDX["P1_Locations"][BL["P1_Locations_id"]],
  "family":   IDX["P2_FamilyTypologies"][BL["P2_FamilyTypologies_id"]],
  "planning": IDX["P3_PlanningTypes"][BL["P3_PlanningTypes_id"]],
  "site":     IDX["P4_SiteBoundaries"][BL["P4_SiteBoundaries_id"]],
}

def fill_template(tpl, c):
  out = tpl
  out = out.replace("{{location.city}}",    c["location"]["city"])
  out = out.replace("{{location.country}}", c["location"]["country"])
  out = out.replace("{{location.climate}}", c["location"]["climate"])
  out = out.replace("{{family.family}}",    c["family"]["family"])
  out = out.replace("{{family.profession}}",c["family"]["profession"])
  out = out.replace("{{planning.name}}",    c["planning"]["name"])
  routing_type = c["planning"].get("routing",{}).get("type","corridor")
  out = out.replace("{{planning.routing.type}}", routing_type)
  out = out.replace("{{site.name}}",        c["site"]["name"])
  return out

def filtered_ids(param, ids_spec, filt):
  all_idx = IDX[param]
  chosen = list(all_idx.keys()) if ids_spec in ("*", None) else [int(i) for i in ids_spec if int(i) in all_idx]
  if filt and param=="P1_Locations":
    climates = set(filt.get("climate_in", []))
    if climates:
      chosen = [i for i in chosen if all_idx[i].get("climate") in climates]
  return sorted(chosen)

cases = []
case_counter = 1

if T.get("include_control_case", False):
  ctx = deepcopy(sel)
  user_prompt = fill_template(T["llm_prompt"]["user_template"], ctx)
  cases.append({
    "case_id": f"CASE_{case_counter:03d}",
    "vary": None,
    "selection": ctx,
    "llm": {
      "system": T["llm_prompt"].get("system",""),
      "user": user_prompt,
      "schema_hint": T["llm_prompt"].get("output_schema_hint",{})
    }
  })
  case_counter += 1

for sweep in T["sweeps"]:
  param = sweep["parameter"]
  ids   = sweep.get("ids","*")
  filt  = sweep.get("filter")

  for choice_id in filtered_ids(param, ids, filt):
    ctx = deepcopy(sel)
    if param == "P1_Locations":        ctx["location"] = IDX[param][choice_id]
    elif param == "P2_FamilyTypologies":ctx["family"]   = IDX[param][choice_id]
    elif param == "P3_PlanningTypes":   ctx["planning"] = IDX[param][choice_id]
    elif param == "P4_SiteBoundaries":  ctx["site"]     = IDX[param][choice_id]

    user_prompt = fill_template(T["llm_prompt"]["user_template"], ctx)
    cases.append({
      "case_id": f"CASE_{case_counter:03d}",
      "vary": param,
      "choice_id": choice_id,
      "selection": ctx,
      "llm": {
        "system": T["llm_prompt"].get("system",""),
        "user": user_prompt,
        "schema_hint": T["llm_prompt"].get("output_schema_hint",{})
      }
    })
    case_counter += 1

mx = T.get("options",{}).get("max_cases")
if isinstance(mx,int) and mx>0: cases = cases[:mx]

with open("oat_cases.json","w") as f:
  json.dump({"cases": cases}, f, indent=2)

print(f"Generated {len(cases)} cases -> oat_cases.json")
