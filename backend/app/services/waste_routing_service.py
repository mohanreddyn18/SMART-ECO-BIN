"""
SMART ECO BIN — Multi-Object Waste Disposal Routing Engine
==========================================================
Classifies individual detected waste items into authoritative disposal streams:
- Wet / Biodegradable Waste (Composting, anaerobic digestion)
- Dry / Recyclable Waste (Paper, cardboard, clean polymers, metal, glass)
- Hazardous Waste (Batteries, e-waste, reactive chemicals)
- Manual Review / Quarantine (Contaminated items, ambiguous/composite materials, low confidence)

Safeguards:
- Never routes toxic or hazardous items (e.g. batteries) into general bins.
- Diverts ambiguous, composite, or low-confidence items to manual inspection.
- Provides transparent municipal reasoning for every separate detection.
"""

import os
import logging
from typing import Dict, Any, Optional
from app.models.schemas import DisposalDecision

logger = logging.getLogger("ecosort.routing")

# Default minimum confidence threshold for automated disposal stream assignment
DEFAULT_DETECTION_CONFIDENCE_THRESHOLD = float(os.getenv("DETECTION_CONFIDENCE_THRESHOLD", "0.25"))

# Municipal Waste Routing Knowledge Base
DISPOSAL_RULES: Dict[str, Dict[str, Any]] = {
    # --------------------------------------------------------------------------
    # 1. Wet / Biodegradable Waste Stream
    # --------------------------------------------------------------------------
    "vegetable_scraps": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Vegetable trimmings and scraps are organic biomass suitable for aerobic composting or biogas digestion.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "vegetable_waste": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Vegetable waste is rapidly biodegradable organic material; keep segregated from dry recyclables.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "fruit_peels": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Citrus and fruit peels decompose readily in organic composting streams.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "fruit_waste": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Discarded fruit matter contributes high moisture and nutrients to municipal compost piles.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "food_waste": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "General food scraps and kitchen discards are collected in the green organic wet waste bin.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "food_scraps": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Food scraps decompose naturally and must be kept out of dry paper and plastic bins.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "biological": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Biological organic waste is routed to composting chutes to prevent dry stream contamination.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "organic_waste": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Pure organic material suitable for municipal anaerobic digestion facilities.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "apple": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Discarded apple core or fruit scrap; biodegradable wet organic matter.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "banana": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Banana peels decompose quickly into nutrient-rich compost.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "orange": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Citrus fruit discards suitable for general organic wet waste treatment.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "broccoli": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Vegetable scrap suitable for organic composting.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "carrot": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Vegetable scrap suitable for organic composting.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "sandwich": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Discarded food item; place in wet organic bin without wrapper.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "pizza": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Cooked food residue and crust are biodegradable wet organic waste.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "donut": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Bakery food waste decomposes readily in composting facilities.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "cake": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Organic bakery discard; dispose in green wet waste bin.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "hot_dog": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Prepared food scrap suitable for organic waste treatment.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },
    "potted_plant": {
        "category": "wet",
        "bin_label": "Wet / Biodegradable Waste",
        "reason": "Plant biomass and soil organic matter; decompose via municipal composting after removing plastic pot.",
        "compartment_id": "bin_organic",
        "color": "#10b981"
    },

    # --------------------------------------------------------------------------
    # 2. Dry / Recyclable Waste Stream (Polymers, Metals, Paper, Glass, Composites)
    # --------------------------------------------------------------------------
    "cardboard": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Cardboard is recyclable dry fiberboard; flatten boxes to optimize transport volume.",
        "compartment_id": "bin_cardboard",
        "color": "#d97706",
        "preparation": "Flatten corrugated cardboard; remove tape and keep dry.",
        "warning": None
    },
    "cardboard_box": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Corrugated cardboard boxes are infinitely repulpable when clean and dry.",
        "compartment_id": "bin_cardboard",
        "color": "#d97706",
        "preparation": "Flatten box completely and store in dry recycling chute.",
        "warning": None
    },
    "paper": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Clean cellulose paper is repulped for high-grade recycled paper manufacturing.",
        "compartment_id": "bin_paper",
        "color": "#3b82f6",
        "preparation": "Keep dry and separate from liquid-contaminated items.",
        "warning": None
    },
    "newspaper": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Newsprint paper is easily de-inked and repulped in paper mills.",
        "compartment_id": "bin_paper",
        "color": "#3b82f6",
        "preparation": "Bundle dry newspapers together for paper repulping.",
        "warning": None
    },
    "plastic": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Rigid recyclable plastics are shredded and pelletized into secondary resin.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Rinse clean and place in dry plastic recycling compartment.",
        "warning": None
    },
    "plastic_bottle": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "PET/HDPE beverage bottles are highly recyclable; empty liquids before recycling.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Empty all liquids, rinse lightly, and crush to conserve volume.",
        "warning": None
    },
    "bottle": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Clean container bottle (plastic or glass); rinse and place in recyclable bin.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Empty and rinse before depositing in dry collection bin.",
        "warning": None
    },
    "metal": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Metals (aluminum and tinplate) are 100% recyclable without loss of metallurgical properties.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Clean metal scrap and place in dry metal recycling bin.",
        "warning": None
    },
    "metal_can": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Aluminum and steel cans are separated via eddy-current magnets for scrap smelting.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Rinse empty can and deposit in dry metal bin.",
        "warning": None
    },
    "can": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Metal beverage or food container; recyclable dry scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Rinse cleanly and place in metal recycling compartment.",
        "warning": None
    },
    "glass_bottle": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Glass containers are melted in cullet furnaces to produce new bottles indefinitely.",
        "compartment_id": "bin_glass_brown",
        "color": "#0284c7",
        "preparation": "Rinse clean; remove non-glass caps.",
        "warning": None
    },
    "brown-glass": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Amber glass cullet preserves light-sensitive pharmaceuticals and beverage packaging.",
        "compartment_id": "bin_glass_brown",
        "color": "#92400e",
        "preparation": "Rinse cleanly and sort into brown glass cullet bin.",
        "warning": None
    },
    "green-glass": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Green container glass cullet routed to color-separated bottle cullet remelting.",
        "compartment_id": "bin_glass_green",
        "color": "#047857",
        "preparation": "Rinse cleanly and sort into green glass cullet bin.",
        "warning": None
    },
    "white-glass": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Clear flint glass cullet melted for high-clarity transparent container manufacturing.",
        "compartment_id": "bin_glass_white",
        "color": "#0284c7",
        "preparation": "Rinse cleanly and place into clear glass cullet bin.",
        "warning": None
    },
    "cup": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Clean plastic, paper, or aluminum beverage cup; recyclable dry container.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Empty liquids and deposit in dry recyclable bin.",
        "warning": None
    },
    "clothes": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Textiles and wearable garments routed for donation or fiber mechanical shredding.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Keep dry and deposit in textile reclamation bin.",
        "warning": None
    },
    "shoes": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Footwear and rubber soles routed to specialized reclamation depot.",
        "compartment_id": "bin_footwear",
        "color": "#7c3aed",
        "preparation": "Tie pairs together and place in dry footwear reclamation.",
        "warning": None
    },
    "wine_glass": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Clear stemware and container glass; recyclable dry cullet.",
        "compartment_id": "bin_glass_white",
        "color": "#0284c7",
        "preparation": "Place carefully in glass recycling chute.",
        "warning": None
    },
    "book": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Paper book or notebook; recyclable dry cellulose stream.",
        "compartment_id": "bin_paper",
        "color": "#3b82f6",
        "preparation": "Keep dry; place in dry paper stream.",
        "warning": None
    },
    "fork": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Metal or rigid plastic utensil; recyclable scrap stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Rinse food residues before recycling.",
        "warning": None
    },
    "knife": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Metal cutlery; route to dry metal reclamation.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Wrap cutting edge safely; place in dry metal recycling.",
        "warning": None
    },
    "spoon": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Metal or plastic cutlery discard; place in dry recycling.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Rinse clean and place in recyclable scrap compartment.",
        "warning": None
    },
    "bowl": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Dry tableware container (plastic or metal); recyclable stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Rinse residue and place in dry plastic/metal bin.",
        "warning": None
    },
    "scissors": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Metal scrap tool; suitable for magnetic separation recycling.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Place in dry metal recycling bin.",
        "warning": None
    },
    "toothbrush": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Polymer personal care handle; dry plastics reclamation.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Dispose in dry plastics recycling chute.",
        "warning": None
    },
    "plate": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Tableware plate (paper, plastic, or ceramic); ensure food scraps are scraped before dry recycling.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Scrape food scraps into organic bin; place dry plate in recycling.",
        "warning": None
    },
    "vase": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Glass or ceramic decorative vessel; route to glass or inert dry recycling depot.",
        "compartment_id": "bin_glass_white",
        "color": "#0284c7",
        "preparation": "Place in glass recycling chute.",
        "warning": None
    },

    # --- Comprehensive COCO / Mixed Waste Item Mappings ---
    "umbrella": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Composed of synthetic polymer/nylon fabric canopy and steel/aluminum wire ribs. Recyclable metal scrap and dry polymer stream.",
        "compartment_id": "bin_metal",
        "color": "#2563eb",
        "preparation": "Separate metal frame from synthetic canopy if feasible; route to dry recycling.",
        "warning": None
    },
    "kite": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Composed of lightweight flexible polyethylene polymer film, ripstop nylon, or paper sheeting. Recyclable dry plastics stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Detach strings or plastic fasteners; place flexible polymer film in dry plastic recycling.",
        "warning": None
    },
    "backpack": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Nylon, polyester, or canvas fabric bag; recyclable dry textile/polymer stream.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Empty all compartments and pockets; place in textile/dry reclamation.",
        "warning": None
    },
    "handbag": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Synthetic polymer, leather, or fabric handbag; recyclable dry goods stream.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Empty completely and place in dry goods collection chute.",
        "warning": None
    },
    "tie": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Silk, polyester, or cotton textile fabric; clean dry clothing recycling stream.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Deposit into textile recycling collection bin.",
        "warning": None
    },
    "suitcase": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Rigid thermoplastic (polycarbonate/ABS) or canvas luggage shell; recyclable dry bulky stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Ensure interior is empty; route to dry plastics or bulky salvage depot.",
        "warning": None
    },
    "frisbee": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "High-density polyethylene/polypropylene rigid disc; 100% recyclable dry plastic.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Deposit in dry plastics recycling bin.",
        "warning": None
    },
    "skis": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Composite wood, fiberglass, and steel edge sports equipment; recyclable dry scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to municipal dry bulky scrap depot.",
        "warning": None
    },
    "snowboard": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Composite polymer, wood, and metal board; recyclable dry scrap stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Deposit in dry bulky goods recycling chute.",
        "warning": None
    },
    "sports_ball": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Synthetic rubber and composite polyurethane sports ball; recyclable dry scrap stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Place in dry composite/rubber recycling collection.",
        "warning": None
    },
    "sports ball": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Synthetic rubber and composite polyurethane sports ball; recyclable dry scrap stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Place in dry composite/rubber recycling collection.",
        "warning": None
    },
    "baseball_bat": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Aluminum alloy or solid wood sporting bat; 100% recyclable metal or timber scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Place in dry metal/timber recycling bin.",
        "warning": None
    },
    "baseball bat": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Aluminum alloy or solid wood sporting bat; 100% recyclable metal or timber scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Place in dry metal/timber recycling bin.",
        "warning": None
    },
    "baseball_glove": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Leather and synthetic composite sports glove; dry textile/leather stream.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Deposit in dry textile and leather collection bin.",
        "warning": None
    },
    "baseball glove": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Leather and synthetic composite sports glove; dry textile/leather stream.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Deposit in dry textile and leather collection bin.",
        "warning": None
    },
    "skateboard": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Maple deck, polyurethane wheels, and aluminum trucks; recyclable dry composite/metal scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Place in dry metal/composite recycling chute.",
        "warning": None
    },
    "surfboard": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Polyurethane/EPS foam core with fiberglass shell; dry salvage stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Deliver to municipal dry bulky goods recycling depot.",
        "warning": None
    },
    "tennis_racket": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Graphite composite or aluminum frame with nylon strings; recyclable dry metal/polymer stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deposit in dry metal scrap recycling compartment.",
        "warning": None
    },
    "tennis racket": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Graphite composite or aluminum frame with nylon strings; recyclable dry metal/polymer stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deposit in dry metal scrap recycling compartment.",
        "warning": None
    },
    "chair": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Wood, molded plastic, or metal seating furniture; recyclable dry bulky stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Separate metal screws if possible; route to bulky dry waste collection.",
        "warning": None
    },
    "couch": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Upholstered furniture with timber frame, steel springs, and synthetic fabric; recyclable bulky salvage.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Deliver to municipal bulky dry waste recovery center.",
        "warning": None
    },
    "bed": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Metal or timber bed frame; recyclable scrap metal and timber stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Disassemble frame components for dry scrap recovery.",
        "warning": None
    },
    "dining_table": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Solid timber or metal dining furniture; dry bulky goods stream.",
        "compartment_id": "bin_cardboard",
        "color": "#64748b",
        "preparation": "Disassemble legs to optimize salvage transport.",
        "warning": None
    },
    "dining table": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Solid timber or metal dining furniture; dry bulky goods stream.",
        "compartment_id": "bin_cardboard",
        "color": "#64748b",
        "preparation": "Disassemble legs to optimize salvage transport.",
        "warning": None
    },
    "bench": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Cast iron, steel, or timber bench; 100% recyclable dry metal and wood scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Route to municipal dry metal reclamation depot.",
        "warning": None
    },
    "toilet": {
        "category": "dry",
        "bin_label": "Dry / Inert Recyclable",
        "reason": "Porcelain or vitreous china sanitary ceramic; recyclable inert mineral aggregate.",
        "compartment_id": "bin_glass_white",
        "color": "#64748b",
        "preparation": "Drain all water completely; deposit at inert masonry recycling depot.",
        "warning": None
    },
    "sink": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Stainless steel or porcelain ceramic basin; 100% recyclable metal/inert stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Disconnect fittings; place in dry metal or ceramic reclamation.",
        "warning": None
    },
    "teddy_bear": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Plush stuffed fabric toy; dry textile fiber reclamation stream.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Ensure no electronic battery modules remain inside; deposit in textile bin.",
        "warning": None
    },
    "teddy bear": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Plush stuffed fabric toy; dry textile fiber reclamation stream.",
        "compartment_id": "bin_textile",
        "color": "#8b5cf6",
        "preparation": "Ensure no electronic battery modules remain inside; deposit in textile bin.",
        "warning": None
    },
    "bicycle": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Bicycle frame and components; 100% recyclable steel/aluminum alloy scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Place in scrap metal collection bin.",
        "warning": None
    },
    "car": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Automotive body metal and scrap; route to vehicle scrap salvage.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to certified automotive scrap salvage facility.",
        "warning": None
    },
    "motorcycle": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Motorcycle alloy chassis and components; recyclable scrap metal.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to vehicle salvage yard.",
        "warning": None
    },
    "airplane": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Aerospace duralumin/composite alloy scrap; specialized aviation salvage.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to industrial scrap metal facility.",
        "warning": None
    },
    "bus": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Commercial vehicle metal chassis scrap; heavy vehicle salvage stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to commercial salvage depot.",
        "warning": None
    },
    "train": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Rail transport steel alloy; industrial metal scrap stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to industrial rail salvage.",
        "warning": None
    },
    "truck": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Heavy transport steel/aluminum chassis; recyclable scrap metal.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to heavy vehicle salvage yard.",
        "warning": None
    },
    "boat": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Marine hull alloy or fiberglass; recyclable marine salvage stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to marine scrap facility.",
        "warning": None
    },
    "traffic_light": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Aluminum and steel municipal fixture; recyclable metal scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to municipal public works depot.",
        "warning": None
    },
    "traffic light": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Aluminum and steel municipal fixture; recyclable metal scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to municipal public works depot.",
        "warning": None
    },
    "fire_hydrant": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Heavy cast iron municipal fixture; 100% recyclable ferrous metal scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to municipal scrap depot.",
        "warning": None
    },
    "fire hydrant": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Heavy cast iron municipal fixture; 100% recyclable ferrous metal scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to municipal scrap depot.",
        "warning": None
    },
    "stop_sign": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Heavy gauge aluminum sign plate; 100% recyclable aluminum scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Place in municipal dry metal scrap stream.",
        "warning": None
    },
    "stop sign": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Heavy gauge aluminum sign plate; 100% recyclable aluminum scrap.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Place in municipal dry metal scrap stream.",
        "warning": None
    },
    "parking_meter": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Cast iron and steel meter housing; recyclable scrap metal.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to municipal works depot.",
        "warning": None
    },
    "parking meter": {
        "category": "dry",
        "bin_label": "Dry / Metal Scrap",
        "reason": "Cast iron and steel meter housing; recyclable scrap metal.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Deliver to municipal works depot.",
        "warning": None
    },
    "plastic_bag": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Clean polyethylene film and packaging bags; dry soft plastic recycling stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Ensure dry and empty; place in film/bag collection receptacle.",
        "warning": None
    },
    "plastic_wrapper": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Dry polymer wrapper film; recyclable dry packaging stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Shake out crumbs; deposit in dry plastics collection chute.",
        "warning": None
    },
    "wrapper": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Polymer or foil food wrapper; recyclable dry packaging stream.",
        "compartment_id": "bin_plastic",
        "color": "#2563eb",
        "preparation": "Deposit in dry waste collection bin.",
        "warning": None
    },
    "foil": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Clean aluminum foil; 100% recyclable dry aluminum stream.",
        "compartment_id": "bin_metal",
        "color": "#64748b",
        "preparation": "Scrunch clean foil into a ball for magnetic sorting.",
        "warning": None
    },
    "carton": {
        "category": "dry",
        "bin_label": "Dry / Recyclable Waste",
        "reason": "Aseptic beverage carton (Tetra Pak); recyclable composite paperboard.",
        "compartment_id": "bin_cardboard",
        "color": "#d97706",
        "preparation": "Rinse and flatten before placing in carton recycling.",
        "warning": None
    },

    # --------------------------------------------------------------------------
    # 3. Hazardous / E-Waste Stream
    # --------------------------------------------------------------------------
    "battery": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Contains toxic heavy metals (lead, lithium, cadmium); NEVER place in wet or dry bins. Requires dedicated e-waste depot.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Tape terminal poles and deliver to designated battery collection receptacle.",
        "warning": "⚠️ Fire Hazard: Lithium and heavy metal chemistries must never be compacted."
    },
    "cell_phone": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Contains lithium battery and electronic circuit boards; deliver to municipal e-waste recycling.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Remove SIM and deliver intact to certified e-waste drop-off.",
        "warning": None
    },
    "laptop": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Computing hardware with battery and soldered boards; municipal e-waste recycling required.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Deliver intact to e-waste recycling collection.",
        "warning": None
    },
    "mouse": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Electronic peripheral with internal circuitry; route to e-waste depot.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Place in small electronic hardware bin.",
        "warning": None
    },
    "keyboard": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Electronic input hardware with PCB components; e-waste stream.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Place in e-waste drop-off depot.",
        "warning": None
    },
    "remote": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Electronic controller containing circuit board and battery compartment; e-waste drop-off.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Remove disposable alkaline batteries; route controller to e-waste.",
        "warning": None
    },
    "microwave": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "High-voltage home appliance; requires municipal hazardous e-waste collection.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Deliver intact to municipal appliance depot.",
        "warning": None
    },
    "toaster": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Small electric appliance; deliver to e-waste processing depot.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Deliver to small electrical appliance recovery center.",
        "warning": None
    },
    "tv": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Television display containing electronic circuitry, capacitors, and display panels; certified e-waste recovery required.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Deliver intact to e-waste depot; do not puncture screen.",
        "warning": None
    },
    "oven": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "High-voltage electrical kitchen appliance; deliver to municipal e-waste recovery.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Deliver to appliance salvage center.",
        "warning": None
    },
    "refrigerator": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Major refrigeration appliance containing compressor and refrigerant fluids; certified e-waste recovery required.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Do not vent coolant circuits; deliver to specialized depot.",
        "warning": None
    },
    "clock": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Battery-operated electronic device; isolate battery and route to e-waste.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Remove battery for dedicated disposal; route clock to e-waste.",
        "warning": None
    },
    "e-waste": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Electronic hardware contains regulated heavy metals and circuit elements requiring specialized depot processing.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Deliver to certified e-waste depot.",
        "warning": None
    },
    "chemical_container": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Toxic or chemical residues must not enter standard residential waste streams.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Seal tightly; deliver to household hazardous waste facility.",
        "warning": "⚠️ Chemical Hazard: Deliver sealed container to specialized municipal chemical collection."
    },
    "hair_drier": {
        "category": "hazardous",
        "bin_label": "Hazardous / E-Waste Collection",
        "reason": "Small motorized electrical appliance with heating elements and cord; requires specialized e-waste processing.",
        "compartment_id": "bin_hazardous",
        "color": "#ef4444",
        "preparation": "Wrap electrical cord; place in e-waste bin.",
        "warning": None
    },

    # --------------------------------------------------------------------------
    # 4. Living Entities / Non-Waste Subjects
    # --------------------------------------------------------------------------
    "person": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Person or operator detected in visual frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Exclude non-waste subjects from sorting receptacle.",
        "warning": None
    },
    "bird": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Wildlife or biological entity detected; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection; ensure sorting tray is clear.",
        "warning": None
    },
    "cat": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Domestic animal detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "dog": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Domestic animal detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "horse": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Domestic animal detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "sheep": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Animal detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "cow": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Animal detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "elephant": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Wildlife detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "bear": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Wildlife detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "zebra": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Wildlife detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },
    "giraffe": {
        "category": "manual_review",
        "bin_label": "Non-Waste Subject",
        "reason": "Wildlife detected in frame; non-waste subject.",
        "compartment_id": "bin_manual_review",
        "color": "#6b7280",
        "preparation": "Non-waste detection.",
        "warning": None
    },

    # --------------------------------------------------------------------------
    # 5. Composite Materials / Manual Review Streams
    # --------------------------------------------------------------------------
    "plastic_packaging": {
        "category": "manual_review",
        "bin_label": "Manual Review / Residual Waste",
        "reason": "Flexible plastic packaging or film may be contaminated or non-recyclable multi-layer composite. Requires visual review or residual disposal.",
        "compartment_id": "bin_residual",
        "color": "#d97706",
        "preparation": "Inspect for multi-layer foil laminates before recycling.",
        "warning": None
    },
    "plastic_film": {
        "category": "manual_review",
        "bin_label": "Manual Review / Residual Waste",
        "reason": "Thin plastic films frequently tangle mechanical recycling sorting trommels. Diverted for manual check.",
        "compartment_id": "bin_residual",
        "color": "#d97706",
        "preparation": "Consolidate clean polyethylene film or route to specialized film drop-off.",
        "warning": None
    },
    "trash": {
        "category": "manual_review",
        "bin_label": "Manual Review / General Residual",
        "reason": "Mixed municipal solid waste; review for possible recoverable fractions before landfill or energy recovery.",
        "compartment_id": "bin_residual",
        "color": "#4b5563",
        "preparation": "Segregate recoverable paper and plastics from non-recyclable residual.",
        "warning": None
    },
    "contaminated_packaging": {
        "category": "manual_review",
        "bin_label": "Manual Review / Residual Waste",
        "reason": "Grease or food contamination degrades pulp/resin quality; diverted to prevent bulk contamination.",
        "compartment_id": "bin_manual_review",
        "color": "#dc2626",
        "preparation": "Rinse if possible; otherwise place in residual disposal.",
        "warning": None
    }
}


class WasteRoutingService:
    """
    Testable disposal routing engine for multi-object detections.
    """

    def __init__(self, confidence_threshold: float = DEFAULT_DETECTION_CONFIDENCE_THRESHOLD):
        self.confidence_threshold = confidence_threshold
        self.rules = dict(DISPOSAL_RULES)

    def register_override(self, label: str, rule: Dict[str, Any]):
        """Allows municipal operators to customize disposal policies."""
        normalized = self._normalize_label(label)
        self.rules[normalized] = rule
        logger.info(f"Registered municipal routing override for '{normalized}' -> {rule.get('category')}")

    @staticmethod
    def _normalize_label(label: str) -> str:
        """Normalizes label text (strips, lowercases, replaces spaces/hyphens with underscores)."""
        if not label:
            return "unknown"
        norm = label.strip().lower()
        # Keep exact hyphenated known classes if matched
        if norm in ("brown-glass", "green-glass", "white-glass", "e-waste"):
            return norm
        return norm.replace(" ", "_").replace("-", "_")

    def route_detected_item(
        self,
        label: str,
        confidence: float,
        min_confidence: Optional[float] = None
    ) -> DisposalDecision:
        """
        Determines the authoritative disposal stream for a detected object.
        Enforces safety guardrails:
        1. Low confidence -> Manual review (quarantine).
        2. Unknown class -> Manual review (unrecognized material).
        3. Hazardous items -> High-priority hazardous isolation.
        """
        threshold = min_confidence if min_confidence is not None else self.confidence_threshold
        normalized_label = self._normalize_label(label)

        # Confidence safeguard: Ambiguous or weak detections are quarantined
        if confidence < threshold:
            return DisposalDecision(
                category="manual_review",
                bin_label="Manual Review / Uncertain",
                reason=(
                    f"Detection confidence ({confidence:.1%}) is below the automated sorting threshold ({threshold:.1%}). "
                    "Quarantined for operator inspection to prevent stream contamination."
                ),
                compartment_id="bin_manual_review",
                color="#dc2626",
                preparation="Divert item to quarantine tray for visual inspection by operator.",
                warning=None
            )

        # 1. Direct rule lookup
        rule = self.rules.get(normalized_label)

        # 2. Key normalization fallback (e.g. spaces vs underscores)
        if not rule:
            alt_label = normalized_label.replace("_", " ")
            rule = self.rules.get(alt_label)

        # 3. Substring matching for waste category keywords
        if not rule:
            for key, val in self.rules.items():
                if len(key) > 3 and (key in normalized_label or normalized_label in key):
                    rule = val
                    break

        if not rule:
            # Fallback for unrecognized classes: Divert cleanly to manual review without alarming errors
            return DisposalDecision(
                category="manual_review",
                bin_label="Manual Review / Unrecognized",
                reason=(
                    f"Detected item '{label}' is not mapped to an automated municipal sorting stream. "
                    "Diverted to manual inspection."
                ),
                compartment_id="bin_manual_review",
                color="#64748b",
                preparation="Set aside in sorting tray. Verify local acceptance criteria.",
                warning=None
            )

        category = rule["category"]
        default_prep = (
            "Separate from plastic bags and non-biodegradable packaging before composting."
            if category == "wet" else
            "Ensure item is clean, empty, and dry. Rinse food residue and flatten containers."
            if category == "dry" else
            "Do not mix with municipal solid waste. Deliver intact to municipal collection."
            if category == "hazardous" else
            "Set aside for manual operator inspection."
        )
        default_warning = (
            None
            if category in ("wet", "dry") else
            "Safety Directive: E-waste contains regulated electronics; deliver to municipal e-waste depot."
            if category == "hazardous" else
            None
        )

        return DisposalDecision(
            category=category,
            bin_label=rule["bin_label"],
            reason=rule["reason"],
            compartment_id=rule.get("compartment_id"),
            color=rule.get("color"),
            preparation=rule.get("preparation", default_prep),
            warning=rule.get("warning", default_warning)
        )


# Global default routing service singleton
waste_routing_service = WasteRoutingService()
