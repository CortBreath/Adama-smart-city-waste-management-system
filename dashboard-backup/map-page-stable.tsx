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
  if (fill >= 80) return "progress-critical";
  if (fill >= 50) return "progress-warning";
  return "progress-normal";
}

function getFillLabel(fill: number | null) {
  if (fill === null) return "No data";
  if (fill >= 80) return "Critical";
  if (fill >= 50) return "Warning";
  return "Normal";
}

function formatTime(value: string | null) {
  if (!value) return "No telemetry";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

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

  async function loadBins() {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/bins",
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data: Bin[] = await response.json();

      setBins(data);
      setError("");
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the Adama Smart City API."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBins();

    const interval = setInterval(loadBins, 5000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const normalBins = useMemo(
    () =>
      bins.filter(
        (bin) =>
          normalizeStatus(bin.system_status) === "NORMAL"
      ).length,
    [bins]
  );

  const warningBins = useMemo(
    () =>
      bins.filter(
        (bin) =>
          normalizeStatus(bin.system_status) === "WARNING"
      ).length,
    [bins]
  );

  const criticalBins = useMemo(
    () =>
      bins.filter((bin) => {
        const status = normalizeStatus(bin.system_status);

        return (
          status === "CRITICAL" ||
          status === "FULL"
        );
      }).length,
    [bins]
  );

  const binsWithTelemetry = useMemo(
    () =>
      bins.filter(
        (bin) => bin.recorded_at !== null
      ).length,
    [bins]
  );

  const averageFill = useMemo(() => {
    const values = bins
      .map((bin) => bin.fill_level_pct)
      .filter(
        (value): value is number =>
          value !== null &&
          typeof value === "number"
      );

    if (values.length === 0) {
      return 0;
    }

    return (
      values.reduce(
        (sum, value) => sum + value,
        0
      ) / values.length
    );
  }, [bins]);

  return (
    <main className="dashboard">

      {/* =========================
          HEADER
      ========================= */}

      <header className="dashboard-header">

        <div className="brand">

          <div className="brand-icon">
            ♻
          </div>

          <div>
            <h1>
              Adama Smart City
            </h1>

            <p>
              Smart Waste Management System
            </p>
          </div>

        </div>


        <div className="header-right">

          <div className="live">
            <span className="live-dot"></span>
            LIVE
          </div>

          <div className="header-api">
            API Connected
          </div>

        </div>

      </header>


      {/* =========================
          CONTENT
      ========================= */}

      <section className="dashboard-content">


        {/* =========================
            PAGE TITLE
        ========================= */}

        <div className="page-title">

          <div>

            <div className="eyebrow">
              CITY OPERATIONS
            </div>

            <h2>
              Waste Management Dashboard
            </h2>

            <p>
              Real-time monitoring of smart waste
              collection infrastructure across Adama.
            </p>

          </div>


          <button
            className="refresh-button"
            onClick={loadBins}
          >
            ↻ Refresh
          </button>

        </div>


        {/* =========================
            ERROR
        ========================= */}

        {error && (
          <div className="error-banner">
            <span>⚠</span>
            {error}
          </div>
        )}


        {/* =========================
            SUMMARY CARDS
        ========================= */}

        <div className="summary-grid">


          {/* TOTAL */}

          <div className="summary-card">

            <div className="summary-icon">
              🗑
            </div>

            <div className="summary-content">

              <div className="summary-label">
                TOTAL BINS
              </div>

              <div className="summary-value">
                {bins.length}
              </div>

              <div className="summary-sub">
                Monitored locations
              </div>

            </div>

          </div>


          {/* NORMAL */}

          <div className="summary-card summary-green">

            <div className="summary-icon">
              ✓
            </div>

            <div className="summary-content">

              <div className="summary-label">
                NORMAL
              </div>

              <div className="summary-value">
                {normalBins}
              </div>

              <div className="summary-sub">
                Operating normally
              </div>

            </div>

          </div>


          {/* WARNING */}

          <div className="summary-card summary-yellow">

            <div className="summary-icon">
              !
            </div>

            <div className="summary-content">

              <div className="summary-label">
                WARNING
              </div>

              <div className="summary-value">
                {warningBins}
              </div>

              <div className="summary-sub">
                Requires attention
              </div>

            </div>

          </div>


          {/* CRITICAL */}

          <div className="summary-card summary-red">

            <div className="summary-icon">
              !
            </div>

            <div className="summary-content">

              <div className="summary-label">
                CRITICAL
              </div>

              <div className="summary-value">
                {criticalBins}
              </div>

              <div className="summary-sub">
                Immediate attention
              </div>

            </div>

          </div>


          {/* AVERAGE FILL */}

          <div className="summary-card">

            <div className="summary-icon">
              ◔
            </div>

            <div className="summary-content">

              <div className="summary-label">
                AVERAGE FILL
              </div>

              <div className="summary-value">
                {averageFill.toFixed(1)}%
              </div>

              <div className="summary-sub">
                Across monitored bins
              </div>

            </div>

          </div>

        </div>


        {/* =========================
            OPERATIONS GRID
        ========================= */}

        <div className="operations-grid">


          {/* =========================
              MAP
          ========================= */}

          <div className="map-card">

            <div className="card-header">

              <div>

                <h3>
                  Live Bin Map
                </h3>

                <p>
                  Real-time locations and operational status
                </p>

              </div>


              <div className="map-status">

                <span className="live-dot"></span>

                Live

              </div>

            </div>


            <div className="map-container">

              <GISMapWrapper bins={bins} />

            </div>


            {/* MAP LEGEND */}

            <div className="map-legend">

              <div className="legend-title">
                STATUS LEGEND
              </div>

              <div className="legend-items">

                <div className="legend-item">
                  <span className="legend-dot legend-green"></span>
                  Normal
                </div>

                <div className="legend-item">
                  <span className="legend-dot legend-yellow"></span>
                  Warning
                </div>

                <div className="legend-item">
                  <span className="legend-dot legend-red"></span>
                  Critical / Full
                </div>

              </div>

            </div>

          </div>


          {/* =========================
              BIN LIST
          ========================= */}

          <div className="bin-list-card">

            <div className="card-header">

              <div>

                <h3>
                  Waste Bins
                </h3>

                <p>
                  Current sensor status
                </p>

              </div>


              <span className="bin-count">
                {bins.length}
              </span>

            </div>


            <div className="bin-list">

              {loading && bins.length === 0 ? (

                <div className="empty-state">

                  <div className="loading-spinner"></div>

                  <p>
                    Loading bins...
                  </p>

                </div>

              ) : bins.length === 0 ? (

                <div className="empty-state">

                  <div className="empty-icon">
                    🗑
                  </div>

                  <p>
                    No bin data available
                  </p>

                </div>

              ) : (

                bins.map((bin) => {

                  const statusClass =
                    getStatusClass(
                      bin.system_status
                    );

                  const fill =
                    bin.fill_level_pct ?? 0;

                  const safeFill =
                    Math.min(
                      Math.max(fill, 0),
                      100
                    );

                  return (

                    <div
                      key={bin.bin_id}
                      className={`bin-row ${statusClass}-row`}
                    >


                      {/* BIN HEADER */}

                      <div className="bin-row-top">

                        <div className="bin-name">

                          <span
                            className={`bin-marker ${statusClass}`}
                          >
                            ●
                          </span>

                          <strong>
                            {bin.bin_id}
                          </strong>

                        </div>


                        <span
                          className={`status-pill ${statusClass}`}
                        >
                          {bin.system_status ??
                            "NO DATA"}
                        </span>

                      </div>


                      {/* FILL */}

                      <div className="bin-fill">

                        <div className="bin-fill-header">

                          <span>
                            Fill level
                          </span>

                          <strong>
                            {bin.fill_level_pct !== null
                              ? `${bin.fill_level_pct.toFixed(
                                  1
                                )}%`
                              : "No data"}
                          </strong>

                        </div>


                        <div className="mini-progress">

                          <div
                            className={`mini-progress-bar ${getFillClass(
                              bin.fill_level_pct
                            )}`}
                            style={{
                              width: `${safeFill}%`,
                            }}
                          />

                        </div>


                        <div className="fill-label">

                          {getFillLabel(
                            bin.fill_level_pct
                          )}

                        </div>

                      </div>


                      {/* SENSOR DETAILS */}

                      <div className="bin-details">

                        <span>
                          🌡{" "}
                          {bin.temperature !== null
                            ? `${bin.temperature.toFixed(
                                1
                              )}°C`
                            : "--"}
                        </span>


                        <span>
                          🔥{" "}
                          {bin.smoke_status ??
                            "--"}
                        </span>


                        <span>
                          🚪{" "}
                          {bin.lid_status ??
                            "--"}
                        </span>

                      </div>


                      {/* DATA SOURCE */}

                      <div className="bin-meta">

                        <span>
                          {bin.data_source ===
                          "HARDWARE"
                            ? "● Hardware"
                            : "● Simulated"}
                        </span>

                        <span>
                          {formatTime(
                            bin.recorded_at
                          )}
                        </span>

                      </div>


                      {/* BUTTON */}

                      <button
                        className="view-bin-button"
                        onClick={() => {
                          window.location.href =
                            `/bins/${bin.bin_id}`;
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


        {/* =========================
            SYSTEM INFORMATION
        ========================= */}

        <div className="system-panel">

          <div className="system-panel-title">

            <div>

              <h3>
                System Status
              </h3>

              <p>
                Smart waste infrastructure connectivity
              </p>

            </div>


            <div className="system-online">

              <span className="footer-dot"></span>

              System Online

            </div>

          </div>


          <div className="system-stats">


            <div className="system-stat">

              <span className="system-stat-icon">
                ◉
              </span>

              <div>

                <span className="system-stat-label">
                  TELEMETRY
                </span>

                <strong>
                  {binsWithTelemetry}/
                  {bins.length}
                </strong>

              </div>

            </div>


            <div className="system-stat">

              <span className="system-stat-icon">
                ↔
              </span>

              <div>

                <span className="system-stat-label">
                  MQTT
                </span>

                <strong>
                  Connected
                </strong>

              </div>

            </div>


            <div className="system-stat">

              <span className="system-stat-icon">
                ◉
              </span>

              <div>

                <span className="system-stat-label">
                  BROKER
                </span>

                <strong>
                  broker.emqx.io
                </strong>

              </div>

            </div>


            <div className="system-stat">

              <span className="system-stat-icon">
                ↻
              </span>

              <div>

                <span className="system-stat-label">
                  AUTO REFRESH
                </span>

                <strong>
                  5 seconds
                </strong>

              </div>

            </div>


            <div className="system-stat">

              <span className="system-stat-icon">
                ●
              </span>

              <div>

                <span className="system-stat-label">
                  LAST UPDATE
                </span>

                <strong>
                  {formatTime(lastUpdated)}
                </strong>

              </div>

            </div>

          </div>

        </div>


        {/* =========================
            FOOTER
        ========================= */}

        <footer className="dashboard-footer">

          <span>
            Adama Smart City
          </span>

          <span>
            Smart Waste Management
          </span>

          <span>
            Live telemetry monitoring
          </span>

        </footer>

      </section>

    </main>
  );
}