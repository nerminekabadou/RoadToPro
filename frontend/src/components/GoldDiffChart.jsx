import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function GoldDiffChart({ data = [] }) {
  return (
    <div className="p-4 bg-gray-800 rounded">
      <h2 className="text-lg mb-2">Gold difference (minutes)</h2>
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="minute" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="diff" stroke="#60a5fa" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
