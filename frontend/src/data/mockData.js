/**
 * Mock Data for EcoSort AI — Frontend Development
 * ================================================
 * This file contains all demo/mock data used during frontend-only development.
 * ALL data here is clearly marked as DEMO and will be replaced with real API/Firebase data.
 * 
 * DO NOT present this data as actual experimental results.
 */

// Demo users
export const DEMO_USER = {
  uid: 'demo-user-001',
  name: 'Demo Student / Researcher',
  email: 'demo@ecosortai.com',
  role: 'user',
  createdAt: '2026-01-15T10:30:00Z',
  photoURL: null
};

export const DEMO_ADMIN = {
  uid: 'demo-admin-001',
  name: 'Admin Supervisor',
  email: 'admin@ecosortai.com',
  role: 'admin',
  createdAt: '2025-12-01T08:00:00Z',
  photoURL: null
};

// 12 waste classes from the trained MobileNetV2 model
export const WASTE_CLASSES = [
  'battery', 'biological', 'brown-glass', 'cardboard', 'clothes',
  'green-glass', 'metal', 'paper', 'plastic', 'shoes', 'trash', 'white-glass'
];

export const COMPARTMENTS = {
  'bin_hazardous': {
    id: 'bin_hazardous',
    name: 'Hazardous Waste Depot (E-Waste)',
    stream: 'Hazardous / Chemical',
    color: '#ef4444',
    icon: '⚡'
  },
  'bin_organic': {
    id: 'bin_organic',
    name: 'Organic Wet Waste Bin (Compost)',
    stream: 'Organic / Wet Waste',
    color: '#10b981',
    icon: '🌿'
  },
  'bin_glass_brown': {
    id: 'bin_glass_brown',
    name: 'Amber Glass Stream Bin',
    stream: 'Recyclable / Glass',
    color: '#92400e',
    icon: '🍾'
  },
  'bin_glass_green': {
    id: 'bin_glass_green',
    name: 'Green Glass Stream Bin',
    stream: 'Recyclable / Glass',
    color: '#047857',
    icon: '🍾'
  },
  'bin_glass_white': {
    id: 'bin_glass_white',
    name: 'Clear Flint Glass Stream Bin',
    stream: 'Recyclable / Glass',
    color: '#0284c7',
    icon: '🥛'
  },
  'bin_cardboard': {
    id: 'bin_cardboard',
    name: 'Cardboard Recycling Bin',
    stream: 'Recyclable / Dry Waste',
    color: '#d97706',
    icon: '📦'
  },
  'bin_paper': {
    id: 'bin_paper',
    name: 'Dry Paper Stream Bin',
    stream: 'Recyclable / Dry Waste',
    color: '#3b82f6',
    icon: '📄'
  },
  'bin_plastic': {
    id: 'bin_plastic',
    name: 'Blue Plastic Recycling Bin',
    stream: 'Recyclable / Dry Waste',
    color: '#2563eb',
    icon: '🧴'
  },
  'bin_metal': {
    id: 'bin_metal',
    name: 'Metal & Can Stream Bin',
    stream: 'Recyclable / Dry Waste',
    color: '#64748b',
    icon: '🥫'
  },
  'bin_textile': {
    id: 'bin_textile',
    name: 'Textile Collection Bin',
    stream: 'Recyclable / Dry Waste',
    color: '#8b5cf6',
    icon: '👕'
  },
  'bin_footwear': {
    id: 'bin_footwear',
    name: 'Footwear & Rubber Reclamation Depot',
    stream: 'Recyclable / Dry Waste',
    color: '#7c3aed',
    icon: '👟'
  },
  'bin_residual': {
    id: 'bin_residual',
    name: 'General Residual Waste Bin',
    stream: 'Non-Recyclable',
    color: '#4b5563',
    icon: '🗑️'
  },
  'bin_manual_review': {
    id: 'bin_manual_review',
    name: 'Manual Review / Quarantine Bin',
    stream: 'Uncertain / Manual Review',
    color: '#dc2626',
    icon: '⚠️'
  }
};

export const CLASS_METADATA = {
  'battery': {
    category: 'Hazardous / Other',
    disposalBin: 'E-Waste / Battery Drop-off Depot',
    destinationCompartment: 'Hazardous Waste Depot (E-Waste)',
    compartmentId: 'bin_hazardous',
    recommendation: 'Do NOT place in general waste. Drop off at designated chemical/e-waste collection depots.',
    routingReason: 'High-priority hazardous isolation: toxic chemistries and fire risk require dedicated e-waste depot handling.',
    color: '#ef4444'
  },
  'biological': {
    category: 'Organic / Wet Waste',
    disposalBin: 'Green Organic Compost Bin',
    destinationCompartment: 'Organic Wet Waste Bin (Compost)',
    compartmentId: 'bin_organic',
    recommendation: 'Suitable for municipal composting and anaerobic digestion. Keep free of plastics.',
    routingReason: 'Biodegradable wet biomass: routed to composting chute to prevent contaminating dry recyclable streams.',
    color: '#10b981'
  },
  'brown-glass': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Amber Glass Stream Bin',
    destinationCompartment: 'Amber Glass Stream Bin',
    compartmentId: 'bin_glass_brown',
    recommendation: 'Rinse container thoroughly. Remove metallic or plastic caps and place in amber glass stream.',
    routingReason: 'Color-separated glass: brown/amber glass cullet preserved for light-sensitive pharmaceutical and beverage bottle remelting.',
    color: '#92400e'
  },
  'green-glass': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Green Glass Stream Bin',
    destinationCompartment: 'Green Glass Stream Bin',
    compartmentId: 'bin_glass_green',
    recommendation: 'Rinse thoroughly before disposal. Infinite recycling potential without degradation.',
    routingReason: 'Color-separated glass: green container glass routed to dedicated cullet furnace.',
    color: '#047857'
  },
  'white-glass': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Flint / Clear Glass Stream Bin',
    destinationCompartment: 'Clear Flint Glass Stream Bin',
    compartmentId: 'bin_glass_white',
    recommendation: 'Clear flint glass. Keep intact and uncrushed where possible for safe optical sorting.',
    routingReason: 'High-purity clear flint glass: routed to optical sortation to produce high-value transparent glass cullet.',
    color: '#0284c7'
  },
  'cardboard': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Dry Paper & Cardboard Bin',
    destinationCompartment: 'Cardboard Recycling Bin',
    compartmentId: 'bin_cardboard',
    recommendation: 'Flatten box to conserve bin volume. Ensure free from oil, grease, and food contamination.',
    routingReason: 'Dry fiberboard stream: corrugated packaging compressed for paper pulp mill reprocessing.',
    color: '#d97706'
  },
  'paper': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Dry Paper Stream Bin',
    destinationCompartment: 'Dry Paper Stream Bin',
    compartmentId: 'bin_paper',
    recommendation: 'Place clean and dry paper into recycling stream. Avoid shredding unless required for confidentiality.',
    routingReason: 'Dry cellulose stream: clean graphic and print paper routed to de-inking and pulp fiber recycling.',
    color: '#3b82f6'
  },
  'plastic': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Blue Plastic Recycling Bin',
    destinationCompartment: 'Blue Plastic Recycling Bin',
    compartmentId: 'bin_plastic',
    recommendation: 'Rinse liquid residue. Check resin code (PET, HDPE, PP). Place in dry recycling bin.',
    routingReason: 'Rigid polymer stream: bottles and containers routed to mechanical washing, flaking, and pelletizing.',
    color: '#2563eb'
  },
  'metal': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Metal & Can Stream Bin',
    destinationCompartment: 'Metal & Can Stream Bin',
    compartmentId: 'bin_metal',
    recommendation: 'Rinse food cans and beverage aluminum tins. 100% recyclable with minimal remelt energy.',
    routingReason: 'Ferrous and non-ferrous metals: routed to magnetic/eddy-current separation for high-efficiency remelting.',
    color: '#64748b'
  },
  'clothes': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Textile Collection Bin',
    destinationCompartment: 'Textile Collection Bin',
    compartmentId: 'bin_textile',
    recommendation: 'Donate wearable apparel to community shelters. Dispose frayed textiles into textile reclamation.',
    routingReason: 'Textile recovery: wearable garments sorted for donation triage; worn fabrics shredded for acoustic insulation.',
    color: '#8b5cf6'
  },
  'shoes': {
    category: 'Recyclable / Dry Waste',
    disposalBin: 'Footwear & Rubber Reclamation Depot',
    destinationCompartment: 'Footwear & Rubber Reclamation Depot',
    compartmentId: 'bin_footwear',
    recommendation: 'Tether pairs together. Donate usable footwear or deposit in specialized rubber/leather reclamation.',
    routingReason: 'Composite footwear stream: routed for rubber outsole stripping and athletic surface material recycling.',
    color: '#7c3aed'
  },
  'trash': {
    category: 'Non-Recyclable',
    disposalBin: 'General Residual Waste Bin',
    destinationCompartment: 'General Residual Waste Bin',
    compartmentId: 'bin_residual',
    recommendation: 'Residual non-recyclable solid waste. Route for energy recovery or municipal sanitary containment.',
    routingReason: 'Inert and composite residual waste: routed to general landfill or thermal waste-to-energy recovery.',
    color: '#4b5563'
  }
};

export const WASTE_CATEGORY_MAP = CLASS_METADATA;

// Dashboard metrics
export const MOCK_DASHBOARD_STATS = {
  totalClassifications: 2264,
  recyclableWaste: 1420,
  organicWaste: 610,
  otherWaste: 234,
  todayActivity: 42,
  averageConfidence: 94.8,
  sanitationStatus: 'GOOD',
  activeAnomalies: 2
};

export const DEMO_DASHBOARD_STATS = {
  ...MOCK_DASHBOARD_STATS,
  recyclableDry: MOCK_DASHBOARD_STATS.recyclableWaste,
  organicWet: MOCK_DASHBOARD_STATS.organicWaste,
  hazardous: 65,
  nonRecyclable: 169,
  anomaliesCount: MOCK_DASHBOARD_STATS.activeAnomalies
};

// Recent records
export const MOCK_RECENT_RECORDS = [
  {
    id: 'REC-9081',
    thumbnail: '🧴',
    itemName: 'Polyethylene Beverage Bottle',
    predictedClass: 'plastic',
    wasteType: 'Recyclable',
    confidence: 96.8,
    recommendation: 'Rinse container and deposit into Blue Plastic Bin.',
    timestamp: '2026-09-25T11:42:00Z'
  },
  {
    id: 'REC-9080',
    thumbnail: '📦',
    itemName: 'Corrugated Shipping Box',
    predictedClass: 'cardboard',
    wasteType: 'Recyclable',
    confidence: 97.4,
    recommendation: 'Flatten completely before insertion into Cardboard Bin.',
    timestamp: '2026-09-25T11:15:00Z'
  },
  {
    id: 'REC-9079',
    thumbnail: '🍎',
    itemName: 'Organic Apple Core & Fruit Rind',
    predictedClass: 'biological',
    wasteType: 'Organic',
    confidence: 93.2,
    recommendation: 'Place into Green Composting & Wet Waste container.',
    timestamp: '2026-09-25T10:50:00Z'
  },
  {
    id: 'REC-9078',
    thumbnail: '🥫',
    itemName: 'Aluminum Beverage Can',
    predictedClass: 'metal',
    wasteType: 'Recyclable',
    confidence: 98.1,
    recommendation: 'Crush can and dispose in Metal Recyclables Bin.',
    timestamp: '2026-09-25T10:12:00Z'
  },
  {
    id: 'REC-9077',
    thumbnail: '🔋',
    itemName: 'Alkaline AA Battery Cell',
    predictedClass: 'battery',
    wasteType: 'Hazardous',
    confidence: 95.6,
    recommendation: 'Do NOT throw into regular bin. Deposit in Battery Box.',
    timestamp: '2026-09-25T09:30:00Z'
  },
  {
    id: 'REC-9076',
    thumbnail: '📄',
    itemName: 'Printed Academic Assignment',
    predictedClass: 'paper',
    wasteType: 'Recyclable',
    confidence: 91.5,
    recommendation: 'Deposit into Dry Paper Recycling stream.',
    timestamp: '2026-09-25T09:05:00Z'
  },
  {
    id: 'REC-9075',
    thumbnail: '🍾',
    itemName: 'Amber Medicine Bottle',
    predictedClass: 'brown-glass',
    wasteType: 'Recyclable',
    confidence: 94.0,
    recommendation: 'Rinse residue and place into Glass Recycling stream.',
    timestamp: '2026-09-25T08:40:00Z'
  }
];

export const DEMO_HISTORY = MOCK_RECENT_RECORDS;

// Waste distribution
export const MOCK_WASTE_DISTRIBUTION = {
  labels: ['Recyclable (Dry)', 'Organic (Wet)', 'Glass Stream', 'Hazardous / Other', 'Non-Recyclable'],
  counts: [1120, 610, 290, 84, 160],
  colors: ['#2563eb', '#10b981', '#8b5cf6', '#f59e0b', '#6b7280']
};

export const DEMO_WASTE_DISTRIBUTION = {
  labels: MOCK_WASTE_DISTRIBUTION.labels,
  data: MOCK_WASTE_DISTRIBUTION.counts
};

// Activity trends
export const MOCK_ACTIVITY_TRENDS = {
  daily: [
    { date: '2026-09-19', total: 112, recyclable: 68, organic: 34, other: 10 },
    { date: '2026-09-20', total: 95, recyclable: 55, organic: 28, other: 12 },
    { date: '2026-09-21', total: 140, recyclable: 85, organic: 42, other: 13 },
    { date: '2026-09-22', total: 165, recyclable: 102, organic: 45, other: 18 },
    { date: '2026-09-23', total: 150, recyclable: 92, organic: 40, other: 18 },
    { date: '2026-09-24', total: 178, recyclable: 110, organic: 50, other: 18 },
    { date: '2026-09-25', total: 42, recyclable: 28, organic: 11, other: 3 }
  ]
};

// Sanitation intelligence
export const MOCK_SANITATION_INTEL = {
  currentStatus: 'GOOD',
  lastUpdated: '2026-09-25T11:45:00Z',
  reason: 'Waste segregation practices are within nominal statistical bounds. Classification frequency is stable and stream ratios align with academic campus baselines.',
  supportingIndicators: [
    { indicator: 'Segregation Accuracy Ratio', value: '94.8%', threshold: '≥ 85.0%', status: 'NORMAL' },
    { indicator: 'Wet / Organic Stream Skew', value: '27.0%', threshold: '20% - 35%', status: 'NORMAL' },
    { indicator: 'Contamination Anomaly Rate', value: '2.1%', threshold: '≤ 5.0%', status: 'NORMAL' },
    { indicator: 'Event Velocity Variance', value: '+4.2%', threshold: '± 25.0%', status: 'NORMAL' }
  ],
  locationSignals: [
    { department: 'Cafeteria Wing A', dominantCategory: 'Organic / Wet', activityLevel: 'High', status: 'OPTIMAL' },
    { department: 'Computer Science Lab 3', dominantCategory: 'Dry / Recyclable', activityLevel: 'Medium', status: 'OPTIMAL' },
    { department: 'Central Library Foyer', dominantCategory: 'Paper / Dry', activityLevel: 'Medium', status: 'OPTIMAL' },
    { department: 'Engineering Workshop 2', dominantCategory: 'Metal / Battery', activityLevel: 'Low', status: 'MONITORED' }
  ],
  recommendations: [
    'Maintain standard bi-daily clearance schedule for organic streams in Cafeteria Wing A.',
    'Dry waste bins in Academic Library exhibit high purity (96%); route directly to paper recycling.',
    'Continue monitoring Workshop 2 for battery drop-off events.'
  ]
};

export const DEMO_SANITATION = {
  status: MOCK_SANITATION_INTEL.currentStatus,
  reason: MOCK_SANITATION_INTEL.reason,
  indicators: MOCK_SANITATION_INTEL.supportingIndicators.map((i) => ({
    label: i.indicator,
    value: i.value,
    status: i.status === 'NORMAL' ? 'good' : 'warning'
  })),
  recommendations: MOCK_SANITATION_INTEL.recommendations
};

// Statistical anomalies
export const MOCK_ANOMALIES = [
  {
    id: 'ANOM-104',
    type: 'Sudden Intake Frequency Spike',
    severity: 'High',
    category: 'Activity Velocity',
    location: 'Cafeteria Wing A',
    reason: 'Classification volume surged +185% over rolling 1-hour moving baseline.',
    recommendation: 'Verify if campus event or banquet concluded; schedule supplemental organic clearance.',
    timestamp: '2026-09-25T11:05:00Z'
  },
  {
    id: 'ANOM-103',
    type: 'Hazardous Stream Skew',
    severity: 'Medium',
    category: 'Stream Distribution',
    location: 'Engineering Workshop 2',
    reason: 'Battery classifications exceeded 3σ standard distribution cutoff.',
    recommendation: 'Check battery collection depot container capacity to prevent cross-contamination.',
    timestamp: '2026-09-24T16:20:00Z'
  }
];

export const DEMO_ANOMALIES = {
  status: 'Monitored',
  records: MOCK_ANOMALIES
};

// Admin metrics
export const MOCK_ADMIN_STATS = {
  totalUsers: 48,
  totalClassifications: 2264,
  anomaliesDetected: 2,
  sanitationStatus: 'GOOD',
  topStream: 'Recyclable (Dry)',
  averageAccuracy: 94.8
};

export const DEMO_ADMIN_STATS = MOCK_ADMIN_STATS;

// Users directory
export const MOCK_USERS_LIST = [
  {
    id: 'USR-001',
    name: 'Student Lead Researcher',
    email: 'student.lead@university.edu',
    role: 'admin',
    createdAt: '2026-01-10',
    classificationsCount: 420
  },
  {
    id: 'USR-002',
    name: 'Sanitation Officer Sharma',
    email: 'sharma.sanitation@campus.edu',
    role: 'user',
    createdAt: '2026-02-01',
    classificationsCount: 312
  },
  {
    id: 'USR-003',
    name: 'Lab Assistant Patel',
    email: 'patel.aiml@university.edu',
    role: 'user',
    createdAt: '2026-02-14',
    classificationsCount: 198
  },
  {
    id: 'USR-004',
    name: 'Prof. Project Guide',
    email: 'guide.cse@university.edu',
    role: 'admin',
    createdAt: '2026-01-05',
    classificationsCount: 65
  },
  {
    id: 'USR-005',
    name: 'Research Scholar Gupta',
    email: 'gupta.scholar@university.edu',
    role: 'user',
    createdAt: '2026-03-01',
    classificationsCount: 88
  }
];

export const DEMO_USERS_LIST = MOCK_USERS_LIST;
