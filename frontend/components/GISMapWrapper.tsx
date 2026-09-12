"use client";

import dynamic from "next/dynamic";


const GISMap = dynamic(
  () => import("./GISMap"),
  {
    ssr: false,
    loading: () => (
      <div
        style={{
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        Loading map...
      </div>
    ),
  }
);


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


export default function GISMapWrapper({
  bins,
}: {
  bins: Bin[];
}) {

  return (
    <GISMap bins={bins} />
  );
}