export const WEIGHT_COLOURS: Record<string, string> = {
  "Lace": "bg-violet-100 text-violet-800",
  "4 Ply": "bg-sky-100 text-sky-800",
  "DK": "bg-teal-100 text-teal-800",
  "Aran": "bg-amber-100 text-amber-800",
  "Worsted": "bg-orange-100 text-orange-800",
  "Chunky": "bg-rose-100 text-rose-800",
  "Super Chunky": "bg-fuchsia-100 text-fuchsia-800",
};

export const YARN_WEIGHTS = ["Lace", "4 Ply", "DK", "Aran", "Worsted", "Chunky", "Super Chunky"] as const;

export const SORT_OPTIONS = [
  { value: "name", label: "Name" },
  { value: "weight", label: "Weight" },
  { value: "colour", label: "Colour" },
  { value: "fibre", label: "Fibre" },
  { value: "estimated_total_metres", label: "Est. Metres" },
  { value: "created_at", label: "Date Added" },
  { value: "updated_at", label: "Last Updated" },
] as const;
