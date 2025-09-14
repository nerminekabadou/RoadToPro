import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";

export default function LiveMatch({ match, stats }) {
  if (!match) return null;

  // Win probabilities - will be replaced by your trained model
  // For now using sample data that updates dynamically
  const teamAWinChance = match.winProbability?.teamA || match.prediction || 0.62;
  const teamBWinChance = match.winProbability?.teamB || (1 - (match.prediction || 0.62));

  return (
    <Card className="w-full max-w-4xl shadow-2xl rounded-2xl bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700">
      {/* Match Info */}
      <CardHeader>
        <CardTitle className="text-center text-2xl font-bold text-white tracking-wide">
          Live Match
        </CardTitle>
      </CardHeader>

      <CardContent>
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
      </CardContent>
    </Card>
  );
}