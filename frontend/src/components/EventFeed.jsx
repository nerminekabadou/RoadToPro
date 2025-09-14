import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Flame, Castle, Skull, Swords } from "lucide-react";

function getIcon(desc) {
  if (desc.toLowerCase().includes("kill")) return <Swords size={16} className="text-red-400" />;
  if (desc.toLowerCase().includes("dragon")) return <Flame size={16} className="text-orange-400" />;
  if (desc.toLowerCase().includes("baron")) return <Skull size={16} className="text-purple-400" />;
  if (desc.toLowerCase().includes("tower")) return <Castle size={16} className="text-yellow-400" />;
  return null;
}

function getTeamColor(desc) {
  if (desc.toLowerCase().includes("blue")) return "text-blue-400";
  if (desc.toLowerCase().includes("red")) return "text-red-400";
  return "text-gray-300";
}

export default function EventFeed({ events = [] }) {
  const last = events.slice(-50).reverse();

  return (
    <Card className="bg-gray-900 text-white max-h-96 overflow-auto">
      <CardHeader>
        <CardTitle>Event Feed</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {last.map((e, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              <span className="text-gray-400 w-12">{e.time ?? "?"}</span>
              {getIcon(e.desc)}
              <span className={getTeamColor(e.desc)}>{e.desc}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
