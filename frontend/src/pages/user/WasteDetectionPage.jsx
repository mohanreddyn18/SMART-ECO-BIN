import React, { useState, useRef, useEffect } from 'react';
import {
  FiUploadCloud,
  FiCheckCircle,
  FiAlertCircle,
  FiRefreshCw,
  FiCamera,
  FiVideo,
  FiVideoOff,
  FiTag,
  FiCheckSquare,
  FiCompass,
  FiShield
} from 'react-icons/fi';
import { validateImageFile, getConfidenceBadgeClass, formatDateTime } from '../../utils/helpers';
import DigitalSegregationSimulation from '../../components/DigitalSegregationSimulation';
import { api } from '../../services/api';

export default function WasteDetectionPage() {
  const [inputMode, setInputMode] = useState('upload'); // 'upload' | 'camera'
  const [analysisMode, setAnalysisMode] = useState('single'); // 'single' (MobileNetV2) | 'multi' (Multi-Object)
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState(null);
  const [detectionResult, setDetectionResult] = useState(null);
  const [confThreshold, setConfThreshold] = useState(0.25);

  // Camera states and refs
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraLoading, setCameraLoading] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);

  // Clean up camera stream on unmount or mode switch
  const stopCameraStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore cleanup errors
        }
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
    setCameraLoading(false);
  };

  useEffect(() => {
    return () => {
      stopCameraStream();
    };
  }, []);

  useEffect(() => {
    if (!preview) return undefined;
    return () => URL.revokeObjectURL(preview);
  }, [preview]);

  const handleModeSwitch = (mode) => {
    setError('');
    setCameraError('');
    if (mode !== 'camera' && isCameraActive) {
      stopCameraStream();
    }
    setInputMode(mode);
  };

  const startCamera = async () => {
    setCameraError('');
    setCameraLoading(true);

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError('Webcam API is not supported by your current browser environment. Please use file upload.');
      setCameraLoading(false);
      return;
    }

    try {
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play().catch(() => {});
        };
      }

      setIsCameraActive(true);
      setCameraLoading(false);
    } catch (err) {
      stopCameraStream();
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraError('Camera access was denied by user or browser permissions. Please allow camera permissions or upload an image file.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setCameraError('No camera device was detected on your system. Please use the file upload option.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setCameraError('Camera hardware is currently in use by another application.');
      } else {
        setCameraError(`Unable to start camera: ${err.message || 'Unknown device error'}`);
      }
      setCameraLoading(false);
    }
  };

  const captureSnapshot = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError('Failed to capture image frame from camera.');
          return;
        }

        const capturedFile = new File([blob], `camera-sample-${Date.now()}.jpg`, {
          type: 'image/jpeg'
        });

        stopCameraStream();
        handleFileSelect(capturedFile);
      },
      'image/jpeg',
      0.95
    );
  };

  const handleFileSelect = (selectedFile) => {
    setError('');
    const validation = validateImageFile(selectedFile);
    if (!validation.valid) {
      setError(validation.error);
      return;
    }

    setFile(selectedFile);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreview(objectUrl);
    setResult(null);
    setDetectionResult(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleClassify = async (overrideThreshold = null) => {
    if (!file) return;

    setLoading(true);
    setError('');

    try {
      const idempotencyKey = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      if (analysisMode === 'multi') {
        const thresholdToUse = overrideThreshold !== null ? overrideThreshold : confThreshold;
        const data = await api.detectWaste(file, true, idempotencyKey, thresholdToUse);
        setDetectionResult(data);
        setResult(null);
      } else {
        const data = await api.predictWaste(file, idempotencyKey);
        setResult(data);
        setDetectionResult(null);
      }
    } catch (err) {
      setError(err.message || 'Network or model inference failure. Please check backend connection.');
      setResult(null);
      setDetectionResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    stopCameraStream();
    setFile(null);
    setPreview(null);
    setResult(null);
    setDetectionResult(null);
    setError('');
    setCameraError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Waste Image Classification & Segregation</h1>
          <p className="page-subtitle">
            {analysisMode === 'multi'
              ? 'Multi-Object Mixed Waste Detection with Bounding Boxes & Per-Item Disposal Directives'
              : 'Intelligent real-time waste detection and digital software-compartment routing (MobileNetV2 12-Class)'}
          </p>
        </div>

        {/* Analysis Mode Selector */}
        <div style={{ display: 'flex', background: '#e2e8f0', borderRadius: '8px', padding: '4px' }}>
          <button
            type="button"
            className="btn btn-sm"
            style={{
              border: 'none',
              borderRadius: '6px',
              padding: '6px 14px',
              fontSize: '0.85rem',
              fontWeight: 600,
              background: analysisMode === 'single' ? '#059669' : 'transparent',
              color: analysisMode === 'single' ? '#fff' : '#475569',
              cursor: 'pointer'
            }}
            onClick={() => {
              setAnalysisMode('single');
              setResult(null);
              setDetectionResult(null);
              setError('');
            }}
          >
            Single Item (MobileNetV2)
          </button>
          <button
            type="button"
            className="btn btn-sm"
            style={{
              border: 'none',
              borderRadius: '6px',
              padding: '6px 14px',
              fontSize: '0.85rem',
              fontWeight: 600,
              background: analysisMode === 'multi' ? '#059669' : 'transparent',
              color: analysisMode === 'multi' ? '#fff' : '#475569',
              cursor: 'pointer'
            }}
            onClick={() => {
              setAnalysisMode('multi');
              setResult(null);
              setDetectionResult(null);
              setError('');
            }}
          >
            Mixed Waste (Multi-Object)
          </button>
        </div>
      </div>

      {analysisMode === 'multi' && (
        <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', padding: '0.75rem 1rem', borderRadius: '8px' }}>
          <FiShield style={{ flexShrink: 0, fontSize: '1.1rem', color: '#15803d' }} />
          <span>
          <strong>Detector limitation:</strong> Labels depend on the configured object detector. The available TorchVision COCO detector is general-purpose, not validated for waste classification; disposal streams are rule-based estimates. Low-confidence or unmapped objects are sent for manual review.
          </span>
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FiAlertCircle style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      <div className="grid-2">
        {/* Left Column: Image Input & Camera Controls */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 className="card-title">Image Input</h3>
              <p className="card-subtitle">Upload file or capture live camera frame</p>
            </div>

            {/* Input Mode Toggle (Only when no image is loaded) */}
            {!preview && (
              <div style={{ display: 'flex', background: '#f1f5f9', borderRadius: '8px', padding: '3px' }}>
                <button
                  type="button"
                  className={`btn btn-sm ${inputMode === 'upload' ? 'btn-primary' : 'btn-outline'}`}
                  style={{
                    border: 'none',
                    borderRadius: '6px',
                    padding: '4px 10px',
                    fontSize: '0.8rem',
                    background: inputMode === 'upload' ? '#059669' : 'transparent',
                    color: inputMode === 'upload' ? '#fff' : '#64748b'
                  }}
                  onClick={() => handleModeSwitch('upload')}
                >
                  <FiUploadCloud style={{ marginRight: '4px' }} /> File Upload
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${inputMode === 'camera' ? 'btn-primary' : 'btn-outline'}`}
                  style={{
                    border: 'none',
                    borderRadius: '6px',
                    padding: '4px 10px',
                    fontSize: '0.8rem',
                    background: inputMode === 'camera' ? '#059669' : 'transparent',
                    color: inputMode === 'camera' ? '#fff' : '#64748b'
                  }}
                  onClick={() => handleModeSwitch('camera')}
                >
                  <FiCamera style={{ marginRight: '4px' }} /> Live Camera
                </button>
              </div>
            )}
          </div>

          {/* Camera Error Message */}
          {cameraError && (
            <div className="alert alert-warning" style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
              <FiAlertCircle style={{ marginRight: '6px' }} />
              {cameraError}
            </div>
          )}

          {/* Mode 1: File Upload (when no preview) */}
          {!preview && inputMode === 'upload' && (
            <div
              className={`upload-area${isDragging ? ' dragover' : ''}`}
              role="button"
              tabIndex={0}
              aria-label="Choose or drop a waste image"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={(e) => {
                if (!e.currentTarget.contains(e.relatedTarget)) setIsDragging(false);
              }}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/jpg"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
                  e.target.value = '';
                }}
              />
              <FiUploadCloud className="upload-icon" />
              <h3>Drag & drop waste image here</h3>
              <p>or click to browse from your device (JPEG, PNG, WebP up to 10MB)</p>
              <span className="badge badge-info" style={{ marginTop: '0.75rem' }}>
                Model Pipeline: 224x224 RGB Normalized
              </span>
            </div>
          )}

          {/* Mode 2: Live Camera View (when no preview) */}
          {!preview && inputMode === 'camera' && (
            <div style={{ textAlign: 'center', padding: '1rem 0' }}>
              <div
                style={{
                  width: '100%',
                  maxHeight: '320px',
                  minHeight: '220px',
                  background: '#0f172a',
                  borderRadius: '10px',
                  overflow: 'hidden',
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid #334155'
                }}
              >
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  style={{
                    width: '100%',
                    height: '100%',
                    maxHeight: '320px',
                    objectFit: 'cover',
                    display: isCameraActive ? 'block' : 'none'
                  }}
                />

                {!isCameraActive && !cameraLoading && (
                  <div style={{ color: '#94a3b8', padding: '2rem 1rem' }}>
                    <FiCamera style={{ fontSize: '3rem', marginBottom: '0.5rem', opacity: 0.6 }} />
                    <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                      Click below to request camera permission and start the live stream
                    </p>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={startCamera}
                    >
                      <FiVideo style={{ marginRight: '6px' }} /> Start Live Camera
                    </button>
                  </div>
                )}

                {cameraLoading && (
                  <div style={{ color: '#ffffff' }}>
                    <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 10px auto' }}></div>
                    <div style={{ fontSize: '0.85rem' }}>Connecting to camera stream...</div>
                  </div>
                )}

                {/* Scanning overlay box when active */}
                {isCameraActive && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '180px',
                      height: '180px',
                      border: '2px dashed #34d399',
                      borderRadius: '12px',
                      boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.4)',
                      pointerEvents: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#a7f3d0',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}
                  >
                    Target Waste Item
                  </div>
                )}
              </div>

              {/* Hidden canvas for snapshot rasterization */}
              <canvas ref={canvasRef} style={{ display: 'none' }} />

              {/* Camera Action Buttons */}
              {isCameraActive && (
                <div style={{ display: 'flex', gap: '10px', marginTop: '1rem' }}>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={stopCameraStream}
                    style={{ flex: 1 }}
                  >
                    <FiVideoOff style={{ marginRight: '6px' }} /> Stop Camera
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={captureSnapshot}
                    style={{ flex: 2 }}
                  >
                    <FiCamera style={{ marginRight: '6px' }} /> Capture Snapshot
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Image Preview & Classification Trigger */}
          {preview && (
            <div>
              <div className="preview-container" style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
                <img
                  src={detectionResult?.annotated_image_base64 || preview}
                  alt="Waste Preview"
                  style={{
                    maxHeight: '320px',
                    width: 'auto',
                    maxWidth: '100%',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    objectFit: 'contain'
                  }}
                />
                <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#6b7280' }}>
                  {file?.name} ({(file?.size / 1024).toFixed(1)} KB)
                  {detectionResult?.annotated_image_base64 && (
                    <span className="badge badge-success" style={{ marginLeft: '8px', fontSize: '0.75rem' }}>
                      Visual Bounding Boxes Overlaid ({detectionResult.detections?.length || 0})
                    </span>
                  )}
                </div>
              </div>

              {analysisMode === 'multi' && (
                <div style={{ marginBottom: '1rem', background: '#f8fafc', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
                      Detector Sensitivity:
                    </span>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#059669' }}>
                      {Math.round(confThreshold * 100)}% Confidence Threshold
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {[
                      { label: 'High Sensitivity (15%)', val: 0.15 },
                      { label: 'Balanced (25%)', val: 0.25 },
                      { label: 'High Precision (40%)', val: 0.40 }
                    ].map((opt) => (
                      <button
                        key={opt.val}
                        type="button"
                        disabled={loading}
                        onClick={() => {
                          setConfThreshold(opt.val);
                          if (detectionResult) {
                            handleClassify(opt.val);
                          }
                        }}
                        style={{
                          flex: 1,
                          padding: '5px 8px',
                          fontSize: '0.75rem',
                          borderRadius: '5px',
                          border: confThreshold === opt.val ? '1px solid #059669' : '1px solid #cbd5e1',
                          background: confThreshold === opt.val ? '#ecfdf5' : '#ffffff',
                          color: confThreshold === opt.val ? '#047857' : '#475569',
                          fontWeight: confThreshold === opt.val ? 700 : 500,
                          cursor: 'pointer'
                        }}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={handleReset}
                  disabled={loading}
                  style={{ flex: 1 }}
                >
                  <FiRefreshCw style={{ marginRight: '6px' }} /> Clear / New
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => handleClassify()}
                  disabled={loading || (analysisMode === 'single' ? !!result : (!!detectionResult && detectionResult.detections?.length > 0))}
                  style={{ flex: 2 }}
                >
                  {loading ? (
                    <>
                      <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px', marginRight: '8px' }}></div>
                      {analysisMode === 'multi' ? 'Scanning Multi-Object Stream...' : 'Analyzing Neural Signature...'}
                    </>
                  ) : (
                    <>
                      <FiCheckCircle style={{ marginRight: '6px' }} />
                      {analysisMode === 'multi' ? 'Detect Mixed Waste Objects' : 'Classify Waste'}
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Real Classification Directives or Multi-Object Output */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              {analysisMode === 'multi' ? 'Multi-Object Segregation Output' : 'Classification Output'}
            </h3>
            <p className="card-subtitle">
              {analysisMode === 'multi'
                ? 'Itemized object detections, bounding boxes & per-item disposal stream routing'
                : 'Neural inference output & authoritative segregation directives'}
            </p>
          </div>

          {!result && !detectionResult && !loading && (
            <div className="empty-state" style={{ padding: '3.5rem 1rem' }}>
              <FiCamera className="empty-icon" />
              <h3>Awaiting Input Image</h3>
              <p>
                {analysisMode === 'multi'
                  ? 'Upload a mixed-waste photograph containing multiple items (e.g. cardboard box, plastic bottle, food scraps, metal cans).'
                  : 'Upload a waste sample or capture a frame from the live camera to trigger deep-learning classification.'}
              </p>
            </div>
          )}

          {loading && (
            <div className="loading-state" style={{ padding: '3.5rem 1rem' }}>
              <div className="spinner"></div>
              <h3>
                {analysisMode === 'multi' ? 'Running Multi-Object Detection' : 'Running Neural Inference'}
              </h3>
              <p>
                {analysisMode === 'multi'
                  ? 'Sending image and waiting for object detection and disposal mapping...'
                  : 'Applying MobileNetV2 224x224 RGB preprocessing & forward pass...'}
              </p>
            </div>
          )}

          {/* Mode 1 Output: Single Item MobileNetV2 */}
          {analysisMode === 'single' && result && !loading && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                <div>
                  <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: '#6b7280', fontWeight: 600 }}>
                    Detected Class
                  </div>
                  <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', textTransform: 'capitalize', margin: '4px 0' }}>
                    {result.predictedClass}
                  </h2>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: '#6b7280', fontWeight: 600 }}>
                    Confidence
                  </div>
                  <span className={`badge ${getConfidenceBadgeClass(result.confidence)}`} style={{ fontSize: '1.1rem', padding: '0.35rem 0.75rem' }}>
                    {result.confidence}%
                  </span>
                </div>
              </div>

              <div className="detail-list" style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1rem' }}>
                {/* Waste Category */}
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.6rem 0', borderBottom: '1px solid #f3f4f6' }}>
                  <span style={{ color: '#6b7280', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FiTag /> Operational Category
                  </span>
                  <span style={{ fontWeight: 600 }}>{result.wasteType}</span>
                </div>

                {/* Destination Compartment */}
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.6rem 0', borderBottom: '1px solid #f3f4f6' }}>
                  <span style={{ color: '#6b7280', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FiCompass /> Target Compartment
                  </span>
                  <span className="badge badge-success" style={{ fontWeight: 600 }}>
                    {result.destinationCompartment || result.disposalBin}
                  </span>
                </div>

                {/* Routing Status */}
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.6rem 0', borderBottom: '1px solid #f3f4f6' }}>
                  <span style={{ color: '#6b7280', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FiShield /> Routing Status
                  </span>
                  <span className={`badge ${result.requiresManualReview ? 'badge-warning' : 'badge-info'}`}>
                    {result.routingStatus || 'AUTOMATED_ROUTED'}
                  </span>
                </div>

                {/* Recommendation */}
                <div style={{ padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
                  <div style={{ color: '#6b7280', fontSize: '0.85rem', marginBottom: '4px' }}>
                    Disposal Directive
                  </div>
                  <div style={{ fontWeight: 500, color: '#1f2937', lineHeight: 1.5 }}>
                    {result.recommendation}
                  </div>
                </div>

                {/* Timestamp */}
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.6rem 0' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>Processed At</span>
                  <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                    {formatDateTime(result.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Mode 2 Output: Mixed-Waste Multi-Object Detection */}
          {analysisMode === 'multi' && detectionResult && !loading && (
            <div>
              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(90px, 1fr))', gap: '8px', marginBottom: '1.25rem' }}>
                <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '6px', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
                    {detectionResult.summary?.total_detections || 0}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Total</div>
                </div>
                <div style={{ background: '#ecfdf5', padding: '8px', borderRadius: '6px', textAlign: 'center', border: '1px solid #a7f3d0' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#047857' }}>
                    {detectionResult.summary?.wet_items || 0}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#047857', fontWeight: 600, textTransform: 'uppercase' }}>Wet Waste</div>
                </div>
                <div style={{ background: '#eff6ff', padding: '8px', borderRadius: '6px', textAlign: 'center', border: '1px solid #bfdbfe' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1d4ed8' }}>
                    {detectionResult.summary?.dry_items || 0}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#1d4ed8', fontWeight: 600, textTransform: 'uppercase' }}>Dry Waste</div>
                </div>
                <div style={{ background: '#fef2f2', padding: '8px', borderRadius: '6px', textAlign: 'center', border: '1px solid #fecaca' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#b91c1c' }}>
                    {detectionResult.summary?.hazardous_items || 0}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#b91c1c', fontWeight: 600, textTransform: 'uppercase' }}>Hazardous</div>
                </div>
                <div style={{ background: '#fffbeb', padding: '8px', borderRadius: '6px', textAlign: 'center', border: '1px solid #fde68a' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#b45309' }}>
                    {detectionResult.summary?.manual_review_items || 0}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#b45309', fontWeight: 600, textTransform: 'uppercase' }}>Review</div>
                </div>
              </div>

              {/* Status Message if unconfigured or empty */}
              {detectionResult.model_status === 'not_configured' && (
                <div className="alert alert-warning" style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>Model Weights Notice:</div>
                  <p style={{ margin: 0 }}>{detectionResult.message}</p>
                </div>
              )}

              {/* Itemized Detected Items List */}
              {detectionResult.detections?.length > 0 ? (
                <div style={{ maxHeight: '380px', overflowY: 'auto', paddingRight: '4px' }}>
                  {detectionResult.detections.map((item) => {
                    const cat = item.disposal?.category || 'manual_review';
                    const badgeClass =
                      cat === 'wet' ? 'badge-success' :
                      cat === 'dry' ? 'badge-info' :
                      cat === 'hazardous' ? 'badge-error' : 'badge-warning';

                    return (
                      <div
                        key={item.detection_id}
                        style={{
                          background: '#ffffff',
                          border: '1px solid #e2e8f0',
                          borderLeft: `4px solid ${item.disposal?.color || '#3b82f6'}`,
                          borderRadius: '6px',
                          padding: '10px 12px',
                          marginBottom: '10px'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b', textTransform: 'capitalize' }}>
                            #{item.detection_id} {item.label.replace(/_/g, ' ')}
                          </span>
                          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                            <span className={`badge ${badgeClass}`} style={{ fontSize: '0.75rem' }}>
                              {item.disposal?.bin_label || 'Unassigned'}
                            </span>
                            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
                              {(item.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        <div style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.4, marginBottom: '6px' }}>
                          <strong>Reason:</strong> {item.disposal?.reason}
                        </div>

                        {item.disposal?.preparation && (
                          <div style={{ fontSize: '0.8rem', color: '#0369a1', background: '#f0f9ff', padding: '4px 8px', borderRadius: '4px', marginBottom: '6px', border: '1px solid #bae6fd' }}>
                            <strong>Prep:</strong> {item.disposal.preparation}
                          </div>
                        )}

                        {item.disposal?.warning && !item.disposal.warning.toLowerCase().includes('unclassified') && (
                          <div style={{ fontSize: '0.8rem', color: '#0369a1', background: '#f0f9ff', padding: '4px 8px', borderRadius: '4px', marginBottom: '6px', border: '1px solid #bae6fd' }}>
                            <strong>Note:</strong> {item.disposal.warning.replace('⚠️', '').trim()}
                          </div>
                        )}

                        <div style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '4px' }}>
                          <span>Compartment: <strong>{item.disposal?.compartment_id || 'Quarantine'}</strong></span>
                          <span>BBox: [{item.bbox?.x1}, {item.bbox?.y1}, {item.bbox?.x2}, {item.bbox?.y2}]</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                detectionResult.model_status !== 'not_configured' && (
                  <div
                    style={{
                      textAlign: 'center',
                      padding: '2rem 1.5rem',
                      background: '#f8fafc',
                      borderRadius: '8px',
                      border: '1px dashed #cbd5e1'
                    }}
                  >
                    <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🔍</div>
                    <h4 style={{ fontWeight: 700, color: '#1e293b', marginBottom: '6px' }}>
                      No Waste Items Detected Above {Math.round(confThreshold * 100)}% Confidence
                    </h4>
                    <p style={{ color: '#64748b', fontSize: '0.85rem', maxWidth: '440px', margin: '0 auto 1.25rem', lineHeight: 1.5 }}>
                      The detector did not locate bounding boxes for individual items above this threshold. This can happen if items overlap heavily, contrast is low, or features are ambiguous.
                    </p>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline"
                        onClick={() => {
                          setConfThreshold(0.15);
                          handleClassify(0.15);
                        }}
                        disabled={loading}
                      >
                        ⚡ Retry with High Sensitivity (15%)
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline"
                        onClick={() => {
                          setAnalysisMode('single');
                          setDetectionResult(null);
                        }}
                        disabled={loading}
                      >
                        🔄 Switch to Single-Item Classifier
                      </button>
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </div>
      </div>

      {/* Digital Segregation Simulation (Renders strictly on successful single-item classification) */}
      {analysisMode === 'single' && result && !loading && (
        <DigitalSegregationSimulation
          result={result}
          imageSrc={preview}
          onReset={handleReset}
        />
      )}
    </div>
  );
}
