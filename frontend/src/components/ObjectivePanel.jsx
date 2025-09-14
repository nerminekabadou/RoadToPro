import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function ObjectivePanel({ objectives }) {
  return (
    <Card className="bg-gray-900 text-white w-64">
      <CardHeader>
        <CardTitle className="text-sm">Objective Control</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Dragon</span>
          <span>{objectives.blueDragon} - {objectives.redDragon}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>Towers</span>
          <span>{objectives.blueTowers} - {objectives.redTowers}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>Baron</span>
          <span>{objectives.blueBaron} - {objectives.redBaron}</span>
        </div>
      </CardContent>
    </Card>
  );
}
