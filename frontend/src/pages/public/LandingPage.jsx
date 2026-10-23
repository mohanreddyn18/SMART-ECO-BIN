import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  FiCheckCircle,
  FiCamera,
  FiLayers,
  FiShield,
  FiTrendingUp,
  FiArrowRight,
  FiTrash2,
  FiAlertTriangle,
  FiInfo,
  FiBarChart2,
  FiAward
} from 'react-icons/fi';

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
      {/* Top Public Header */}
      <header style={{
        background: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        padding: '0.85rem 1.5rem',
        position: 'sticky',
        top: 0,
        zIndex: 40
      }}>
        <div style={{
          maxWidth: '1280px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: '#059669',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.2rem'
            }}>
              E
            </div>
            <div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>EcoSort AI</span>
              <span style={{ fontSize: '0.75rem', display: 'block', color: '#64748b', fontWeight: 500 }}>
                SMART ECO BIN Public Service
              </span>
            </div>
          </div>

          <nav style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <a href="#features" style={{ color: '#475569', fontSize: '0.9rem', fontWeight: 500, textDecoration: 'none' }}>Features</a>
            <a href="#streams" style={{ color: '#475569', fontSize: '0.9rem', fontWeight: 500, textDecoration: 'none' }}>Waste Streams</a>
            <a href="#models" style={{ color: '#475569', fontSize: '0.9rem', fontWeight: 500, textDecoration: 'none' }}>AI Architecture</a>
            <a href="#provenance" style={{ color: '#475569', fontSize: '0.9rem', fontWeight: 500, textDecoration: 'none' }}>Data Integrity</a>

            {user ? (
              <Link to="/dashboard" className="btn btn-primary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                Open Dashboard <FiArrowRight />
              </Link>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Link to="/login" className="btn btn-outline btn-sm">Sign In</Link>
                <Link to="/register" className="btn btn-primary btn-sm">Register</Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1 }}>
        {/* Hero Section */}
        <section style={{
          padding: '4rem 1.5rem',
          background: 'linear-gradient(180deg, #ecfdf5 0%, #f8fafc 100%)',
          textAlign: 'center'
        }}>
          <div style={{ maxWidth: '900px', margin: '0 auto' }}>
            <span className="badge badge-success" style={{ fontSize: '0.85rem', padding: '0.35rem 0.85rem', marginBottom: '1rem', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <FiAward /> Public Environmental Intelligence Platform
            </span>

            <h1 style={{
              fontSize: 'clamp(2rem, 5vw, 3.25rem)',
              fontWeight: 800,
              color: '#0f172a',
              lineHeight: 1.15,
              letterSpacing: '-0.02em',
              margin: '1rem 0'
            }}>
              Intelligent Waste Segregation Powered by Computer Vision
            </h1>

            <p style={{
              fontSize: 'clamp(1rem, 2vw, 1.25rem)',
              color: '#475569',
              lineHeight: 1.6,
              maxWidth: '740px',
              margin: '0 auto 2rem auto'
            }}>
              Real-time deep learning classification and mixed-waste multi-object localization.
              Equipping citizens and municipal teams with verified disposal directives, prep guidelines, and cloud-ready audit analytics.
            </p>

            <div style={{ display: 'inline-flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              {user ? (
                <>
                  <Link to="/detect" className="btn btn-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                    <FiCamera /> Classify Waste Now
                  </Link>
                  <Link to="/dashboard" className="btn btn-outline" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem' }}>
                    View Citizen Dashboard
                  </Link>
                </>
              ) : (
                <>
                  <Link to="/login" className="btn btn-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                    Get Started / Sign In <FiArrowRight />
                  </Link>
                  <Link to="/register" className="btn btn-outline" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem' }}>
                    Register Free Citizen Account
                  </Link>
                </>
              )}
            </div>
          </div>
        </section>

        {/* Core Value Props Grid */}
        <section id="features" style={{ maxWidth: '1280px', margin: '0 auto', padding: '3.5rem 1.5rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <h2 style={{ fontSize: '1.85rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
              Built for Municipal Realities & Real AI Inference
            </h2>
            <p style={{ color: '#64748b', maxWidth: '600px', margin: '0 auto' }}>
              From single plastic bottles to complex mixed waste heaps, every item is localized, inspected, and routed to the correct destination.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: '#ecfdf5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', marginBottom: '1rem' }}>
                <FiCamera />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>
                Single-Item Classifier
              </h3>
              <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.5 }}>
                Custom fine-tuned MobileNetV2 classifying across 12 distinct waste classes (plastic, paper, cardboard, metal, biological, glass, clothes, battery, and trash) at over 90% test accuracy.
              </p>
            </div>

            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', marginBottom: '1rem' }}>
                <FiLayers />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>
                Mixed-Waste Multi-Object Detection
              </h3>
              <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.5 }}>
                SSDLite320-MobileNetV3 detector scans one photograph containing multiple items, isolates each object with visual bounding boxes, and generates independent disposal directives.
              </p>
            </div>

            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: '#fffbeb', color: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', marginBottom: '1rem' }}>
                <FiShield />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>
                Actionable Preparation & Warnings
              </h3>
              <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.5 }}>
                Practical citizen instructions: rinsing greasy containers, flattening cardboard, isolating hazardous lithium cells, and quarantining contaminated or ambiguous items.
              </p>
            </div>

            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: '#f5f3ff', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', marginBottom: '1rem' }}>
                <FiTrendingUp />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>
                Cloud Analytics & Period Filtering
              </h3>
              <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.5 }}>
                Comprehensive longitudinal telemetry with hourly, daily, weekly, monthly, and yearly windows, baseline comparisons, and multi-series stream volume trends.
              </p>
            </div>
          </div>
        </section>

        {/* Waste Stream Directives */}
        <section id="streams" style={{ background: '#ffffff', padding: '3.5rem 1.5rem', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0' }}>
          <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
              <h2 style={{ fontSize: '1.85rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
                Standardized Waste Streams & Disposal Rules
              </h2>
              <p style={{ color: '#64748b', maxWidth: '600px', margin: '0 auto' }}>
                Aligned with municipal solid waste guidelines and scientific recycling standards.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
              <div style={{ border: '1px solid #bbf7d0', background: '#f0fdf4', borderRadius: '8px', padding: '1.25rem' }}>
                <span className="badge badge-success" style={{ marginBottom: '0.5rem' }}>Wet / Organic</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#166534', margin: '4px 0' }}>Green Compartment</h3>
                <p style={{ fontSize: '0.85rem', color: '#14532d', lineHeight: 1.5 }}>
                  Food scraps, vegetable peels, fruit rinds, leaves, biodegradable organics.
                </p>
                <div style={{ fontSize: '0.78rem', color: '#15803d', marginTop: '8px', fontWeight: 600 }}>
                  Directive: Drain liquids, remove plastic wrappings, transfer to compost.
                </div>
              </div>

              <div style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: '8px', padding: '1.25rem' }}>
                <span className="badge badge-info" style={{ marginBottom: '0.5rem' }}>Dry / Recyclable</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1e40af', margin: '4px 0' }}>Blue Compartment</h3>
                <p style={{ fontSize: '0.85rem', color: '#1e3a8a', lineHeight: 1.5 }}>
                  Clean plastic bottles, paper, corrugated cardboard, metal cans, glass containers.
                </p>
                <div style={{ fontSize: '0.78rem', color: '#1d4ed8', marginTop: '8px', fontWeight: 600 }}>
                  Directive: Empty and rinse thoroughly; food grease contaminates paper mills.
                </div>
              </div>

              <div style={{ border: '1px solid #fecaca', background: '#fef2f2', borderRadius: '8px', padding: '1.25rem' }}>
                <span className="badge badge-error" style={{ marginBottom: '0.5rem' }}>Hazardous & E-Waste</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#991b1b', margin: '4px 0' }}>Red Compartment</h3>
                <p style={{ fontSize: '0.85rem', color: '#7f1d1d', lineHeight: 1.5 }}>
                  Lithium batteries, electronic circuits, aerosol cans, toxic chemicals.
                </p>
                <div style={{ fontSize: '0.78rem', color: '#b91c1c', marginTop: '8px', fontWeight: 600 }}>
                  Directive: Fire and chemical hazard; never place in standard municipal bins.
                </div>
              </div>

              <div style={{ border: '1px solid #fde68a', background: '#fffbeb', borderRadius: '8px', padding: '1.25rem' }}>
                <span className="badge badge-warning" style={{ marginBottom: '0.5rem' }}>Residual / Review</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#92400e', margin: '4px 0' }}>Yellow Compartment</h3>
                <p style={{ fontSize: '0.85rem', color: '#78350f', lineHeight: 1.5 }}>
                  Multi-layer composites, unidentifiable matter, low-confidence predictions.
                </p>
                <div style={{ fontSize: '0.78rem', color: '#b45309', marginTop: '8px', fontWeight: 600 }}>
                  Directive: Sent to manual verification to avoid contaminating bulk recycling lines.
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Model Architecture & Provenance */}
        <section id="models" style={{ maxWidth: '1280px', margin: '0 auto', padding: '3.5rem 1.5rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <h2 style={{ fontSize: '1.85rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
              Dual Neural Architecture
            </h2>
            <p style={{ color: '#64748b', maxWidth: '600px', margin: '0 auto' }}>
              Engineered with lightweight, edge-compatible deep learning backbones for high throughput.
            </p>
          </div>

          <div className="grid-2">
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                  MobileNetV2 Classifier
                </h3>
                <span className="badge badge-success">Single Item Mode</span>
              </div>
              <ul style={{ paddingLeft: '1.25rem', color: '#475569', fontSize: '0.88rem', lineHeight: 1.7, margin: 0 }}>
                <li>Pretrained on ImageNet, custom head trained across 12 distinct waste classes.</li>
                <li>Input: 224x224 RGB image with ImageNet standard normalization.</li>
                <li>Outputs softmax probability vector across 12 target classes.</li>
                <li>Enforces &gt; 60% confidence threshold; low-confidence samples route to manual review.</li>
                <li>Fast inference (~15–40ms CPU latency).</li>
              </ul>
            </div>

            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                  SSDLite320-MobileNetV3 Detector
                </h3>
                <span className="badge badge-info">Multi-Object Mixed Mode</span>
              </div>
              <ul style={{ paddingLeft: '1.25rem', color: '#475569', fontSize: '0.88rem', lineHeight: 1.7, margin: 0 }}>
                <li>TorchVision lightweight object detection network designed for edge devices.</li>
                <li>Localizes individual bounding boxes [x1, y1, x2, y2] for multiple co-located items.</li>
                <li>Maps localized objects (bottles, cups, bananas, cardboard, cans) to municipal waste streams.</li>
                <li>Returns annotated image visualization with overlaid colored bounding boxes and labels.</li>
                <li>Maintains genuine inference honesty with explicit unconfigured/fallback states.</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Data Integrity Section */}
        <section id="provenance" style={{ background: '#f1f5f9', padding: '3rem 1.5rem', borderTop: '1px solid #e2e8f0' }}>
          <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem' }}>
              Public Service Integrity & Scientific Transparency
            </h2>
            <p style={{ color: '#475569', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              EcoSort AI adheres to ethical government and civic technology standards. We simulate segregation compartments in digital logic without asserting physical robotic hardware. To eliminate greenwashing, all environmental statistics are derived purely from empirical classification records without fabricating synthetic carbon offsets.
            </p>
            <div style={{ display: 'inline-flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              <Link to="/login" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                Access System <FiArrowRight />
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer style={{ background: '#0f172a', color: '#94a3b8', padding: '2.5rem 1.5rem', fontSize: '0.85rem' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <strong style={{ color: '#f8fafc', fontSize: '1rem' }}>EcoSort AI</strong> — SMART ECO BIN (RJ147-Smart-Waste)
            <div style={{ marginTop: '4px' }}>Public Service Waste Segregation & Computer Vision Intelligence</div>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            <Link to="/login" style={{ color: '#cbd5e1', textDecoration: 'none' }}>Citizen Sign In</Link>
            <Link to="/register" style={{ color: '#cbd5e1', textDecoration: 'none' }}>Register</Link>
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" style={{ color: '#cbd5e1', textDecoration: 'none' }}>GitHub Repository</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
