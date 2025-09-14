import { useState, useEffect } from "react";

// Built-in components
const WinProb = ({ value }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h3 className="text-lg font-semibold mb-4 text-center">Win Probability</h3>
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-blue-400">Blue Team</span>
        <span className="text-xl font-bold text-blue-400">{Math.round(value.blue * 100)}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-3">
        <div 
          className="bg-blue-500 h-3 rounded-full transition-all duration-500"
          style={{ width: `${value.blue * 100}%` }}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-red-400">Red Team</span>
        <span className="text-xl font-bold text-red-400">{Math.round(value.red * 100)}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-3">
        <div 
          className="bg-red-500 h-3 rounded-full transition-all duration-500"
          style={{ width: `${value.red * 100}%` }}
        />
      </div>
    </div>
  </div>
);

const GoldDiffChart = ({ data }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h3 className="text-lg font-semibold mb-4">Gold Difference</h3>
    <div className="h-64 flex items-end space-x-2">
      {data.map((item, i) => {
        const height = Math.abs(item.diff) / 10;
        const isPositive = item.diff > 0;
        return (
          <div key={i} className="flex flex-col items-center flex-1">
            <div className="text-xs mb-1">{item.diff > 0 ? `+${item.diff}` : item.diff}</div>
            <div 
              className={`w-full ${isPositive ? 'bg-blue-500' : 'bg-red-500'} rounded-t`}
              style={{ height: `${Math.max(height, 10)}px` }}
            />
            <div className="text-xs mt-1">{item.minute}m</div>
          </div>
        );
      })}
    </div>
  </div>
);

const EventFeed = ({ events }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h3 className="text-lg font-semibold mb-4">Recent Events</h3>
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {events.slice(-8).reverse().map((event, i) => (
        <div key={i} className="flex justify-between items-center p-2 bg-gray-700 rounded">
          <span className="text-sm">{event.desc}</span>
          <span className="text-xs text-gray-400">{event.time}</span>
        </div>
      ))}
    </div>
  </div>
);

const PlayerCard = ({ player }) => (
  <div className={`bg-gray-800 p-4 rounded-lg border ${player.team === 'blue' ? 'border-blue-500' : 'border-red-500'}`}>
    <div className="text-center">
      <h4 className="font-semibold text-white">{player.name}</h4>
      <p className="text-sm text-gray-400">{player.champion}</p>
      <p className="text-xs text-gray-500 mb-2">{player.role}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span>K/D/A:</span>
          <span className="text-green-400">{player.kills}/{player.deaths}/{player.assists}</span>
        </div>
        <div className="flex justify-between">
          <span>Gold:</span>
          <span className="text-yellow-400">{player.gold.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span>CS:</span>
          <span className="text-purple-400">{player.cs}</span>
        </div>
      </div>
    </div>
  </div>
);

const ObjectivePanel = ({ objectives }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h3 className="text-lg font-semibold mb-4">Objectives</h3>
    <div className="space-y-3">
      <div className="flex justify-between">
        <span>Dragons</span>
        <span className="text-blue-400">{objectives.blueDragon}</span>
        <span className="text-red-400">{objectives.redDragon}</span>
      </div>
      <div className="flex justify-between">
        <span>Towers</span>
        <span className="text-blue-400">{objectives.blueTowers}</span>
        <span className="text-red-400">{objectives.redTowers}</span>
      </div>
      <div className="flex justify-between">
        <span>Barons</span>
        <span className="text-blue-400">{objectives.blueBaron}</span>
        <span className="text-red-400">{objectives.redBaron}</span>
      </div>
      <div className="flex justify-between">
        <span>Heralds</span>
        <span className="text-blue-400">{objectives.blueHerald}</span>
        <span className="text-red-400">{objectives.redHerald}</span>
      </div>
    </div>
  </div>
);

const MomentumChart = ({ data }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h3 className="text-lg font-semibold mb-4">Game Momentum</h3>
    <div className="h-32 flex items-end space-x-2">
      {data.map((item, i) => (
        <div key={i} className="flex flex-col items-center flex-1">
          <div className="text-xs mb-1">{Math.round((item.blueProbability || 0.5) * 100)}%</div>
          <div 
            className="w-full bg-gradient-to-t from-blue-500 to-purple-500 rounded-t"
            style={{ height: `${(item.blueProbability || 0.5) * 100}px` }}
          />
          <div className="text-xs mt-1">{item.time}m</div>
        </div>
      ))}
    </div>
  </div>
);

const KeyEventsImpact = ({ events, winProbHistory }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h3 className="text-lg font-semibold mb-4">AI Insights - Key Events Impact</h3>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <h4 className="font-medium mb-2 text-yellow-400">High Impact Events</h4>
        {events.filter(e => e.impact === 'high' || e.impact === 'critical').slice(-3).map((event, i) => (
          <div key={i} className="p-2 bg-gray-700 rounded mb-2">
            <div className="flex justify-between">
              <span className="text-sm">{event.desc}</span>
              <span className={`text-xs px-2 py-1 rounded ${
                event.impact === 'critical' ? 'bg-red-600' : 'bg-orange-600'
              }`}>{event.impact}</span>
            </div>
          </div>
        ))}
      </div>
      <div>
        <h4 className="font-medium mb-2 text-green-400">Win Probability Trend</h4>
        <div className="text-sm space-y-1">
          {winProbHistory.slice(-3).map((item, i) => (
            <div key={i} className="flex justify-between">
              <span>{Math.floor(item.time/60)}:{(item.time%60).toString().padStart(2, '0')}</span>
              <span className="text-blue-400">{Math.round(item.blue * 100)}%</span>
              <span className="text-xs text-gray-400">({Math.round((item.confidence || 0.8) * 100)}% conf.)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

const UpcomingMatches = ({ matches }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h3 className="text-lg font-semibold mb-4">Upcoming Matches</h3>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {matches.map((match, i) => (
        <div key={i} className="bg-gray-700 p-4 rounded-lg">
          <div className="text-center">
            <div className="font-semibold">{match.teamA} vs {match.teamB}</div>
            <div className="text-sm text-gray-400">{match.league}</div>
            <div className="text-xs text-gray-500 mt-1">
              {new Date(match.scheduledTime).toLocaleDateString()} - BO{match.bestOf}
            </div>
            {match.predictedWinner && (
              <div className="mt-2 text-xs">
                <span className="text-green-400">Predicted: </span>
                <span>{match.predictedWinner}</span>
                <span className="text-gray-400"> ({Math.round(match.winProbability * 100)}%)</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  </div>
);

const LiveMatch = ({ match, stats }) => {
  if (!match) return null;

  // Win probabilities - will be replaced by your trained model
  // For now using sample data that updates dynamically
  const teamAWinChance = match.winProbability?.teamA || match.prediction || 0.62;
  const teamBWinChance = match.winProbability?.teamB || (1 - (match.prediction || 0.62));

  return (
    <div className="w-full max-w-4xl shadow-2xl rounded-2xl bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700">
      {/* Match Info */}
      <div className="p-6 border-b border-gray-700">
        <h2 className="text-center text-2xl font-bold text-white tracking-wide">
          Live Match
        </h2>
      </div>

      <div className="p-6">
        {/* Teams and Score */}
        <div className="flex flex-col md:flex-row items-center justify-between mb-8">
          {/* Team A */}
          <div className="flex flex-col items-center mb-4 md:mb-0">
            <img
              src={match.teamA.logo}
              alt={match.teamA.name}
              className="w-20 h-20 rounded-full mb-2 border-2 border-blue-500 shadow-md"
            />
            <span className="font-semibold text-white">{match.teamA.name}</span>
            <span className="text-2xl font-bold text-blue-400">{match.teamA.score}</span>
            <span className="mt-1 text-sm text-green-400 font-semibold">
              {Math.round(teamAWinChance * 100)}% Win Chance
            </span>
          </div>

          {/* VS */}
          <div className="text-center mx-4">
            <span className="text-3xl font-bold text-gray-200">VS</span>
          </div>

          {/* Team B */}
          <div className="flex flex-col items-center">
            <img
              src={match.teamB.logo}
              alt={match.teamB.name}
              className="w-20 h-20 rounded-full mb-2 border-2 border-red-500 shadow-md"
            />
            <span className="font-semibold text-white">{match.teamB.name}</span>
            <span className="text-2xl font-bold text-red-400">{match.teamB.score}</span>
            <span className="mt-1 text-sm text-green-400 font-semibold">
              {Math.round(teamBWinChance * 100)}% Win Chance
            </span>
          </div>
        </div>

        {/* Statistics Section */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-center">
            {[
              { label: "Overall Win Rate", value: `${stats.winRate}%` },
              { label: "MVP", value: stats.mvp },
              { label: "Most Played Champion", value: stats.mostChamp },
              { label: "Top Team", value: stats.topTeam },
              { label: "Top Player", value: stats.topPlayer },
              { label: "Kills Participation", value: `${stats.killParticipation}%` },
            ].map((item, idx) => (
              <div
                key={idx}
                className="p-4 bg-gray-700 hover:bg-gray-600 transition-colors rounded-xl shadow-inner"
              >
                <p className="text-sm text-gray-300">{item.label}</p>
                <p className="text-lg font-bold text-white">{item.value}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default function App() {
  // Main state with ML-ready data structure
  const [state, setState] = useState({
    // Win probability data - will be fed by ML model
    win_prob: { blue: 0.6, red: 0.4 },
    
    // Game state data for ML model input
    gameState: {
      gameTime: 1450, // seconds
      blueTeam: {
        totalGold: 45200,
        totalKills: 12,
        totalDeaths: 8,
        towers: 5,
        dragons: 2,
        barons: 1,
        heralds: 1
      },
      redTeam: {
        totalGold: 41800,
        totalKills: 8,
        totalDeaths: 12,
        towers: 3,
        dragons: 1,
        barons: 0,
        heralds: 0
      }
    },

    // Historical data for charts
    gold_diff: [
      { minute: 5, diff: 200, blueGold: 12500, redGold: 12300 },
      { minute: 10, diff: -150, blueGold: 18400, redGold: 18550 },
      { minute: 15, diff: 300, blueGold: 26800, redGold: 26500 },
      { minute: 20, diff: 450, blueGold: 35200, redGold: 34750 },
      { minute: 25, diff: 200, blueGold: 45200, redGold: 45000 },
    ],

    events: [
      { time: "03:12", desc: "Blue First Blood - Top Lane", impact: "high", type: "kill" },
      { time: "04:20", desc: "Red Dragon (Infernal)", impact: "medium", type: "objective" },
      { time: "06:45", desc: "Blue Tower Destroyed - Mid", impact: "medium", type: "tower" },
      { time: "12:30", desc: "Blue Herald - Top Lane Push", impact: "high", type: "objective" },
      { time: "18:45", desc: "Red Baron Nashor", impact: "critical", type: "objective" },
      { time: "21:30", desc: "Blue Team Fight Victory - 4v2", impact: "high", type: "teamfight" },
      { time: "23:05", desc: "Red Tower Destroyed - Top", impact: "low", type: "tower" },
    ],

    players: [
      { name: "Player1", champion: "Ahri", role: "Mid", kills: 5, deaths: 2, assists: 7, gold: 12000, cs: 165, team: "blue" },
      { name: "Player2", champion: "Lee Sin", role: "Jungle", kills: 3, deaths: 1, assists: 10, gold: 11000, cs: 120, team: "blue" },
      { name: "Player3", champion: "Ezreal", role: "ADC", kills: 4, deaths: 3, assists: 5, gold: 11500, cs: 180, team: "blue" },
      { name: "Player4", champion: "Leona", role: "Support", kills: 0, deaths: 2, assists: 12, gold: 8000, cs: 45, team: "blue" },
      { name: "Player5", champion: "Darius", role: "Top", kills: 0, deaths: 0, assists: 3, gold: 2500, cs: 140, team: "blue" },
      { name: "Enemy1", champion: "Yasuo", role: "Mid", kills: 2, deaths: 4, assists: 4, gold: 9800, cs: 145, team: "red" },
      { name: "Enemy2", champion: "Graves", role: "Jungle", kills: 3, deaths: 2, assists: 3, gold: 10200, cs: 110, team: "red" },
      { name: "Enemy3", champion: "Jinx", role: "ADC", kills: 2, deaths: 3, assists: 4, gold: 10000, cs: 160, team: "red" },
      { name: "Enemy4", champion: "Thresh", role: "Support", kills: 1, deaths: 2, assists: 6, gold: 7500, cs: 35, team: "red" },
      { name: "Enemy5", champion: "Garen", role: "Top", kills: 0, deaths: 1, assists: 1, gold: 8500, cs: 125, team: "red" },
    ],

    objectives: {
      blueDragon: 2,
      redDragon: 1,
      blueTowers: 5,
      redTowers: 3,
      blueBaron: 1,
      redBaron: 0,
      blueHerald: 1,
      redHerald: 0,
    },

    momentumData: [
      { time: 5, blueKills: 1, redKills: 0, blueGoldDiff: 500, redGoldDiff: -500, blueProbability: 0.55 },
      { time: 10, blueKills: 2, redKills: 1, blueGoldDiff: 800, redGoldDiff: -800, blueProbability: 0.58 },
      { time: 15, blueKills: 2, redKills: 3, blueGoldDiff: -200, redGoldDiff: 200, blueProbability: 0.45 },
      { time: 20, blueKills: 4, redKills: 3, blueGoldDiff: 1200, redGoldDiff: -1200, blueProbability: 0.62 },
      { time: 25, blueKills: 7, redKills: 5, blueGoldDiff: 1800, redGoldDiff: -1800, blueProbability: 0.68 },
    ],

    // Live match data with ML model predictions
    liveMatch: {
      teamA: { 
        name: "Blue Warriors", 
        logo: "https://placehold.co/64x64/3B82F6/FFFFFF?text=BW",
        score: 8 
      },
      teamB: { 
        name: "Red Titans", 
        logo: "https://placehold.co/64x64/EF4444/FFFFFF?text=RT", 
        score: 6 
      },
      // Multiple prediction formats for flexibility
      prediction: 0.62, // Single value (Team A win probability)
      winProbability: {
        teamA: 0.62,
        teamB: 0.38,
        confidence: 0.85, // Model confidence
        lastUpdated: new Date().toISOString()
      },
      modelMetrics: {
        accuracy: 0.89,
        version: "v1.0.0",
        features: ["gold_diff", "kills", "objectives", "game_time", "team_composition"]
      }
    },

    stats: {
      winRate: 67,
      mvp: "Player1 (Ahri)",
      mostChamp: "Ahri",
      topTeam: "Blue Warriors",
      topPlayer: "Player1",
      killParticipation: 78,
      avgGameLength: "28:45",
      totalMatches: 156
    },
  });

  // Separate state for win probability history (for ML model tracking)
  const [winProbHistory, setWinProbHistory] = useState([
    { time: 0, blue: 0.5, red: 0.5, confidence: 0.7 },
    { time: 300, blue: 0.52, red: 0.48, confidence: 0.72 },
    { time: 600, blue: 0.55, red: 0.45, confidence: 0.75 },
    { time: 900, blue: 0.48, red: 0.52, confidence: 0.78 },
    { time: 1200, blue: 0.60, red: 0.40, confidence: 0.82 },
    { time: 1450, blue: 0.62, red: 0.38, confidence: 0.85 },
  ]);

  const [upcomingMatches, setUpcomingMatches] = useState([
    {
      id: 1,
      teamA: "Team Liquid",
      teamB: "Cloud9",
      league: "LCS",
      tournament: "Summer Playoffs",
      scheduledTime: "2025-09-15T20:00:00Z",
      bestOf: 5,
      predictedWinner: "Team Liquid",
      winProbability: 0.65
    },
    {
      id: 2,
      teamA: "T1",
      teamB: "Gen.G",
      league: "LCK",
      tournament: "Summer Finals",
      scheduledTime: "2025-09-16T10:00:00Z",
      bestOf: 5,
      predictedWinner: "T1",
      winProbability: 0.58
    },
    {
      id: 3,
      teamA: "G2 Esports",
      teamB: "Fnatic",
      league: "LEC",
      tournament: "Playoffs",
      scheduledTime: "2025-09-17T18:00:00Z",
      bestOf: 3,
      predictedWinner: "G2 Esports",
      winProbability: 0.72
    }
  ]);

  // ML Model Integration Hook (placeholder for your future implementation)
  const updatePredictions = (gameData) => {
    // TODO: Call your ML model API here
    // const predictions = await mlModel.predict(gameData);
    // setState(prev => ({
    //   ...prev,
    //   win_prob: predictions.win_prob,
    //   liveMatch: {
    //     ...prev.liveMatch,
    //     winProbability: predictions.winProbability
    //   }
    // }));
  };

  // Simulate real-time updates for demo purposes
  useEffect(() => {
    const interval = setInterval(() => {
      setState(prev => ({
        ...prev,
        liveMatch: {
          ...prev.liveMatch,
          winProbability: {
            ...prev.liveMatch.winProbability,
            teamA: Math.max(0.1, Math.min(0.9, prev.liveMatch.winProbability.teamA + (Math.random() - 0.5) * 0.05)),
            teamB: Math.max(0.1, Math.min(0.9, prev.liveMatch.winProbability.teamB + (Math.random() - 0.5) * 0.05)),
            confidence: Math.max(0.6, Math.min(0.95, prev.liveMatch.winProbability.confidence + (Math.random() - 0.5) * 0.02)),
            lastUpdated: new Date().toISOString()
          }
        }
      }));
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-screen min-h-screen p-0 m-0 bg-gray-900 text-white">
      <div className="w-full px-4 py-6">
        <h1 className="text-3xl font-bold mb-8 text-center">
          Esports Live Dashboard - ML Predictions Ready
        </h1>

        {/* Live Match on top - Now with ML predictions */}
        <div className="w-full mb-8 flex justify-center">
          <LiveMatch match={state.liveMatch} stats={state.stats} />
        </div>

        {/* Upcoming Matches with ML predictions */}
        <div className="w-full mb-12">
          <UpcomingMatches matches={upcomingMatches} />
        </div>

        {/* Top Row - Enhanced with ML data */}
        <div className="w-full mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 w-full">
            {/* Left side */}
            <div className="lg:col-span-3 w-full space-y-6">
              <GoldDiffChart data={state.gold_diff} />
              <MomentumChart data={state.momentumData} />
            </div>

            {/* Right side */}
            <div className="lg:col-span-1 space-y-6">
              <WinProb value={state.win_prob} />
              <ObjectivePanel objectives={state.objectives} />
              
              {/* ML Model Status Card */}
              <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <h3 className="text-sm font-semibold mb-2 text-green-400">ML Model Status</h3>
                <div className="space-y-1 text-xs">
                  <p>Version: {state.liveMatch.modelMetrics.version}</p>
                  <p>Accuracy: {(state.liveMatch.modelMetrics.accuracy * 100).toFixed(1)}%</p>
                  <p>Confidence: {(state.liveMatch.winProbability.confidence * 100).toFixed(1)}%</p>
                  <p className="text-gray-400">
                    Updated: {new Date(state.liveMatch.winProbability.lastUpdated).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI Insights - Enhanced for ML */}
        <div className="w-full mb-8">
          <KeyEventsImpact
            events={state.events}
            winProbHistory={winProbHistory}
          />
        </div>

        {/* Event Feed */}
        <div className="w-full mb-8">
          <EventFeed events={state.events} />
        </div>

        {/* Player Cards - Enhanced with team separation */}
        <div className="w-full">
          <h2 className="text-xl font-semibold mb-4">Team Rosters</h2>
          
          {/* Blue Team */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3 text-blue-400">Blue Team</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 w-full">
              {state.players.filter(p => p.team === 'blue').map((p, i) => (
                <PlayerCard key={i} player={p} />
              ))}
            </div>
          </div>

          {/* Red Team */}
          <div>
            <h3 className="text-lg font-medium mb-3 text-red-400">Red Team</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 w-full">
              {state.players.filter(p => p.team === 'red').map((p, i) => (
                <PlayerCard key={i} player={p} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}