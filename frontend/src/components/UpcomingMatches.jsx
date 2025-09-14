import React from "react";

export default function UpcomingMatches({ matches }) {
  if (!matches || matches.length === 0) {
    return <div className="text-center text-gray-400">No upcoming matches</div>;
  }

  return (
    <div className="bg-gray-800 p-4 rounded space-y-4">
      <h3 className="text-lg font-semibold mb-2">Upcoming Matches</h3>
      {matches.map((m) => (
        <div key={m.payload.id} className="flex justify-between items-center p-2 bg-gray-900 rounded hover:bg-gray-700 transition">
          <div>
            <div className="font-semibold">{m.payload.name}</div>
            <div className="text-sm text-gray-400">
              {m.payload.league} • {m.payload.tournament} • Best of {m.payload.best_of}
            </div>
          </div>
          <div className="text-sm text-gray-300">
            {new Date(m.payload.begin_at).toLocaleString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
              day: "numeric",
              month: "short",
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
