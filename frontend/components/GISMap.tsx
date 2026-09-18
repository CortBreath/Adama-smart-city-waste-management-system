"use client";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import L from "leaflet";

type Bin = {
  bin_id: string;
  latitude: number;
  longitude: number;
  status: string;
  data_source: string;

  fill_level_pct: number | null;
  temperature: number | null;
  smoke_status: string | null;
  lid_status: string | null;
  system_status: string | null;
};

type GISMapProps = {
  bins: Bin[];
};


/* =========================================================
   STATUS
========================================================= */

function getStatus(bin: Bin) {
  const fill = bin.fill_level_pct;

  if (fill === null || fill === undefined) {
    return "unknown";
  }

  if (fill >= 90) {
    return "critical";
  }

  if (fill >= 60) {
    return "warning";
  }

  return "normal";
}

/* =========================================================
   COLORED BIN ICON
========================================================= */

function createBinIcon(status: string) {

  let background = "#16a34a";

  if (status === "warning") {
    background = "#eab308";
  }

  if (status === "critical") {
    background = "#dc2626";
  }

  return L.divIcon({
    className: "custom-bin-marker",

    html: `
      <div
        style="
          width: 34px;
          height: 34px;
          border-radius: 50%;
          background: ${background};
          border: 4px solid white;
          box-shadow: 0 3px 10px rgba(0,0,0,0.35);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 15px;
          font-weight: 800;
        "
      >
        ♻
      </div>
    `,

    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -20],
  });
}


/* =========================================================
   MAP
========================================================= */

export default function GISMap({ bins }: GISMapProps) {

  return (

    <MapContainer
      center={[8.54, 39.272]}
      zoom={15}
      style={{
        height: "100%",
        width: "100%",
      }}
    >

      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />


      {/* =================================================
          BIN MARKERS
      ================================================= */}

      {bins.map((bin) => {

        const status = getStatus(bin);

        const icon = createBinIcon(status);

        return (

          <Marker
            key={bin.bin_id}
            position={[
              bin.latitude,
              bin.longitude,
            ]}
            icon={icon}
          >

            <Popup>

              <div
                style={{
                  minWidth: "240px",
                  fontFamily: "Arial, sans-serif",
                }}
              >

                <h3
                  style={{
                    margin: "0 0 12px",
                    fontSize: "18px",
                  }}
                >
                  {bin.bin_id}
                </h3>


                {/* STATUS */}

                <div
                  style={{
                    display: "inline-block",
                    padding: "5px 10px",
                    borderRadius: "999px",
                    marginBottom: "12px",
                    background:
                      status === "normal"
                        ? "#dcfce7"
                        : status === "warning"
                        ? "#fef9c3"
                        : "#fee2e2",
                    color:
                      status === "normal"
                        ? "#166534"
                        : status === "warning"
                        ? "#854d0e"
                        : "#991b1b",
                    fontWeight: 700,
                    fontSize: "12px",
                  }}
                >
                  {status === "critical"
                   ? "CRITICAL / FULL"
                   : status === "warning"
                   ? "WARNING"
                   : status === "normal"
                   ? "NORMAL"
                   : "NO DATA"}
                </div>


                <p>
                  <strong>Fill:</strong>{" "}
                  {bin.fill_level_pct !== null
                    ? `${bin.fill_level_pct.toFixed(1)}%`
                    : "No data"}
                </p>


                <p>
                  <strong>Temperature:</strong>{" "}
                  {bin.temperature !== null
                    ? `${bin.temperature.toFixed(1)} °C`
                    : "No data"}
                </p>


                <p>
                  <strong>Smoke:</strong>{" "}
                  {bin.smoke_status ?? "No data"}
                </p>


                <p>
                  <strong>Lid:</strong>{" "}
                  {bin.lid_status ?? "No data"}
                </p>


                <p>
                  <strong>Source:</strong>{" "}
                  {bin.data_source}
                </p>


                <button
                  style={{
                    width: "100%",
                    marginTop: "8px",
                    padding: "9px 12px",
                    border: "none",
                    borderRadius: "8px",
                    background: "#0f766e",
                    color: "white",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    window.location.href =
                      `/bins/${bin.bin_id}`;
                  }}
                >
                  View Dashboard →
                </button>

              </div>

            </Popup>

          </Marker>

        );

      })}


      {/* =================================================
          MAP LEGEND
      ================================================= */}

      <div
        style={{
          position: "absolute",
          bottom: "20px",
          right: "20px",
          zIndex: 1000,
          background: "white",
          padding: "14px 16px",
          borderRadius: "12px",
          boxShadow: "0 3px 15px rgba(0,0,0,0.2)",
          fontSize: "13px",
          fontWeight: 600,
        }}
      >

        <div
          style={{
            fontWeight: 800,
            marginBottom: "9px",
          }}
        >
          Bin Status
        </div>


        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "7px",
          }}
        >
          <span
            style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: "#16a34a",
            }}
          />

          Normal
        </div>


        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "7px",
          }}
        >
          <span
            style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: "#eab308",
            }}
          />

          Warning
        </div>


        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span
            style={{
              width: "12px",
              height: "12px",
              borderRadius: "50%",
              background: "#dc2626",
            }}
          />

          Critical / Full
        </div>

      </div>

    </MapContainer>
  );
}