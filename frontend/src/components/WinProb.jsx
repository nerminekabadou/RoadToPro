import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function WinProb({ value }) {
  const blue = Math.round((value?.blue ?? 0.5) * 100);
  const red = 100 - blue;

  const data = [
    { name: "Blue", value: blue },
    { name: "Red", value: red }
  ];
  const COLORS = ["#3b82f6", "#ef4444"]; // Tailwind blue-500, red-500

  return (
    <Card className="bg-gray-900 text-white">
      <CardHeader>
        <CardTitle>Win Probability</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div style={{ width: "100%", height: 220 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex justify-between w-full px-4">
          <span className="text-blue-400">Blue {blue}%</span>
          <span className="text-red-400">Red {red}%</span>
        </div>
      </CardContent>
    </Card>
  );
}
