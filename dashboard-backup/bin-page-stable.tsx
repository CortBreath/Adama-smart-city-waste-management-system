"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

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

function normalize(value: string | null | undefined) {
  return (value ?? "").toUpperCase();
}

function statusClass(value: string | null | undefined) {
  const status = normalize(value);

  if (status === "NORMAL") return "normal";
  if (status === "WARNING") return "warning";
  if (status === "CRITICAL") return "critical";
  if (status === "FULL") return "critical";

  return "unknown";
}

function formatTime(value: string | null) {
  if (!value) return "--";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function BinPage() {
  const params = useParams();
  const binId = params?.binId as string;

  const [bin, setBin] = useState<Bin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadBin() {
    if (!binId) return;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/bins/${binId}`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data: Bin = await response.json();

      setBin(data);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Unable to load bin information.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBin();

    const interval = setInterval(loadBin, 3000);

    return () => clearInterval(interval);
  }, [binId]);

  if (loading) {
    return (
      <main className="bin-dashboard">
        <div className="bin-loading">
          <div className="loading-spinner"></div>
          <p>Loading bin information...</p>
        </div>
      </main>
    );
  }

  if (error || !bin) {
    return (
      <main className="bin-dashboard">
        <div className="bin-error">
          <h2>Unable to load bin</h2>
          <p>{error || "Bin not found."}</p>

          <button
            onClick={() => {
              window.location.href = "/";
            }}
          >
            ← Back to Map
          </button>
        </div>
      </main>
    );
  }

  const currentStatus = normalize(bin.system_status);
  const currentStatusClass = statusClass(bin.system_status);

  const fill =
    bin.fill_level_pct !== null
      ? Math.min(Math.max(bin.fill_level_pct, 0), 100)
      : 0;

  const isCritical =
    currentStatus === "CRITICAL" ||
    currentStatus === "FULL";

  const isWarning = currentStatus === "WARNING";

  const statusMessage = isCritical
    ? "Immediate collection required"
    : isWarning
      ? "Collection attention required"
      : "Operating normally";

  return (
    <main className="bin-dashboard">

      {/* ==========================================
          HEADER
      ========================================== */}

      <header className="bin-header">
        <div className="bin-brand">

          <div className="bin-logo">
            ♻
          </div>

          <div>
            <h1>Adama Smart City</h1>
            <p>Smart Waste Management System</p>
          </div>

        </div>

        <div className="bin-header-actions">

          <div className="bin-live">
            <span></span>
            LIVE
          </div>

          <button
            className="back-map-button"
            onClick={() => {
              window.location.href = "/";
            }}
          >
            ← Back to Map
          </button>

        </div>
      </header>

      {/* ==========================================
          MAIN
      ========================================== */}

      <section className="bin-content">

        {/* Breadcrumb */}

        <div className="bin-breadcrumb">
          <span>City Operations</span>
          <b>›</b>
          <span>Waste Bins</span>
          <b>›</b>
          <strong>{bin.bin_id}</strong>
        </div>

        {/* ==========================================
            TITLE
        ========================================== */}

        <div className="bin-title-row">

          <div>

            <h2 className="bin-page-title">
              <span
                className={`title-status-dot ${currentStatusClass}`}
              ></span>

              {bin.bin_id}
            </h2>

            <p className="bin-page-subtitle">
              Smart waste bin monitoring dashboard
            </p>

          </div>

          <div className="auto-update">

            <span className="auto-dot"></span>

            <strong>Updating automatically</strong>

            <span className="separator">•</span>

            <span>Every 3 seconds</span>

          </div>

        </div>

        {/* ==========================================
            STATUS HERO
        ========================================== */}

        <section
          className={`status-hero ${currentStatusClass}`}
        >

          <div className="status-hero-left">

            <div className="status-warning-icon">
              !
            </div>

            <div>

              <div className="small-heading">
                SYSTEM STATUS
              </div>

              <div className="status-large">
                {bin.system_status ?? "UNKNOWN"}
              </div>

              <div className="status-message">
                {statusMessage}
              </div>

            </div>

          </div>

          <div className="status-hero-right">

            <div className="status-badge">
              {bin.system_status ?? "UNKNOWN"}
            </div>

            <div className="source-text">
              Data source:{" "}
              <strong>{bin.data_source}</strong>
            </div>

          </div>

        </section>

        {/* ==========================================
            FILL LEVEL
        ========================================== */}

        <section className="fill-card">

          <div className="fill-header">

            <div>

              <div className="section-label">
                WASTE CAPACITY
              </div>

              <h3>
                Current Fill Level
              </h3>

            </div>

            <div className="fill-percentage">
              {bin.fill_level_pct !== null
                ? `${bin.fill_level_pct.toFixed(1)}%`
                : "--"}
            </div>

          </div>

          <div className="large-progress">
            <div
              className={`large-progress-bar ${
                fill >= 80
                  ? "fill-red"
                  : fill >= 50
                    ? "fill-yellow"
                    : "fill-green"
              }`}
              style={{
                width: `${fill}%`,
              }}
            ></div>
          </div>

          <div className="fill-scale">

            <span>Empty</span>

            <span>50%</span>

            <span>70%</span>

            <span>90%</span>

            <span>Full</span>

          </div>

          <div className="collection-notice">

            <div className="notice-icon">
              !
            </div>

            <div>
              <strong>
                {isCritical
                  ? "Collection required"
                  : isWarning
                    ? "Collection attention required"
                    : "No collection required"}
              </strong>

              <span>
                Fill sensor distance:{" "}
                {bin.fill_distance !== null &&
                bin.fill_distance !== undefined
                  ? `${bin.fill_distance.toFixed(2)} cm`
                  : "--"}
              </span>
            </div>

          </div>

        </section>

        {/* ==========================================
            TELEMETRY
        ========================================== */}

        <section className="telemetry-section">

          <div className="telemetry-heading">

            <div>

              <div className="section-label">
                LIVE TELEMETRY
              </div>

              <h3>Sensor Readings</h3>

            </div>

            <div className="live-data">
              <span></span>
              Live data
            </div>

          </div>

          <div className="telemetry-grid">

            {/* FILL */}

            <div className="telemetry-card">

              <div className="telemetry-icon fill-icon">
                ◫
              </div>

              <div className="telemetry-info">

                <div className="telemetry-label">
                  FILL LEVEL
                </div>

                <strong>
                  {bin.fill_level_pct !== null
                    ? `${bin.fill_level_pct.toFixed(1)}%`
                    : "--"}
                </strong>

                <span>
                  Distance:{" "}
                  {bin.fill_distance !== null &&
                  bin.fill_distance !== undefined
                    ? `${bin.fill_distance.toFixed(2)} cm`
                    : "--"}
                </span>

              </div>

            </div>

            {/* TEMPERATURE */}

            <div className="telemetry-card">

              <div className="telemetry-icon temperature-icon">
                °C
              </div>

              <div className="telemetry-info">

                <div className="telemetry-label">
                  TEMPERATURE
                </div>

                <strong>
                  {bin.temperature !== null
                    ? `${bin.temperature.toFixed(1)} °C`
                    : "--"}
                </strong>

                <span>
                  Environmental sensor
                </span>

              </div>

            </div>

            {/* SMOKE */}

            <div className="telemetry-card">

              <div className="telemetry-icon smoke-icon">
                !
              </div>

              <div className="telemetry-info">

                <div className="telemetry-label">
                  SMOKE
                </div>

                <strong>
                  {bin.smoke_status ?? "--"}
                </strong>

                <span>
                  Sensor value:{" "}
                  {bin.smoke_value !== null &&
                  bin.smoke_value !== undefined
                    ? Number(bin.smoke_value).toFixed(2)
                    : "--"}
                </span>

              </div>

            </div>

            {/* LID */}

            <div className="telemetry-card">

              <div className="telemetry-icon lid-icon">
                □
              </div>

              <div className="telemetry-info">

                <div className="telemetry-label">
                  LID STATUS
                </div>

                <strong>
                  {bin.lid_status ?? "--"}
                </strong>

                <span>
                  Smart lid sensor
                </span>

              </div>

            </div>

            {/* HUMAN DISTANCE */}

            <div className="telemetry-card">

              <div className="telemetry-icon human-icon">
                •
              </div>

              <div className="telemetry-info">

                <div className="telemetry-label">
                  HUMAN DISTANCE
                </div>

                <strong>
                  {bin.human_distance !== null &&
                  bin.human_distance !== undefined
                    ? `${bin.human_distance.toFixed(1)} cm`
                    : "--"}
                </strong>

                <span>
                  Proximity sensor
                </span>

              </div>

            </div>

            {/* DATA SOURCE */}

            <div className="telemetry-card">

              <div className="telemetry-icon source-icon">
                ◉
              </div>

              <div className="telemetry-info">

                <div className="telemetry-label">
                  DATA SOURCE
                </div>

                <strong>
                  {bin.data_source}
                </strong>

                <span>
                  Telemetry connection
                </span>

              </div>

            </div>

          </div>

        </section>

        {/* ==========================================
            LOCATION + SYSTEM
        ========================================== */}

        <section className="info-grid">

          {/* LOCATION */}

          <div className="info-card">

            <div className="info-card-header">

              <div className="info-icon gps-icon">
                ◉
              </div>

              <div>

                <div className="section-label">
                  GPS
                </div>

                <h3>Bin Location</h3>

              </div>

            </div>

            <div className="info-lines">

              <div className="info-line">

                <span>Latitude</span>

                <strong>
                  {bin.latitude.toFixed(2)}
                </strong>

              </div>

              <div className="info-line">

                <span>Longitude</span>

                <strong>
                  {bin.longitude.toFixed(2)}
                </strong>

              </div>

              <div className="info-line">

                <span>Bin ID</span>

                <strong>
                  {bin.bin_id}
                </strong>

              </div>

            </div>

          </div>

          {/* SYSTEM */}

          <div className="info-card">

            <div className="info-card-header">

              <div className="info-icon system-icon">
                ⚙
              </div>

              <div>

                <div className="section-label">
                  CONNECTIVITY
                </div>

                <h3>System Information</h3>

              </div>

            </div>

            <div className="info-lines">

              <div className="info-line">

                <span>System status</span>

                <strong
                  className={
                    isCritical
                      ? "text-red"
                      : isWarning
                        ? "text-yellow"
                        : "text-green"
                  }
                >
                  {bin.system_status ?? "--"}
                </strong>

              </div>

              <div className="info-line">

                <span>Data source</span>

                <strong>
                  {bin.data_source}
                </strong>

              </div>

              <div className="info-line">

                <span>MQTT</span>

                <strong className="mqtt-connected">
                  <span></span>
                  Connected
                </strong>

              </div>

            </div>

          </div>

        </section>

        {/* ==========================================
            LAST TELEMETRY
        ========================================== */}

        <section className="last-update-card">

          <div className="last-update-left">

            <div className="update-icon">
              ↻
            </div>

            <div>

              <div className="last-update-label">
                LAST TELEMETRY UPDATE
              </div>

              <strong>
                {formatTime(bin.recorded_at)}
              </strong>

            </div>

          </div>

          <div className="system-online">
            <span></span>
            System online
          </div>

        </section>

        {/* ==========================================
            FOOTER
        ========================================== */}

        <footer className="bin-footer">

          <div>
            <span className="footer-green-dot"></span>
            Adama Smart City Operations
          </div>

          <div>
            Smart Waste Management System
          </div>

          <div>
            Auto-refresh: 3 seconds
          </div>

        </footer>

      </section>

    </main>
  );
}