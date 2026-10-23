import React, { useState, useEffect } from 'react';
import {
  FiCheckCircle,
  FiAlertTriangle,
  FiRefreshCw,
  FiPlay,
  FiInfo,
  FiArrowRight,
  FiBox
} from 'react-icons/fi';
import { COMPARTMENTS } from '../data/mockData';

export default function DigitalSegregationSimulation({ result, imageSrc, onReset }) {
  const [simStep, setSimStep] = useState(0); // 0: Intake/Scan, 1: Diverting/Transit, 2: Deposited
  const [isAnimating, setIsAnimating] = useState(true);

  const targetCompartmentId = result?.compartmentId || 'bin_residual';
  const targetMeta = COMPARTMENTS[targetCompartmentId] || {
    id: targetCompartmentId,
    name: result?.destinationCompartment || 'General Residual Waste Bin',
    stream: result?.wasteType || 'General Waste',
    color: '#10b981',
    icon: '📦'
  };

  const isQuarantine = result?.requiresManualReview || result?.routingStatus === 'UNSUPPORTED_CLASS';

  // Run the 3-phase digital simulation sequence
  const startSimulation = () => {
    setSimStep(0);
    setIsAnimating(true);

    const t1 = setTimeout(() => {
      setSimStep(1);
    }, 750);

    const t2 = setTimeout(() => {
      setSimStep(2);
      setIsAnimating(false);
    }, 1800);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  };

  useEffect(() => {
    if (result) {
      return startSimulation();
    }
  }, [result]);

  // Primary compartments to display in the digital dock
  const primaryCompartmentKeys = [
    'bin_organic',
    'bin_plastic',
    'bin_cardboard',
    'bin_paper',
    'bin_metal',
    'bin_glass_brown',
    'bin_glass_green',
    'bin_glass_white',
    'bin_hazardous',
    'bin_textile',
    'bin_footwear',
    'bin_residual'
  ];

  // Include quarantine compartment if it's the target
  const displayKeys = isQuarantine
    ? [...primaryCompartmentKeys, 'bin_manual_review']
    : primaryCompartmentKeys;

  return (
    <div className="card" style={{ marginTop: '1.5rem', border: '1px solid #d1fae5' }}>
      {/* Simulation Header */}
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-success" style={{ textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.72rem' }}>
              Software Simulation Only
            </span>
            <span className="badge badge-info" style={{ fontSize: '0.72rem' }}>
              Digital Routing Engine
            </span>
          </div>
          <h3 className="card-title" style={{ marginTop: '6px' }}>
            Smart Segregation Simulation
          </h3>
          <p className="card-subtitle">
            Virtual diverter gate actuation into software-defined disposal compartments
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={startSimulation}
            disabled={isAnimating}
            title="Re-run the digital sorting simulation"
          >
            <FiPlay style={{ marginRight: '4px' }} /> Replay
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={onReset}
            title="Clear and input a new sample"
          >
            <FiRefreshCw style={{ marginRight: '4px' }} /> New Sample
          </button>
        </div>
      </div>

      {/* Software Simulation Disclaimer Banner */}
      <div
        style={{
          background: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: '8px',
          padding: '0.75rem 1rem',
          margin: '0.5rem 0 1.25rem 0',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.85rem',
          color: '#166534'
        }}
      >
        <FiInfo style={{ flexShrink: 0, fontSize: '1.1rem' }} />
        <span>
          <strong>Research Note:</strong> This is a real-time software simulation demonstrating automated sorting directives. No physical electromechanical actuators or servo arms are engaged.
        </span>
      </div>

      {/* Progress Stepper */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem', color: '#4b5563', fontWeight: 500 }}>
          <span style={{ color: simStep >= 0 ? '#059669' : '#9ca3af' }}>
            1. Optical Intake Scan {simStep > 0 && '✓'}
          </span>
          <span style={{ color: simStep >= 1 ? '#059669' : '#9ca3af' }}>
            2. Software Chute Transit {simStep > 1 && '✓'}
          </span>
          <span style={{ color: simStep >= 2 ? (isQuarantine ? '#dc2626' : '#059669') : '#9ca3af' }}>
            3. {isQuarantine ? 'Diverted to Quarantine' : 'Allocated in Target Bin'} {simStep >= 2 && '✓'}
          </span>
        </div>
        <div style={{ width: '100%', height: '8px', background: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: simStep === 0 ? '33%' : simStep === 1 ? '66%' : '100%',
              background: isQuarantine && simStep === 2 ? '#dc2626' : 'linear-gradient(90deg, #10b981, #059669)',
              transition: 'width 0.6s ease-in-out'
            }}
          />
        </div>
      </div>

      {/* Visual Conveyor & Intake Simulation Area */}
      <div
        style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '1.25rem',
          marginBottom: '1.5rem',
          position: 'relative'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Intake Item Node */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              background: '#ffffff',
              padding: '0.75rem 1rem',
              borderRadius: '10px',
              border: '1px solid #cbd5e1',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
              minWidth: '220px'
            }}
          >
            {imageSrc ? (
              <img
                src={imageSrc}
                alt="Intake item"
                style={{
                  width: '54px',
                  height: '54px',
                  objectFit: 'cover',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0'
                }}
              />
            ) : (
              <div
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '6px',
                  background: '#f1f5f9',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <FiBox style={{ fontSize: '1.5rem', color: '#64748b' }} />
              </div>
            )}
            <div>
              <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                Intake Sample
              </div>
              <div style={{ fontWeight: 700, color: '#0f172a', textTransform: 'capitalize' }}>
                {result.predictedClass}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#059669', fontWeight: 600 }}>
                {result.confidence}% confidence
              </div>
            </div>
          </div>

          {/* Transfer Conveyor Indicator */}
          <div style={{ flex: 1, minWidth: '140px', textAlign: 'center' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '0.4rem 0.85rem',
                borderRadius: '20px',
                background: simStep === 1 ? '#dcfce7' : '#f1f5f9',
                color: simStep === 1 ? '#15803d' : '#64748b',
                fontSize: '0.78rem',
                fontWeight: 600,
                transition: 'all 0.3s ease'
              }}
            >
              <span>{simStep === 0 ? 'Scanning' : simStep === 1 ? 'Routing Diverter' : 'Deposited'}</span>
              <FiArrowRight style={{ transform: simStep === 1 ? 'translateX(4px)' : 'none', transition: 'transform 0.3s ease' }} />
            </div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '4px' }}>
              {simStep === 0 && 'Feature extraction in progress...'}
              {simStep === 1 && 'Software gate directing stream...'}
              {simStep === 2 && 'Item logged in software ledger'}
            </div>
          </div>

          {/* Active Target Allocation Pill */}
          <div
            style={{
              padding: '0.75rem 1.25rem',
              borderRadius: '10px',
              background: simStep === 2 ? (isQuarantine ? '#fef2f2' : '#ecfdf5') : '#f8fafc',
              border: `2px solid ${simStep === 2 ? (isQuarantine ? '#ef4444' : '#10b981') : '#e2e8f0'}`,
              minWidth: '240px',
              transition: 'all 0.4s ease'
            }}
          >
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
              Destination Compartment
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.98rem', color: simStep === 2 ? (isQuarantine ? '#b91c1c' : '#047857') : '#1e293b' }}>
              {targetMeta.name}
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
              Stream: {targetMeta.stream}
            </div>
          </div>
        </div>
      </div>

      {/* Compartments Dock View */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.75rem' }}>
          Smart Bin Compartments Dock
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: '10px'
          }}
        >
          {displayKeys.map((key) => {
            const comp = COMPARTMENTS[key];
            if (!comp) return null;
            const isTarget = key === targetCompartmentId;
            const isHighlighted = isTarget && simStep === 2;

            return (
              <div
                key={key}
                style={{
                  background: isHighlighted ? `${comp.color}15` : '#ffffff',
                  border: isHighlighted
                    ? `2px solid ${comp.color}`
                    : isTarget && simStep === 1
                    ? `2px dashed ${comp.color}`
                    : '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  position: 'relative',
                  boxShadow: isHighlighted ? `0 4px 12px ${comp.color}25` : 'none',
                  transition: 'all 0.3s ease'
                }}
              >
                <div
                  style={{
                    fontSize: '1.4rem',
                    width: '38px',
                    height: '38px',
                    borderRadius: '8px',
                    background: `${comp.color}18`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}
                >
                  {comp.icon || '📦'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontWeight: isHighlighted ? 700 : 600,
                      fontSize: '0.82rem',
                      color: isHighlighted ? comp.color : '#1e293b',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                    title={comp.name}
                  >
                    {comp.name}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
                    {comp.stream}
                  </div>
                </div>

                {isHighlighted && (
                  <span
                    style={{
                      position: 'absolute',
                      top: '-7px',
                      right: '8px',
                      background: comp.color,
                      color: '#ffffff',
                      fontSize: '0.62rem',
                      fontWeight: 700,
                      padding: '1px 6px',
                      borderRadius: '10px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em'
                    }}
                  >
                    Target
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Decision Explanation & Directives Card */}
      <div
        style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '10px',
          padding: '1rem 1.25rem'
        }}
      >
        <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#1e293b', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
          {isQuarantine ? <FiAlertTriangle style={{ color: '#dc2626' }} /> : <FiCheckCircle style={{ color: '#059669' }} />}
          Segregation Decision Rationale
        </div>
        <div style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.5, marginBottom: '0.5rem' }}>
          {result.routingReason || 'Standard rule-based mapping applied based on MobileNetV2 classification signature.'}
        </div>
        <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
          <strong>Operator Recommendation:</strong> {result.recommendation}
        </div>
      </div>
    </div>
  );
}
