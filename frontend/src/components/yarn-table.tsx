import { useState } from "react";
import { ChevronDownIcon, ChevronRightIcon, PencilIcon, Trash2Icon } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { WeightBadge } from "@/components/weight-badge";
import type { Yarn } from "@/types";

function formatQuantity(yarn: Yarn): string {
  const parts: string[] = [];
  if (yarn.full_balls > 0) parts.push(`${yarn.full_balls} ball${yarn.full_balls !== 1 ? "s" : ""}`);
  if (yarn.part_balls > 0) parts.push(`${yarn.part_balls} part`);
  if (yarn.extra_metres) parts.push(`${yarn.extra_metres}m extra`);
  return parts.join(" + ") || "None";
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

interface YarnTableProps {
  yarns: Yarn[];
  onEdit: (yarn: Yarn) => void;
  onDelete: (yarn: Yarn) => void;
}

export function YarnTable({ yarns, onEdit, onDelete }: YarnTableProps) {
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  function toggleRow(id: number) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-8" />
          <TableHead>Name</TableHead>
          <TableHead>Weight</TableHead>
          <TableHead>Colour</TableHead>
          <TableHead className="hidden md:table-cell">Fibre</TableHead>
          <TableHead>Quantity</TableHead>
          <TableHead>Est. Metres</TableHead>
          <TableHead className="hidden md:table-cell">Project</TableHead>
          <TableHead className="hidden lg:table-cell">Pattern</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {yarns.map((yarn) => {
          const isExpanded = expandedIds.has(yarn.id);
          return (
            <>
              <TableRow
                key={yarn.id}
                className="cursor-pointer"
                onClick={() => toggleRow(yarn.id)}
              >
                <TableCell className="w-8 text-stone-400">
                  {isExpanded ? (
                    <ChevronDownIcon className="size-4" />
                  ) : (
                    <ChevronRightIcon className="size-4" />
                  )}
                </TableCell>
                <TableCell className="font-medium">{yarn.name}</TableCell>
                <TableCell>
                  <WeightBadge weight={yarn.weight} />
                </TableCell>
                <TableCell>{yarn.colour}</TableCell>
                <TableCell className="hidden md:table-cell">{yarn.fibre}</TableCell>
                <TableCell>{formatQuantity(yarn)}</TableCell>
                <TableCell>
                  {yarn.estimated_total_metres != null
                    ? `${yarn.estimated_total_metres.toLocaleString()}m`
                    : "—"}
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  {yarn.intended_project ?? "—"}
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  {yarn.pattern_name && yarn.ravelry_url ? (
                    <a
                      href={yarn.ravelry_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {yarn.pattern_name}
                    </a>
                  ) : (
                    "—"
                  )}
                </TableCell>
              </TableRow>
              {isExpanded && (
                <TableRow key={`${yarn.id}-expanded`} className="bg-stone-50 hover:bg-stone-50">
                  <TableCell />
                  <TableCell colSpan={8}>
                    <div className="py-2 flex flex-col gap-2 text-sm text-stone-700">
                      <div className="flex items-start gap-4">
                        {yarn.image_url && (
                          <img
                            src={yarn.image_url}
                            alt={yarn.name}
                            className="size-20 rounded border border-stone-200 object-cover flex-shrink-0"
                          />
                        )}
                        <div className="grid grid-cols-2 gap-x-8 gap-y-1 sm:grid-cols-4 flex-1">
                          <div>
                            <span className="text-stone-500">Metres per ball: </span>
                            {yarn.metres_per_ball != null ? `${yarn.metres_per_ball}m` : "—"}
                          </div>
                          {yarn.ball_weight_grams != null && (
                            <div>
                              <span className="text-stone-500">Ball weight: </span>
                              {yarn.ball_weight_grams}g
                            </div>
                          )}
                          {yarn.needle_size_mm != null && (
                            <div>
                              <span className="text-stone-500">Needle size: </span>
                              {yarn.needle_size_mm}mm
                            </div>
                          )}
                          {yarn.tension && (
                            <div>
                              <span className="text-stone-500">Tension: </span>
                              {yarn.tension}
                            </div>
                          )}
                          <div>
                            <span className="text-stone-500">Extra metres: </span>
                            {yarn.extra_metres != null ? `${yarn.extra_metres}m` : "—"}
                          </div>
                          <div>
                            <span className="text-stone-500">Added: </span>
                            {formatDate(yarn.created_at)}
                          </div>
                          <div>
                            <span className="text-stone-500">Updated: </span>
                            {formatDate(yarn.updated_at)}
                          </div>
                        </div>
                      </div>
                      {yarn.notes && (
                        <div>
                          <span className="text-stone-500">Notes: </span>
                          {yarn.notes}
                        </div>
                      )}
                      <div className="flex gap-2 mt-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onEdit(yarn);
                          }}
                        >
                          <PencilIcon className="size-3.5 mr-1" />
                          Edit
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDelete(yarn);
                          }}
                        >
                          <Trash2Icon className="size-3.5 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </>
          );
        })}
      </TableBody>
    </Table>
  );
}
