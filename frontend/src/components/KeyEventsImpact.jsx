import React from "react";

export default function KeyEventsImpact({ events, winProbHistory }) {
  // Calculate impact for each event
  const impacts = events.map((evt, i) => {
    if (!winProbHistory[i + 1]) return { ...evt, delta: 0 };
    const deltaBlue = winProbHistory[i + 1].blue - winProbHistory[i].blue;
    return { ...evt, delta: Math.round(deltaBlue * 100) }; // convert to percentage
  });

  return (
    <div className="bg-gray-800 p-4 rounded space-y-2">
      <h3 className="text-lg font-semibold mb-2">Key Events Impact</h3>
      {impacts.map((e, i) => (
        <div key={i} className="flex justify-between">
          <span>{e.time} - {e.desc}</span>
          <span className={`font-bold ${e.delta >= 0 ? "text-green-400" : "text-red-400"}`}>
            {e.delta >= 0 ? `+${e.delta}%` : `${e.delta}%`}
          </span>
        </div>
      ))}
    </div>
  );
}
