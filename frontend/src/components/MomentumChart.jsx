import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area } from "recharts";

export default function MomentumChart({ data }) {
  // Compute momentum combining kills + gold diff
  const processedData = data.map((point) => ({
    time: point.time,
    blueMomentum: point.blueKills * 100 + point.blueGoldDiff / 10,
    redMomentum: point.redKills * 100 + point.redGoldDiff / 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={processedData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" label={{ value: "Time (min)", position: "insideBottomRight", offset: 0 }} />
        <YAxis label={{ value: "Momentum", angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Legend verticalAlign="top" />
        <Line type="monotone" dataKey="blueMomentum" stroke="#1f77b4" strokeWidth={2} />
        <Line type="monotone" dataKey="redMomentum" stroke="#d62728" strokeWidth={2} />
        <Area type="monotone" dataKey="blueMomentum" stroke="#1f77b4" fill="#1f77b4" fillOpacity={0.1} />
        <Area type="monotone" dataKey="redMomentum" stroke="#d62728" fill="#d62728" fillOpacity={0.1} />
      </LineChart>
    </ResponsiveContainer>
  );
}
