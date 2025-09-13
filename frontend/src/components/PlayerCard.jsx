import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function PlayerCard({ player }) {
  return (
    <Card className="bg-gray-800 text-white w-48">
      <CardHeader>
        <CardTitle className="text-sm">{player.name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Champion:</span>
          <span>{player.champion}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>K/D/A:</span>
          <span>{player.kills}/{player.deaths}/{player.assists}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>Gold:</span>
          <span>{player.gold}</span>
        </div>
      </CardContent>
    </Card>
  );
}