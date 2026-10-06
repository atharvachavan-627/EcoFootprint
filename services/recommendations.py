TIPS = {
 'transport': ["Shift two weekly car or bike trips to metro, bus or train: public transport emits roughly a third as much per km.",
               "Combine errands and carpool; keep tyres inflated to protect fuel efficiency.", "Swap one short flight a year for a train journey where possible."],
 'energy': ["Set the AC to 24-26°C and service it yearly; each hour less per day trims home emissions.",
            "Switch to 5-star appliances and LED lighting, and unplug idle chargers.", "Ask your housing society or provider about rooftop solar or a green tariff."],
 'food': ["Replace a few meat meals per week with dal, legumes or vegetables.", "Plan meals and store food well to cut food waste.", "Buy seasonal, local produce."],
 'lifestyle': ["Wait 30 days before non-essential purchases, and buy second-hand clothing.", "Bundle online orders and avoid express delivery.", "Carry a reusable bag and bottle; segregate dry waste for recycling."],
 'ewaste': ["Repair or upgrade before replacing: manufacturing is most of a device's footprint.", "Choose refurbished or certified pre-owned devices.", "Hand old electronics only to authorised e-waste recyclers or collection drives."]}

def recommend(big, d, cats, ew_score):
    out = list(TIPS[big])
    if d.get('disposal') in ('general', 'unknown'):
        out.append("E-waste: never bin old electronics. Use an authorised e-waste collection centre or a brand take-back programme.")
    if d.get('battery_recycle') not in (True, 'yes'):
        out.append("E-waste: drop used batteries at battery collection points; they contain heavy metals and fire risks.")
    if d.get('repair') == 'never':
        out.append("E-waste: try repairing one device before replacing it; it keeps materials in use longer.")
    if ew_score >= 80:
        out.append("Your e-waste habits are strong. Share them, or run a collection drive on campus.")
    return out[:6]
