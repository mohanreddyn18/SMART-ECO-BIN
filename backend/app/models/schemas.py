from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PredictionResponse(BaseModel):
    predictedClass: str
    confidence: float
    wasteType: str
    recommendation: str
    disposalBin: str
    timestamp: str
    model: str = "MobileNetV2 Transfer Learning (RJ147)"
    isDemo: bool = False
    # Authoritative Software Segregation Routing Policy Fields
    destinationCompartment: Optional[str] = None
    compartmentId: Optional[str] = None
    routingStatus: Optional[str] = "AUTOMATED_ROUTED"
    routingReason: Optional[str] = None
    requiresManualReview: bool = False
    simulationStatus: Optional[str] = "READY"

class HistoryRecord(BaseModel):
    id: str
    itemName: Optional[str] = "Standard Waste Sample"
    predictedClass: str
    confidence: float
    wasteType: str
    recommendation: str
    disposalBin: Optional[str] = None
    timestamp: str
    imageUrl: Optional[str] = None
    userId: Optional[str] = "public-citizen"
    destinationCompartment: Optional[str] = None
    compartmentId: Optional[str] = None
    routingStatus: Optional[str] = None
    routingReason: Optional[str] = None
    requiresManualReview: Optional[bool] = False
    simulationStatus: Optional[str] = None

class DisposalDecision(BaseModel):
    category: str = Field(..., description="Stream category: 'wet', 'dry', 'hazardous', or 'manual_review'")
    bin_label: str = Field(..., description="Human-readable bin designation")
    reason: str = Field(..., description="Authoritative municipal reasoning for disposal stream")
    compartment_id: Optional[str] = Field(None, description="Software-simulated compartment ID")
    color: Optional[str] = Field(None, description="Hex color code for visual badge indicators")
    preparation: Optional[str] = Field(None, description="Actionable preparation instruction (e.g. rinse, flatten, separate)")
    warning: Optional[str] = Field(None, description="Safety or contamination warning (e.g. fire risk, chemical caution)")

class WasteDistribution(BaseModel):
    labels: List[str]
    counts: List[int]
    colors: List[str]

class AnalyticsResponse(BaseModel):
    totalClassifications: int
    distribution: WasteDistribution
    weeklyTrends: Dict[str, Any]
    averageConfidence: float
    topCategory: Optional[str] = "None"
    dataSource: Optional[str] = "Software Classification Ledger (Dev Emulation)"
    hardwareSensors: Optional[bool] = False

    # Enhanced Analytics Fields for Dashboards, Graphs, and Multi-Object Aggregation
    categoryBreakdown: Optional[Dict[str, int]] = Field(default_factory=dict)
    volumeTrends: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    classBreakdown: Optional[Dict[str, int]] = Field(default_factory=dict)
    todayActivity: Optional[int] = 0
    storageProvider: Optional[str] = "Local Registry"
    sanitationStatus: Optional[str] = "GOOD"
    activeAnomalies: Optional[int] = 0

    # Time-Filter & Multi-Object Dimensions
    timePeriod: Optional[str] = "all"
    totalUploads: Optional[int] = 0
    totalObjectsDetected: Optional[int] = 0
    wetCount: Optional[int] = 0
    dryCount: Optional[int] = 0
    hazardousCount: Optional[int] = 0
    manualReviewCount: Optional[int] = 0
    comparison: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timeSeries: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class SupportingIndicator(BaseModel):
    indicator: str
    value: str
    threshold: str
    status: str

class LocationSignal(BaseModel):
    department: str
    dominantCategory: str
    activityLevel: str
    status: str

class SanitationResponse(BaseModel):
    currentStatus: str # GOOD, ATTENTION REQUIRED, CRITICAL, UNAVAILABLE
    reason: str
    lastUpdated: str
    hardwareSensors: bool = False
    telemetrySource: Optional[str] = "Software Event Stream (Zero IoT Sensors)"
    supportingIndicators: List[SupportingIndicator] = []
    locationSignals: List[LocationSignal] = []
    recommendations: List[str] = []

class AnomalyItem(BaseModel):
    id: str
    type: str
    severity: str # High, Medium, Low
    category: str
    location: str
    reason: str
    recommendation: str
    timestamp: str

class AnomalyResponse(BaseModel):
    status: str
    totalAnomalies: int
    algorithm: str
    anomalies: List[AnomalyItem]
    message: Optional[str] = None
    recordsSampled: Optional[int] = 0

class PredictiveInsightsResponse(BaseModel):
    sufficientData: bool
    currentSamples: int
    requiredSamples: int
    observationDays: int
    requiredDays: int
    message: str
    projections: Optional[Dict[str, Any]] = None
    currentEvents: Optional[int] = None
    requiredEvents: Optional[int] = None
    readinessPct: Optional[float] = None
    forecast: Optional[List[Dict[str, Any]]] = None
    generatedAt: Optional[str] = None
    scope: Optional[str] = None

class StorageStatusResponse(BaseModel):
    mode: str
    storage_backend: str
    storage_file: Optional[str] = None
    persistent_cloud_enabled: bool
    cloud_provider: str
    record_count: int
    idempotency_enabled: bool
    project_id: Optional[str] = None
    collection: Optional[str] = None
    notes: Optional[str] = None

class AIQueryRequest(BaseModel):
    prompt: str
    userId: Optional[str] = None

class WasteAIResponse(BaseModel):
    reply: str
    timestamp: str
    source: str = "Gemini / WasteAI"

class SanitationAIResponse(BaseModel):
    reply: str
    function_called: Optional[str] = None
    telemetry_grounded: bool = True
    timestamp: str


# ==============================================================================
# Multi-Object Mixed Waste Detection Schemas (Stage 12)
# ==============================================================================

class BoundingBox(BaseModel):
    x1: float = Field(..., description="Top-left X pixel coordinate in original image")
    y1: float = Field(..., description="Top-left Y pixel coordinate in original image")
    x2: float = Field(..., description="Bottom-right X pixel coordinate in original image")
    y2: float = Field(..., description="Bottom-right Y pixel coordinate in original image")
    norm_x1: Optional[float] = Field(None, description="Normalized top-left X [0.0, 1.0]")
    norm_y1: Optional[float] = Field(None, description="Normalized top-left Y [0.0, 1.0]")
    norm_x2: Optional[float] = Field(None, description="Normalized bottom-right X [0.0, 1.0]")
    norm_y2: Optional[float] = Field(None, description="Normalized bottom-right Y [0.0, 1.0]")


class ObjectDetectionItem(BaseModel):
    detection_id: int = Field(..., description="Sequential identifier for this detected item")
    label: str = Field(..., description="Identified waste object class")
    confidence: float = Field(..., description="Detection confidence score (0.0 to 1.0)")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates in image space")
    mask: Optional[List[List[float]]] = Field(None, description="Polygon segmentation mask if supported")
    disposal: DisposalDecision = Field(..., description="Disposal routing decision for this object")


class DetectionSummary(BaseModel):
    total_detections: int = 0
    wet_items: int = 0
    dry_items: int = 0
    hazardous_items: int = 0
    manual_review_items: int = 0


class WasteDetectionResponse(BaseModel):
    success: bool
    model_status: str = Field(..., description="Status: 'loaded', 'not_configured', 'inference_failed'")
    message: Optional[str] = None
    model_info: Optional[Dict[str, Any]] = None
    image_dimensions: Optional[Dict[str, int]] = None
    detections: List[ObjectDetectionItem] = Field(default_factory=list)
    summary: DetectionSummary = Field(default_factory=DetectionSummary)
    annotated_image_base64: Optional[str] = None
