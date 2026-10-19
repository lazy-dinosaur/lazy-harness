"""SYNTHETIC catalog writer only; no real business approval is distributed.
The API signature is retained. Non-synthetic plans need a separately trusted external
catalog workflow, not conversion of this fixture into confirmed user intent.
"""
from pathlib import Path
from safety import load, save, digest, Stop
from prepare import AREA_SCOPES, scope_home
from area_catalog import areas

CONFIRMED_AREAS = tuple(('Fixture'+str(i), 'Synthetic offline area '+str(i)) for i in range(1,11))

def check_home(plan, home):
    home = Path(home)
    if plan.get('scope') not in AREA_SCOPES or not plan.get('area_catalog'):
        raise Stop('confirmed catalog only supports area pilots')
    if home.resolve() != scope_home(plan['scope']).resolve() or home.is_symlink():
        raise Stop('confirmed catalog requires exact isolated home')
    if load(home/'plan.json') != plan or load(home/'state/plan.json') != plan:
        raise Stop('exact home/plan.json and import-state identity required')
    return home

def write_confirmed(plan, home, approval):
    if approval != digest(plan): raise Stop('exact plan SHA required')
    home = check_home(plan, home)
    if plan.get('synthetic_only') is not True:
        raise Stop('SYNTHETIC catalog only; trusted external business approval unavailable')
    value = {'areas':[{'name':n,'description':d} for n,d in CONFIRMED_AREAS],
             'confirmed_by_user':True, 'synthetic_only':True,
             'confirmation':'fixture-only, not real business approval', 'plan_sha':approval}
    areas(value)
    path = home/'state/area-catalog.json'
    if path.exists() and load(path) != value: raise Stop('existing confirmed catalog differs; do not overwrite')
    save(path,value)
    return value
