import { Badge } from "@/components/ui/badge";
import { WEIGHT_COLOURS } from "@/data/constants";

export function WeightBadge({ weight }: { weight: string }) {
  const colours = WEIGHT_COLOURS[weight] ?? "bg-stone-100 text-stone-800";
  return <Badge className={colours}>{weight}</Badge>;
}
