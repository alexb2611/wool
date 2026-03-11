import { useState } from "react";
import { toast } from "sonner";
import { LoaderCircleIcon } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { YARN_WEIGHTS } from "@/data/constants";
import { useScrapeYarn } from "@/hooks/use-yarns";
import type { Yarn, YarnCreate, YarnUpdate, YarnWeight, ScrapedColourway } from "@/types";

interface YarnFormProps {
  initialData?: Yarn;
  onSubmit: (data: YarnCreate | YarnUpdate) => void;
  isSubmitting?: boolean;
  existingNames: string[];
  existingFibres: string[];
}

export function YarnForm({
  initialData,
  onSubmit,
  isSubmitting,
  existingNames,
  existingFibres,
}: YarnFormProps) {
  const [scrapeUrl, setScrapeUrl] = useState("");
  const [colourways, setColourways] = useState<ScrapedColourway[]>([]);

  const [name, setName] = useState(initialData?.name ?? "");
  const [weight, setWeight] = useState<YarnWeight>(initialData?.weight ?? "DK");
  const [colour, setColour] = useState(initialData?.colour ?? "");
  const [fibre, setFibre] = useState(initialData?.fibre ?? "");
  const [metresPerBall, setMetresPerBall] = useState<string>(
    initialData?.metres_per_ball != null ? String(initialData.metres_per_ball) : ""
  );
  const [fullBalls, setFullBalls] = useState<string>(String(initialData?.full_balls ?? 0));
  const [partBalls, setPartBalls] = useState<string>(String(initialData?.part_balls ?? 0));
  const [extraMetres, setExtraMetres] = useState<string>(
    initialData?.extra_metres != null ? String(initialData.extra_metres) : ""
  );
  const [needleSizeMm, setNeedleSizeMm] = useState<string>(
    initialData?.needle_size_mm != null ? String(initialData.needle_size_mm) : ""
  );
  const [tension, setTension] = useState(initialData?.tension ?? "");
  const [ballWeightGrams, setBallWeightGrams] = useState<string>(
    initialData?.ball_weight_grams != null ? String(initialData.ball_weight_grams) : ""
  );
  const [imageUrl, setImageUrl] = useState(initialData?.image_url ?? "");
  const [intendedProject, setIntendedProject] = useState(initialData?.intended_project ?? "");
  const [notes, setNotes] = useState(initialData?.notes ?? "");
  const [ravelryUrl, setRavelryUrl] = useState(initialData?.ravelry_url ?? "");

  const scrape = useScrapeYarn();

  function handleFetch() {
    if (!scrapeUrl.trim()) return;
    scrape.mutate(scrapeUrl.trim(), {
      onSuccess: (data) => {
        if (data.name) setName(data.name);
        if (data.weight && YARN_WEIGHTS.includes(data.weight as YarnWeight)) {
          setWeight(data.weight as YarnWeight);
        }
        if (data.fibre) setFibre(data.fibre);
        if (data.metres_per_ball != null) setMetresPerBall(String(data.metres_per_ball));
        if (data.ball_weight_grams != null) setBallWeightGrams(String(data.ball_weight_grams));
        if (data.needle_size_mm != null) setNeedleSizeMm(String(data.needle_size_mm));
        if (data.tension) setTension(data.tension);
        if (data.image_url) setImageUrl(data.image_url);
        if (data.colourways.length > 0) {
          setColourways(data.colourways);
        }
        toast.success("Product data fetched");
      },
      onError: (err) => {
        toast.error(`Failed to fetch: ${err.message}`);
      },
    });
  }

  function handleColourwayChange(colourwayName: string | null) {
    if (!colourwayName) return;
    const cw = colourways.find((c) => c.name === colourwayName);
    if (cw) {
      setColour(cw.name);
      if (cw.image_url) setImageUrl(cw.image_url);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const data: YarnCreate = {
      name: name.trim(),
      weight,
      colour: colour.trim(),
      fibre: fibre.trim(),
      metres_per_ball: metresPerBall !== "" ? Number(metresPerBall) : null,
      full_balls: Number(fullBalls) || 0,
      part_balls: Number(partBalls) || 0,
      extra_metres: extraMetres !== "" ? Number(extraMetres) : null,
      needle_size_mm: needleSizeMm !== "" ? Number(needleSizeMm) : null,
      tension: tension.trim() || null,
      ball_weight_grams: ballWeightGrams !== "" ? Number(ballWeightGrams) : null,
      image_url: imageUrl.trim() || null,
      intended_project: intendedProject.trim() || null,
      notes: notes.trim() || null,
      ravelry_url: ravelryUrl.trim() || null,
    };
    onSubmit(data);
  }

  const namesListId = "yarn-names-list";
  const fibresListId = "yarn-fibres-list";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {/* URL Import Section */}
      <div className="rounded-lg border border-dashed border-stone-300 bg-stone-50 p-3">
        <Label htmlFor="scrape-url" className="text-sm font-medium">
          Import from URL
        </Label>
        <div className="mt-1.5 flex gap-2">
          <Input
            id="scrape-url"
            type="url"
            value={scrapeUrl}
            onChange={(e) => setScrapeUrl(e.target.value)}
            placeholder="Paste a link from Wool Warehouse or LoveCrafts..."
            className="flex-1"
          />
          <Button
            type="button"
            variant="secondary"
            onClick={handleFetch}
            disabled={scrape.isPending || !scrapeUrl.trim()}
          >
            {scrape.isPending ? (
              <LoaderCircleIcon className="size-4 animate-spin" />
            ) : (
              "Fetch"
            )}
          </Button>
        </div>
        <p className="mt-1 text-xs text-stone-500">
          Supported: woolwarehouse.co.uk, lovecrafts.com
        </p>

        {/* Image preview + colourway selector */}
        {(imageUrl || colourways.length > 0) && (
          <div className="mt-3 flex items-start gap-3">
            {imageUrl && (
              <img
                src={imageUrl}
                alt="Product"
                className="size-20 rounded border border-stone-200 object-cover"
              />
            )}
            {colourways.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="colourway-select" className="text-sm">
                  Colourway
                </Label>
                <Select onValueChange={handleColourwayChange}>
                  <SelectTrigger id="colourway-select" className="w-56">
                    <SelectValue placeholder="Select a colourway..." />
                  </SelectTrigger>
                  <SelectContent>
                    {colourways.map((cw) => (
                      <SelectItem key={cw.name} value={cw.name}>
                        {cw.shade_number ? `${cw.shade_number} ${cw.name}` : cw.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        )}
      </div>

      <datalist id={namesListId}>
        {existingNames.map((n) => (
          <option key={n} value={n} />
        ))}
      </datalist>
      <datalist id={fibresListId}>
        {existingFibres.map((f) => (
          <option key={f} value={f} />
        ))}
      </datalist>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-name">Name</Label>
          <Input
            id="yarn-name"
            type="text"
            required
            list={namesListId}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Drops Baby Merino"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-weight">Weight</Label>
          <Select
            value={weight}
            onValueChange={(v) => setWeight((v ?? "DK") as YarnWeight)}
          >
            <SelectTrigger id="yarn-weight" className="w-full">
              <SelectValue placeholder="Select weight" />
            </SelectTrigger>
            <SelectContent>
              {YARN_WEIGHTS.map((w) => (
                <SelectItem key={w} value={w}>
                  {w}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-colour">Colour</Label>
          <Input
            id="yarn-colour"
            type="text"
            required
            value={colour}
            onChange={(e) => setColour(e.target.value)}
            placeholder="e.g. Dusty Rose"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-fibre">Fibre</Label>
          <Input
            id="yarn-fibre"
            type="text"
            required
            list={fibresListId}
            value={fibre}
            onChange={(e) => setFibre(e.target.value)}
            placeholder="e.g. 100% Merino"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-metres-per-ball">Metres per ball</Label>
          <Input
            id="yarn-metres-per-ball"
            type="number"
            min={0}
            value={metresPerBall}
            onChange={(e) => setMetresPerBall(e.target.value)}
            placeholder="e.g. 125"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-ball-weight">Ball weight (g)</Label>
          <Input
            id="yarn-ball-weight"
            type="number"
            min={0}
            value={ballWeightGrams}
            onChange={(e) => setBallWeightGrams(e.target.value)}
            placeholder="e.g. 50"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-needle-size">Needle size (mm)</Label>
          <Input
            id="yarn-needle-size"
            type="number"
            min={0}
            step={0.5}
            value={needleSizeMm}
            onChange={(e) => setNeedleSizeMm(e.target.value)}
            placeholder="e.g. 4.0"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-tension">Tension</Label>
          <Input
            id="yarn-tension"
            type="text"
            value={tension}
            onChange={(e) => setTension(e.target.value)}
            placeholder="e.g. 22 sts × 30 rows / 10cm"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-full-balls">Full balls</Label>
          <Input
            id="yarn-full-balls"
            type="number"
            min={0}
            value={fullBalls}
            onChange={(e) => setFullBalls(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-part-balls">Part balls</Label>
          <Input
            id="yarn-part-balls"
            type="number"
            min={0}
            value={partBalls}
            onChange={(e) => setPartBalls(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-extra-metres">Extra metres</Label>
          <Input
            id="yarn-extra-metres"
            type="number"
            min={0}
            value={extraMetres}
            onChange={(e) => setExtraMetres(e.target.value)}
            placeholder="e.g. 30"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="yarn-image-url">Image URL</Label>
          <Input
            id="yarn-image-url"
            type="url"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://..."
          />
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="yarn-project">Intended project</Label>
          <Input
            id="yarn-project"
            type="text"
            value={intendedProject}
            onChange={(e) => setIntendedProject(e.target.value)}
            placeholder="e.g. Helen's cardigan"
          />
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="yarn-ravelry-url">Ravelry pattern URL</Label>
          <Input
            id="yarn-ravelry-url"
            type="url"
            value={ravelryUrl}
            onChange={(e) => setRavelryUrl(e.target.value)}
            placeholder="https://www.ravelry.com/patterns/library/..."
          />
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="yarn-notes">Notes</Label>
          <Textarea
            id="yarn-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any additional notes..."
            rows={3}
          />
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : initialData ? "Save changes" : "Add yarn"}
        </Button>
      </div>
    </form>
  );
}
