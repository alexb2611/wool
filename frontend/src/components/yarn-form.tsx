import { useState } from "react";
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
import type { Yarn, YarnCreate, YarnUpdate, YarnWeight } from "@/types";

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
  const [intendedProject, setIntendedProject] = useState(initialData?.intended_project ?? "");
  const [notes, setNotes] = useState(initialData?.notes ?? "");

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
      intended_project: intendedProject.trim() || null,
      notes: notes.trim() || null,
    };
    onSubmit(data);
  }

  const namesListId = "yarn-names-list";
  const fibresListId = "yarn-fibres-list";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
