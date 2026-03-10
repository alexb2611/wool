import { useYarnStats } from "@/hooks/use-yarns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { WeightBadge } from "@/components/weight-badge";

export function Dashboard() {
  const { data: stats, isLoading } = useYarnStats();

  if (isLoading || !stats) return null;

  const topFibres = Object.entries(stats.by_fibre)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  const weightEntries = Object.entries(stats.by_weight).filter(([, count]) => count > 0);

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4 mb-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-stone-500 text-sm font-normal">Total Yarns</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-teal-800">{stats.total_yarns}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-stone-500 text-sm font-normal">Est. Total Metres</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-teal-800">
            {stats.total_estimated_metres.toLocaleString()}m
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-stone-500 text-sm font-normal">By Weight</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-1.5">
            {weightEntries.length === 0 ? (
              <span className="text-stone-400 text-xs">None</span>
            ) : (
              weightEntries.map(([weight, count]) => (
                <div key={weight} className="flex items-center justify-between gap-2">
                  <WeightBadge weight={weight} />
                  <span className="text-teal-800 font-semibold text-sm">{count}</span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-stone-500 text-sm font-normal">Top Fibres</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-1">
            {topFibres.length === 0 ? (
              <span className="text-stone-400 text-xs">None</span>
            ) : (
              topFibres.map(([fibre, count]) => (
                <div key={fibre} className="flex items-center justify-between gap-2">
                  <span className="text-stone-700 text-sm truncate">{fibre}</span>
                  <span className="text-teal-800 font-semibold text-sm shrink-0">{count}</span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
