import os
from datetime import datetime
from typing import Dict, Any, Optional

CLASS_NAMES = [
    'battery', 'biological', 'brown-glass', 'cardboard', 'clothes',
    'green-glass', 'metal', 'paper', 'plastic', 'shoes', 'trash', 'white-glass'
]

# Low-confidence single-item predictions require operator confirmation by default.
DEFAULT_UNCERTAINTY_THRESHOLD = float(os.getenv("ROUTING_UNCERTAINTY_THRESHOLD", "60.0"))

# Authoritative Digital Software Compartment Definitions
COMPARTMENTS = {
    'bin_hazardous': {
        'id': 'bin_hazardous',
        'name': 'Hazardous Waste Depot (E-Waste)',
        'stream': 'Hazardous / Chemical',
        'color': '#ef4444',
        'description': 'Direct hazardous containment; toxic heavy metals and reactive chemistries.'
    },
    'bin_organic': {
        'id': 'bin_organic',
        'name': 'Organic Wet Waste Bin (Compost)',
        'stream': 'Organic / Wet Waste',
        'color': '#10b981',
        'description': 'Biodegradable wet organics routed for anaerobic digestion and compost.'
    },
    'bin_glass_brown': {
        'id': 'bin_glass_brown',
        'name': 'Amber Glass Stream Bin',
        'stream': 'Recyclable / Glass',
        'color': '#92400e',
        'description': 'Amber UV-protective glass sorted for color-pure cullet remelting.'
    },
    'bin_glass_green': {
        'id': 'bin_glass_green',
        'name': 'Green Glass Stream Bin',
        'stream': 'Recyclable / Glass',
        'color': '#047857',
        'description': 'Green container glass routed to color-separated bottle cullet streams.'
    },
    'bin_glass_white': {
        'id': 'bin_glass_white',
        'name': 'Clear Flint Glass Stream Bin',
        'stream': 'Recyclable / Glass',
        'color': '#0284c7',
        'description': 'High-clarity flint glass routed to optical sorting and transparent remelting.'
    },
    'bin_cardboard': {
        'id': 'bin_cardboard',
        'name': 'Cardboard Recycling Bin',
        'stream': 'Recyclable / Dry Waste',
        'color': '#d97706',
        'description': 'Corrugated fiberboard routed for compaction and paper hydrapulping.'
    },
    'bin_paper': {
        'id': 'bin_paper',
        'name': 'Dry Paper Stream Bin',
        'stream': 'Recyclable / Dry Waste',
        'color': '#3b82f6',
        'description': 'Clean cellulose paper routed for de-inking and pulp reclamation.'
    },
    'bin_plastic': {
        'id': 'bin_plastic',
        'name': 'Blue Plastic Recycling Bin',
        'stream': 'Recyclable / Dry Waste',
        'color': '#2563eb',
        'description': 'Polymer containers (PET, HDPE, PP) routed for mechanical shredding and washing.'
    },
    'bin_metal': {
        'id': 'bin_metal',
        'name': 'Metal & Can Stream Bin',
        'stream': 'Recyclable / Dry Waste',
        'color': '#64748b',
        'description': 'Tinplate and aluminum cans routed to electromagnetic sorting and smelter.'
    },
    'bin_textile': {
        'id': 'bin_textile',
        'name': 'Textile Collection Bin',
        'stream': 'Recyclable / Dry Waste',
        'color': '#8b5cf6',
        'description': 'Fabrics and garments routed to shelter donation or fiber shredding.'
    },
    'bin_footwear': {
        'id': 'bin_footwear',
        'name': 'Footwear & Rubber Reclamation Depot',
        'stream': 'Recyclable / Dry Waste',
        'color': '#7c3aed',
        'description': 'Shoes and athletic footwear routed for rubber sole downcycling.'
    },
    'bin_residual': {
        'id': 'bin_residual',
        'name': 'General Residual Waste Bin',
        'stream': 'Non-Recyclable',
        'color': '#4b5563',
        'description': 'Non-recyclable municipal solid waste routed for energy recovery or landfill.'
    },
    'bin_manual_review': {
        'id': 'bin_manual_review',
        'name': 'Manual Review / Quarantine Bin',
        'stream': 'Uncertain / Manual Review',
        'color': '#dc2626',
        'description': 'Diverted items requiring operator inspection to prevent stream contamination.'
    }
}

CLASS_METADATA: Dict[str, Dict[str, Any]] = {
    'battery': {
        'category': 'Hazardous / Other',
        'disposalBin': 'E-Waste / Battery Drop-off Depot',
        'destinationCompartment': COMPARTMENTS['bin_hazardous']['name'],
        'compartmentId': 'bin_hazardous',
        'recommendation': 'Do NOT dispose in general or recycling bins. Contains hazardous heavy metals (lead, cadmium, or lithium). Take to specialized e-waste collection.',
        'routingReason': 'High-priority hazardous isolation: toxic chemistries and fire risk require dedicated e-waste depot handling.',
        'color': COMPARTMENTS['bin_hazardous']['color']
    },
    'biological': {
        'category': 'Organic / Wet Waste',
        'disposalBin': 'Green Organic Compost Bin',
        'destinationCompartment': COMPARTMENTS['bin_organic']['name'],
        'compartmentId': 'bin_organic',
        'recommendation': 'Suitable for biological composting, vermicomposting, and anaerobic digestion. Keep segregated from dry recyclables and non-biodegradable packaging.',
        'routingReason': 'Biodegradable wet biomass: routed to composting chute to prevent contaminating dry recyclable streams.',
        'color': COMPARTMENTS['bin_organic']['color']
    },
    'brown-glass': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Amber Glass Stream Bin',
        'destinationCompartment': COMPARTMENTS['bin_glass_brown']['name'],
        'compartmentId': 'bin_glass_brown',
        'recommendation': 'Rinse thoroughly to remove chemical or liquid residue. Remove metal/plastic caps. 100% infinitely recyclable without quality loss.',
        'routingReason': 'Color-separated glass: brown/amber glass cullet preserved for light-sensitive pharmaceutical and beverage bottle remelting.',
        'color': COMPARTMENTS['bin_glass_brown']['color']
    },
    'green-glass': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Green Glass Stream Bin',
        'destinationCompartment': COMPARTMENTS['bin_glass_green']['name'],
        'compartmentId': 'bin_glass_green',
        'recommendation': 'Rinse thoroughly before disposal. Infinite recyclable glass packaging. Keep unbroken for optical sorting.',
        'routingReason': 'Color-separated glass: green container glass routed to dedicated cullet furnace.',
        'color': COMPARTMENTS['bin_glass_green']['color']
    },
    'white-glass': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Flint / Clear Glass Stream Bin',
        'destinationCompartment': COMPARTMENTS['bin_glass_white']['name'],
        'compartmentId': 'bin_glass_white',
        'recommendation': 'Rinse thoroughly. Clear flint glass is melted to produce new transparent food and beverage containers.',
        'routingReason': 'High-purity clear flint glass: routed to optical sortation to produce high-value transparent glass cullet.',
        'color': COMPARTMENTS['bin_glass_white']['color']
    },
    'cardboard': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Dry Paper & Cardboard Bin',
        'destinationCompartment': COMPARTMENTS['bin_cardboard']['name'],
        'compartmentId': 'bin_cardboard',
        'recommendation': 'Flatten corrugated boxes to optimize storage volume. Keep clean and free of heavy food oils or grease.',
        'routingReason': 'Dry fiberboard stream: corrugated packaging compressed for paper pulp mill reprocessing.',
        'color': COMPARTMENTS['bin_cardboard']['color']
    },
    'paper': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Dry Paper Stream Bin',
        'destinationCompartment': COMPARTMENTS['bin_paper']['name'],
        'compartmentId': 'bin_paper',
        'recommendation': 'Keep clean and dry. Staples do not need removal, but plastic covers should be detached.',
        'routingReason': 'Dry cellulose stream: clean graphic and print paper routed to de-inking and pulp fiber recycling.',
        'color': COMPARTMENTS['bin_paper']['color']
    },
    'plastic': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Blue Plastic Recycling Bin',
        'destinationCompartment': COMPARTMENTS['bin_plastic']['name'],
        'compartmentId': 'bin_plastic',
        'recommendation': 'Empty and rinse container. Check resin code (PETE #1, HDPE #2, PP #5). Avoid compressing with liquid remaining.',
        'routingReason': 'Rigid polymer stream: bottles and containers routed to mechanical washing, flaking, and pelletizing.',
        'color': COMPARTMENTS['bin_plastic']['color']
    },
    'metal': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Metal & Can Stream Bin',
        'destinationCompartment': COMPARTMENTS['bin_metal']['name'],
        'compartmentId': 'bin_metal',
        'recommendation': 'Rinse food residue from cans and foil. Aluminum and tin are highly recyclable with 95% energy savings over virgin smelting.',
        'routingReason': 'Ferrous and non-ferrous metals: routed to magnetic/eddy-current separation for high-efficiency remelting.',
        'color': COMPARTMENTS['bin_metal']['color']
    },
    'clothes': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Textile Collection Bin',
        'destinationCompartment': COMPARTMENTS['bin_textile']['name'],
        'compartmentId': 'bin_textile',
        'recommendation': 'Donate reusable wearable apparel. Place damaged textiles in dedicated fabric reclamation streams.',
        'routingReason': 'Textile recovery: wearable garments sorted for donation triage; worn fabrics shredded for acoustic insulation.',
        'color': COMPARTMENTS['bin_textile']['color']
    },
    'shoes': {
        'category': 'Recyclable / Dry Waste',
        'disposalBin': 'Footwear & Rubber Reclamation Depot',
        'destinationCompartment': COMPARTMENTS['bin_footwear']['name'],
        'compartmentId': 'bin_footwear',
        'recommendation': 'Tie shoe pairs together. Donate wearable pairs or deposit into specialized rubber/composite reclamation bins.',
        'routingReason': 'Composite footwear stream: routed for rubber outsole stripping and athletic surface material recycling.',
        'color': COMPARTMENTS['bin_footwear']['color']
    },
    'trash': {
        'category': 'Non-Recyclable',
        'disposalBin': 'General Residual Waste Bin',
        'destinationCompartment': COMPARTMENTS['bin_residual']['name'],
        'compartmentId': 'bin_residual',
        'recommendation': 'Residual solid waste not currently suited for mechanical recycling. Route for municipal sanitary treatment or energy recovery.',
        'routingReason': 'Inert and composite residual waste: routed to general landfill or thermal waste-to-energy recovery.',
        'color': COMPARTMENTS['bin_residual']['color']
    }
}

def get_current_iso_time() -> str:
    return datetime.utcnow().isoformat() + "Z"

def get_metadata_for_class(class_name: str) -> Dict[str, Any]:
    key = class_name.lower().strip() if class_name else ""
    return CLASS_METADATA.get(key, {
        'category': 'Uncertain / Manual Review',
        'disposalBin': 'Manual Review / Quarantine Bin',
        'destinationCompartment': COMPARTMENTS['bin_manual_review']['name'],
        'compartmentId': 'bin_manual_review',
        'recommendation': 'Unsupported or unrecognized class. Route to inspection table for manual evaluation.',
        'routingReason': f"Unrecognized class '{class_name}'. Diverted to prevent contamination.",
        'color': COMPARTMENTS['bin_manual_review']['color']
    })

def determine_routing(class_name: str, confidence: float, uncertainty_threshold: Optional[float] = None) -> Dict[str, Any]:
    """
    Authoritative single routing policy implementation.
    Maps predictions to clearly defined software compartments, enforces hazardous routing,
    preserves glass subtypes, and provides an explicit quarantine/manual-review path.
    """
    threshold = uncertainty_threshold if uncertainty_threshold is not None else DEFAULT_UNCERTAINTY_THRESHOLD
    key = class_name.lower().strip() if class_name else ""

    # Unknown or unsupported class rejection
    if key not in CLASS_METADATA:
        return {
            'category': 'Uncertain / Manual Review',
            'disposalBin': 'Manual Review / Quarantine Bin',
            'destinationCompartment': COMPARTMENTS['bin_manual_review']['name'],
            'compartmentId': 'bin_manual_review',
            'recommendation': 'Unrecognized waste class. Place in manual inspection area.',
            'routingStatus': 'UNSUPPORTED_CLASS',
            'routingReason': f"Class '{class_name}' is not supported by the 12-class classifier policy. Quarantined for manual visual sorting.",
            'requiresManualReview': True,
            'color': COMPARTMENTS['bin_manual_review']['color']
        }

    meta = CLASS_METADATA[key]

    # Configurable uncertainty threshold check
    if threshold > 0.0 and confidence < threshold:
        return {
            'category': meta['category'],
            'disposalBin': meta['disposalBin'],
            'destinationCompartment': COMPARTMENTS['bin_manual_review']['name'],
            'compartmentId': 'bin_manual_review',
            'recommendation': f"Confidence ({confidence:.1f}%) is below uncertainty threshold ({threshold:.1f}%). Requires operator visual confirmation.",
            'routingStatus': 'UNCERTAIN_MANUAL_REVIEW',
            'routingReason': f"Neural classification confidence ({confidence:.1f}%) fell below operational threshold ({threshold:.1f}%). Diverted to manual review quarantine to avoid contamination.",
            'requiresManualReview': True,
            'color': COMPARTMENTS['bin_manual_review']['color']
        }

    # Authoritative automated routing
    return {
        'category': meta['category'],
        'disposalBin': meta['disposalBin'],
        'destinationCompartment': meta['destinationCompartment'],
        'compartmentId': meta['compartmentId'],
        'recommendation': meta['recommendation'],
        'routingStatus': 'AUTOMATED_ROUTED',
        'routingReason': meta['routingReason'],
        'requiresManualReview': False,
        'color': meta['color']
    }
