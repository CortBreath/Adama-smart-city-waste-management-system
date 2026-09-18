"use client";

import { useEffect, useMemo, useState } from "react";
import GISMapWrapper from "../components/GISMapWrapper";

type Bin = {
  bin_id: string;
  latitude: number;
  longitude: number;
  status: string;
  data_source: string;
  fill_level_pct: number | null;
  fill_distance?: number | null;
  temperature: number | null;
  smoke_value?: number | null;
  smoke_status: string | null;
  human_distance?: number | null;
  lid_status: string | null;
  system_status: string | null;
  recorded_at: string | null;
};

type Alert = {
  id: number;
  bin_id: string;
  alert_type: string;
  severity: string;
  message: string;
  created_at: string;
  resolved_at: string | null;
  assigned_janitor_id: number | null;
  janitor_name: string | null;
  trigger_fill_level: number | null;
  cleanup_notification_sent: boolean;
  status: string;
};

function normalizeStatus(status: string | null | undefined) {
  return (status ?? "").toUpperCase();
}

function getStatusClass(status: string | null | undefined) {
  const value = normalizeStatus(status);
  if (value === "NORMAL") return "normal";
  if (value === "WARNING") return "warning";
  if (value === "CRITICAL") return "critical";
  if (value === "FULL") return "full";
  return "unknown";
}

function getFillClass(fill: number | null) {
  if (fill === null) return "progress-unknown";
  if (fill >= 90) return "progress-critical";
  if (fill >= 60) return "progress-warning";
  return "progress-normal";
}

function getFillLabel(fill: number | null) {
  if (fill === null) return "No data";
  if (fill >= 90) return "Critical";
  if (fill >= 60) return "Warning";
  return "Normal";
}

function formatTime(value: string | null) {
  if (!value) return "No telemetry";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function Home() {
  const [bins, setBins] = useState<Bin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);

  function handleLogout() {
  localStorage.removeItem("access_token");
  window.location.replace("/login");
  }

  async function loadBins() {
  try {
    const token = localStorage.getItem("access_token");

    const response = await fetch("http://127.0.0.1:8000/api/bins", {
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) throw new Error(`API returned ${response.status}`);

    const data: Bin[] = await response.json();
    setBins(data);
    setApiConnected(true);
    setError("");
    setLastUpdated(new Date().toISOString());
  } catch (err) {
  console.error(err);
  setApiConnected(false);
  setError("Unable to connect to the Adama Smart City API.");
  }finally {
    setLoading(false);
  }
}

async function loadActiveAlerts() {
  try {
    const token = localStorage.getItem("access_token");

    const response = await fetch(
      "http://127.0.0.1:8000/api/alerts/active",
      {
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Alerts API returned ${response.status}`);
    }

    const data: Alert[] = await response.json();

    setActiveAlerts(data);
  } catch (err) {
    console.error("Unable to load active alerts:", err);
  }
}

    useEffect(() => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    window.location.replace("/login");
    return;
  }

  setAuthChecking(false);

  loadBins();
  loadActiveAlerts();

  const interval = setInterval(() => {
   loadBins();
   loadActiveAlerts();
  }, 5000);

  return () => clearInterval(interval);
}, []);

  const normalBins = useMemo(
    () => bins.filter((bin) => normalizeStatus(bin.system_status) === "NORMAL").length,
    [bins]
  );

  const warningBins = useMemo(
    () => bins.filter((bin) => normalizeStatus(bin.system_status) === "WARNING").length,
    [bins]
  );

  const criticalBins = useMemo(
    () =>
      bins.filter((bin) => {
        const status = normalizeStatus(bin.system_status);
        return status === "CRITICAL" || status === "FULL";
      }).length,
    [bins]
  );

  const binsWithTelemetry = useMemo(
    () => bins.filter((bin) => bin.recorded_at !== null).length,
    [bins]
  );

  const averageFill = useMemo(() => {
    const values = bins
      .map((bin) => bin.fill_level_pct)
      .filter((value): value is number => typeof value === "number");

    return values.length
      ? values.reduce((sum, value) => sum + value, 0) / values.length
      : 0;
  }, [bins]);

  const cityStatus = criticalBins > 0
    ? {
        className: "critical",
        icon: "!",
        title: "Critical Attention Required",
        message: `${criticalBins} bin${criticalBins === 1 ? "" : "s"} require immediate attention.`,
      }
    : warningBins > 0
    ? {
        className: "warning",
        icon: "!",
        title: "Collection Attention Required",
        message: `${warningBins} bin${warningBins === 1 ? "" : "s"} currently need attention.`,
      }
    : {
        className: "normal",
        icon: "✓",
        title: "City Operations Running Normally",
        message: "All monitored waste bins are operating within normal limits.",
      };

   if (authChecking) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "Inter, sans-serif",
          color: "#10233f",
        }}
      >
        Checking authentication...
      </div>
    );
  }
     
  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div className="brand">
          <div className="brand-icon">♻</div>
          <div className="brand-text">
            <h1>Adama Smart City</h1>
            <p>Smart Waste Management System</p>
          </div>
        </div>

        <div className="header-right">
     <div className="live">
    <span className="live-dot" />
     LIVE
   </div>

  <div className={`header-api ${apiConnected ? "connected" : "disconnected"}`}>
  {apiConnected ? "API Connected" : "API Disconnected"}
</div>

  <button
    className="logout-button"
    onClick={handleLogout}
  >
    Logout
  </button>
</div>
      </header>

      <section className="dashboard-content">
        <div className="page-title">
          <div>
            <div className="eyebrow">CITY OPERATIONS</div>
            <h2>Operations Dashboard</h2>
            <p>
              Real-time monitoring of smart waste collection infrastructure
              across Adama.
            </p>
          </div>

          <button className="refresh-button" onClick={loadBins}>
            ↻ <span>Refresh</span>
          </button>
        </div>

        {error && (
          <div className="error-banner">
            <span className="error-icon">!</span>
            <div>
              <strong>Connection problem</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        <div className={`city-status ${cityStatus.className}`}>
          <div className="city-status-left">
            <div className="city-status-icon">{cityStatus.icon}</div>
            <div>
              <span>Current City Status</span>
              <strong>{cityStatus.title}</strong>
            </div>
          </div>
          <div className="city-status-right">
            <span className="live-dot" />
            {cityStatus.message}
          </div>
        </div>
        <div className="active-alerts-panel">
  <div className="active-alerts-header">
    <div>
      <div className="section-eyebrow">DECISION ENGINE</div>
      <h3>Active Alerts</h3>
      <p>Current collection and environmental alerts requiring attention</p>
    </div>

    <span className="active-alert-count">
      {activeAlerts.length}
    </span>
  </div>

  {activeAlerts.length === 0 ? (
    <div className="no-active-alerts">
      <span>✓</span>
      <div>
        <strong>No active alerts</strong>
        <p>BIN-001 is currently operating without open collection or environmental alerts.</p>
      </div>
    </div>
  ) : (
    <div className="active-alert-list">
      {activeAlerts.map((alert) => (
        <div
          key={alert.id}
          className={`active-alert ${alert.severity.toLowerCase()}`}
        >
          <div className="active-alert-icon">!</div>

          <div className="active-alert-content">
            <div className="active-alert-top">
              <strong>{alert.bin_id}</strong>

              <span
                className={`active-alert-severity ${alert.severity.toLowerCase()}`}
              >
                {alert.severity}
              </span>
            </div>

           <p>
             {alert.alert_type === "FULL_BIN"
             ? `Collection required at ${
             alert.trigger_fill_level !== null
             ? `${Number(alert.trigger_fill_level).toFixed(1)}%`
             : "--"
             }.`
             : alert.alert_type === "SMOKE_DETECTED"
             ? "Smoke detected inside the bin. Immediate inspection required."
             : alert.alert_type === "HIGH_TEMPERATURE"
             ? "High temperature detected inside the bin. Immediate inspection required."
             : alert.alert_type === "SMOKE_AND_HIGH_TEMPERATURE"
             ? "Smoke and high temperature detected inside the bin. Immediate inspection required."
             : alert.message}
          </p>

            <div className="active-alert-meta">
              <span>
                👷 {alert.janitor_name ?? "No janitor assigned"}
              </span>

              <span>
                🕒 {formatTime(alert.created_at)}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )}
</div>
        <div className="summary-grid">
          <div className="summary-card">
            <div className="summary-card-top">
              <div className="summary-icon blue">♻</div>
              <span className="summary-trend">MONITORED</span>
            </div>
            <div className="summary-label">TOTAL BINS</div>
            <div className="summary-value">{bins.length}</div>
            <div className="summary-sub">Monitored locations</div>
          </div>

          <div className="summary-card green">
            <div className="summary-card-top">
              <div className="summary-icon green">✓</div>
              <span className="summary-trend positive">HEALTHY</span>
            </div>
            <div className="summary-label">NORMAL</div>
            <div className="summary-value">{normalBins}</div>
            <div className="summary-sub">Operating normally</div>
          </div>

          <div className="summary-card yellow">
            <div className="summary-card-top">
              <div className="summary-icon yellow">!</div>
              <span className="summary-trend attention">ATTENTION</span>
            </div>
            <div className="summary-label">WARNING</div>
            <div className="summary-value">{warningBins}</div>
            <div className="summary-sub">Requires attention</div>
          </div>

          <div className="summary-card red">
            <div className="summary-card-top">
              <div className="summary-icon red">!</div>
              <span className="summary-trend danger">URGENT</span>
            </div>
            <div className="summary-label">CRITICAL</div>
            <div className="summary-value">{criticalBins}</div>
            <div className="summary-sub">Immediate attention</div>
          </div>

          <div className="summary-card">
            <div className="summary-card-top">
              <div className="summary-icon purple">◉</div>
              <span className="summary-trend">AVERAGE</span>
            </div>
            <div className="summary-label">AVERAGE FILL</div>
            <div className="summary-value">{averageFill.toFixed(1)}%</div>
            <div className="summary-sub">Across monitored bins</div>
          </div>
        </div>

        <div className="operations-grid">
          <div className="map-card">
            <div className="card-header">
              <div>
                <div className="section-eyebrow">REAL-TIME GIS</div>
                <h3>Live Bin Map</h3>
                <p>Real-time locations and operational status</p>
              </div>
              <div className="map-status">
                <span className="live-dot" />
                Live
              </div>
            </div>

            <div className="map-container">
              <GISMapWrapper bins={bins} />
            </div>

          </div>

          <div className="bin-list-card">
            <div className="card-header">
              <div>
                <div className="section-eyebrow">SENSOR NETWORK</div>
                <h3>Waste Bins</h3>
                <p>Current sensor status</p>
              </div>
              <span className="bin-count">{bins.length}</span>
            </div>

            <div className="bin-list">
              {loading && bins.length === 0 ? (
                <div className="empty-state">
                  <div className="loading-spinner" />
                  <p>Loading bins...</p>
                </div>
              ) : bins.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">♻</div>
                  <p>No bin data available</p>
                </div>
              ) : (
                bins.map((bin) => {
                  const statusClass = getStatusClass(bin.system_status);
                  const fill = bin.fill_level_pct ?? 0;
                  const safeFill = Math.min(Math.max(fill, 0), 100);

                  return (
                    <div
                      key={bin.bin_id}
                      className={`bin-row ${statusClass}-row`}
                    >
                      <div className="bin-row-top">
                        <div className="bin-name">
                          <span className={`bin-marker ${statusClass}`}>●</span>
                          <strong>{bin.bin_id}</strong>
                        </div>
                        <span className={`status-pill ${statusClass}`}>
                          {bin.system_status ?? "NO DATA"}
                        </span>
                      </div>

                      <div className="bin-fill">
                        <div className="bin-fill-header">
                          <span>Fill level</span>
                          <strong>
                            {bin.fill_level_pct !== null
                              ? `${bin.fill_level_pct.toFixed(1)}%`
                              : "No data"}
                          </strong>
                        </div>
                        <div className="mini-progress">
                          <div
                            className={`mini-progress-bar ${getFillClass(
                              bin.fill_level_pct
                            )}`}
                            style={{ width: `${safeFill}%` }}
                          />
                        </div>
                        <div className="fill-label">
                          {getFillLabel(bin.fill_level_pct)}
                        </div>
                      </div>

                      <div className="bin-details">
                        <span>🌡 {bin.temperature !== null ? `${bin.temperature.toFixed(1)}°C` : "--"}</span>
                        <span>🔥 {bin.smoke_status ?? "--"}</span>
                        <span>🚪 {bin.lid_status ?? "--"}</span>
                      </div>

                      <div className="bin-meta">
                        <span>
                          {bin.data_source === "HARDWARE"
                            ? "● Hardware"
                            : "● Simulated"}
                        </span>
                        <span>{formatTime(bin.recorded_at)}</span>
                      </div>

                      <button
                        className="view-bin-button"
                        onClick={() => {
                          window.location.href = `/bins/${bin.bin_id}`;
                        }}
                      >
                        View Dashboard →
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        <div className="system-panel">
          <div className="system-panel-title">
            <div>
              <h3>System Status</h3>
              <p>Smart waste infrastructure connectivity</p>
            </div>
            <div className="system-online">
              <span className="footer-dot" />
              System Online
            </div>
          </div>

          <div className="system-stats">
            <div className="system-stat">
              <span className="system-stat-icon">◉</span>
              <div>
                <span className="system-stat-label">TELEMETRY</span>
                <strong>{binsWithTelemetry}/{bins.length}</strong>
              </div>
            </div>
            <div className="system-stat">
              <span className="system-stat-icon">→</span>
              <div>
                <span className="system-stat-label">MQTT</span>
                <strong>Connected</strong>
              </div>
            </div>
            <div className="system-stat">
              <span className="system-stat-icon">◉</span>
              <div>
                <span className="system-stat-label">BROKER</span>
                <strong>broker.emqx.io</strong>
              </div>
            </div>
            <div className="system-stat">
              <span className="system-stat-icon">↻</span>
              <div>
                <span className="system-stat-label">AUTO REFRESH</span>
                <strong>5 seconds</strong>
              </div>
            </div>
            <div className="system-stat">
              <span className="system-stat-icon">●</span>
              <div>
                <span className="system-stat-label">LAST UPDATE</span>
                <strong>{formatTime(lastUpdated)}</strong>
              </div>
            </div>
          </div>
        </div>

        <footer className="dashboard-footer">
          <span>Adama Smart City</span>
          <span>Smart Waste Management</span>
          <span>Live telemetry monitoring</span>
        </footer>
      </section>
    </main>
  );
}
