"""Transparent footprint engine. All values kg CO2e internally."""
import json, os
from .recommendations import recommend
F = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'emission_factors.json')))

class ValidationError(ValueError):
    pass

def _num(d, k, lo, hi):
    try:
        v = float(d.get(k))
    except (TypeError, ValueError):
        raise ValidationError(f"{k.replace('_', ' ').capitalize()} must be a number.")
    if not lo <= v <= hi:
        raise ValidationError(f"{k.replace('_', ' ').capitalize()} must be between {lo} and {hi}.")
    return v

def _opt(d, k, options):
    v = d.get(k)
    if v not in options:
        raise ValidationError(f"Choose a valid option for {k.replace('_', ' ')}.")
    return v

def calculate(d):
    if not isinstance(d, dict):
        raise ValidationError("No input received.")
    T, E, Fd, L, W = F['transport'], F['energy'], F['food'], F['lifestyle'], F['ewaste']
    g = F['grid_kg_per_kwh']
    mode = _opt(d, 'mode', ['car', 'motorcycle', 'bus', 'train', 'metro', 'bicycle', 'walking'])
    fuel = _opt(d, 'fuel', ['petrol', 'diesel', 'cng', 'electric'])
    km = _num(d, 'daily_km', 0, 500) * _num(d, 'days_week', 0, 7) * 52
    eff = _num(d, 'efficiency', 1, 100)
    if mode in ('car', 'motorcycle'):
        vehicle = km * T['ev_kwh_per_km'][mode] * g if fuel == 'electric' else km / eff * T['fuel_kg_per_unit'][fuel]
    else:
        vehicle = km * T['per_km'][mode]
    public = _num(d, 'pub_km_week', 0, 2000) * 52 * T['public_avg_per_km']
    flights = _num(d, 'flights_short', 0, 100) * T['flight_short'] + _num(d, 'flights_long', 0, 50) * T['flight_long']
    hh = _num(d, 'household', 1, 20)
    ren = _num(d, 'renewable_pct', 0, 100) / 100
    electricity = _num(d, 'kwh_month', 0, 5000) * 12 * g * (1 - ren) / hh
    ac = _num(d, 'ac_hours', 0, 24) * E['ac_kw'] * E['ac_days'] * g * (1 - ren) / hh
    lpg = _num(d, 'lpg_cylinders', 0, 50) * E['lpg_kg_per_cylinder'] * E['lpg_kg_co2_per_kg'] / hh
    gas = _num(d, 'gas_m3_month', 0, 500) * 12 * E['gas_kg_per_m3'] / hh
    diet = _opt(d, 'diet', list(Fd['diet_base']))
    mult = Fd['waste'][_opt(d, 'food_waste', list(Fd['waste']))] * Fd['origin'][_opt(d, 'origin', list(Fd['origin']))]
    meals = _num(d, 'meat_meals', 0, 21)
    dietp, meat = Fd['diet_base'][diet] * mult, meals * 52 * Fd['meat_meal_kg'] * mult
    recyc = L['recycling_multiplier'][_opt(d, 'recycling', list(L['recycling_multiplier']))]
    life = (_num(d, 'clothes_month', 0, 100) * 12 * L['clothing_item_kg'] + _num(d, 'electronics_year', 0, 50) * L['electronics_kg']
            + L['plastic'][_opt(d, 'plastic', list(L['plastic']))] + _num(d, 'online_month', 0, 200) * 12 * L['online_order_kg']) * recyc
    dev = _num(d, 'devices_replaced', 0, 30)
    repair = _opt(d, 'repair', list(W['repair_mult']))
    refurb = _opt(d, 'refurbished', list(W['refurb_mult']))
    disp = _opt(d, 'disposal', list(W['disposal_penalty_per_device']))
    batt, cert = d.get('battery_recycle') in (True, 'yes'), d.get('certified_center') in (True, 'yes')
    ew_prod = dev * W['device_embodied_kg'] * W['repair_mult'][repair] * W['refurb_mult'][refurb]
    ew_disp = dev * W['disposal_penalty_per_device'][disp] + (0 if batt else W['battery_penalty'])
    cats = {'transport': vehicle + public + flights, 'energy': electricity + ac + lpg + gas,
            'food': dietp + meat, 'lifestyle': life, 'ewaste': ew_prod + ew_disp}
    total = sum(cats.values())
    ew_score = ({'always': 20, 'sometimes': 10, 'never': 0}[repair] + {'yes': 15, 'sometimes': 8, 'no': 0}[refurb]
                + {'certified': 30, 'collection': 24, 'donation': 24, 'general': 0, 'unknown': 5}[disp]
                + (10 if batt else 0) + (10 if cert else 0) + max(0, 15 - round(dev * 3)))
    sc = lambda kg, t: round(max(0, min(100, 100 * (1 - kg / (2 * t)))))
    comp = {k: sc(cats[k], F['targets_kg'][k]) for k in F['targets_kg']}
    comp['ewaste'] = ew_score
    big = max(cats, key=cats.get)
    parts = dict(vehicle=vehicle, public=public, flights=flights, electricity=electricity + ac, lpg=lpg, gas=gas,
                 diet=dietp, meat=meat, lifestyle=life, ewaste_prod=ew_prod, ewaste_disp=ew_disp)
    return {
        'parts': {k: round(v, 2) for k, v in parts.items()},
        'categories': {k: round(v, 2) for k, v in cats.items()},
        'percent': {k: round(v / total * 100, 1) if total else 0 for k, v in cats.items()},
        'total_kg': round(total, 2), 'total_t': round(total / 1000, 2),
        'eco_score': round(sum(comp.values()) / 5), 'score_parts': comp, 'ewaste_score': ew_score,
        'biggest': big, 'recommendations': recommend(big, d, cats, ew_score),
        'disclaimer': 'This calculator provides an estimate based on predefined emission factors and user-provided information.'}
