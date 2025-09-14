import { useState, useEffect } from "react";
import WinProb from "./components/WinProb";
import GoldDiffChart from "./components/GoldDiffChart";
import EventFeed from "./components/EventFeed";
import PlayerCard from "./components/PlayerCard";
import ObjectivePanel from "./components/ObjectivePanel";
import MomentumChart from "./components/MomentumChart";
import KeyEventsImpact from "./components/KeyEventsImpact";
import UpcomingMatches from "./components/UpcomingMatches";

export default function App() {
  // Main state
  const [state, setState] = useState({
    win_prob: { blue: 0.6, red: 0.4 },
    gold_diff: [
      { minute: 5, diff: 200 },
      { minute: 10, diff: -150 },
      { minute: 15, diff: 300 },
      { minute: 20, diff: 450 },
      { minute: 25, diff: 200 },
      { minute: 30, diff: 600 },
    ],
    events: [
      { time: "03:12", desc: "Blue Kill Top" },
      { time: "04:20", desc: "Red Dragon" },
      { time: "06:45", desc: "Blue Tower Mid" },
      { time: "21:30", desc: "Red Baron" },
      { time: "22:10", desc: "Blue Kill Bot" },
      { time: "23:05", desc: "Red Tower Top" },
    ],
    players: [
      { name: "Player1", champion: "Ahri", kills: 5, deaths: 2, assists: 7, gold: 12000 },
      { name: "Player2", champion: "Lee Sin", kills: 3, deaths: 1, assists: 10, gold: 11000 },
      { name: "Player3", champion: "Ezreal", kills: 2, deaths: 3, assists: 5, gold: 9500 },
      { name: "Player4", champion: "Leona", kills: 1, deaths: 4, assists: 12, gold: 8000 },
      { name: "Player5", champion: "Darius", kills: 6, deaths: 2, assists: 3, gold: 13000 },
    ],
    objectives: {
      blueDragon: 2,
      redDragon: 1,
      blueTowers: 5,
      redTowers: 3,
      blueBaron: 1,
      redBaron: 0,
    },
    momentumData: [
      { time: 1, blueKills: 1, redKills: 0, blueGoldDiff: 500, redGoldDiff: -500 },
      { time: 2, blueKills: 2, redKills: 1, blueGoldDiff: 800, redGoldDiff: -800 },
      { time: 3, blueKills: 2, redKills: 3, blueGoldDiff: -200, redGoldDiff: 200 },
      { time: 4, blueKills: 4, redKills: 3, blueGoldDiff: 1200, redGoldDiff: -1200 },
    ],
  });

  // Separate state for win probability history
  const [winProbHistory, setWinProbHistory] = useState([
    { time: 0, blue: 0.5, red: 0.5 },
    { time: 5, blue: 0.55, red: 0.45 },
    { time: 10, blue: 0.52, red: 0.48 },
    { time: 15, blue: 0.60, red: 0.40 },
    { time: 20, blue: 0.62, red: 0.38 },
  ]);

  const [upcomingMatches, setUpcomingMatches] = useState([
    {
      type: "lol.schedule.upsert",
      at: "2025-09-13T16:41:25.848682+00:00",
      key: "match:1229897",
      payload: {
        id: 1229897,
        slug: "2025-09-14-2dc42d59-0241-4949-8a0e-8ec0a97f9bd5",
        name: "Lower bracket quarterfinal 1: 100 vs PNG",
        status: "not_started",
        league: "LTA",
        tournament: "Playoffs",
        best_of: 5,
        begin_at: "2025-09-13T20:00:00Z",
        scheduled_at: "2025-09-13T20:00:00Z",
        opponent1: "100 Thieves",
        opponent2: "paiN Gaming",
        serie_id: 9610,
        tournament_id: 17436,
        live: false,
      },
      source: "pandascore",
      version: "1.0",
    },
  // Add the other two matches here for testing...
]);

  useEffect(() => {
    const wsUrl = "ws://localhost:8000/ws";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log("WS connected");
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        setState((prev) => ({
          ...prev,
          win_prob: msg.win_prob ?? prev.win_prob,
          gold_diff: msg.gold_diff ? msg.gold_diff : prev.gold_diff,
          events: msg.events ? [...prev.events, ...msg.events] : prev.events,
          momentumData: msg.momentumData ? msg.momentumData : prev.momentumData,
        }));

        // Optionally update winProbHistory dynamically if provided by WS
        if (msg.winProbHistory) {
          setWinProbHistory(msg.winProbHistory);
        }
      } catch (e) {
        console.error(e);
      }
    };

    ws.onclose = () => console.log("WS closed");
    ws.onerror = (e) => console.error("WS error", e);

    return () => ws.close();
  }, []);

  return (
    <div className="w-screen min-h-screen p-0 m-0 bg-gray-900 text-white">
      <div className="w-full px-4 py-6">
        <h1 className="text-3xl font-bold mb-8 text-center">Esports Live Dashboard (MVP)</h1>

        {/* Top Row */}
        <div className="w-full mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 w-full">
            {/* Main chart area */}
            <div className="lg:col-span-3 w-full space-y-6">
              <GoldDiffChart data={state.gold_diff} />
              <MomentumChart data={state.momentumData} />
            </div>

            {/* Right sidebar */}
            <div className="lg:col-span-1 space-y-6">
              <WinProb value={state.win_prob} />
              <ObjectivePanel objectives={state.objectives} />
              <UpcomingMatches matches={upcomingMatches} />
            </div>
          </div>
        </div>

        {/* AI Insights - Key Events Impact */}
        <div className="w-full mb-8">
          <KeyEventsImpact events={state.events} winProbHistory={winProbHistory} />
        </div>

        {/* Event Feed */}
        <div className="w-full mb-8">
          <EventFeed events={state.events} />
        </div>

        {/* Player Cards */}
        <div className="w-full">
          <h2 className="text-xl font-semibold mb-4">Team Roster</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 w-full">
            {state.players.map((p, i) => (
              <PlayerCard key={i} player={p} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}