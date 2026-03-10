import { useState } from "react";
import { toast } from "sonner";
import { PlusIcon, SproutIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dashboard } from "@/components/dashboard";
import { SearchFilters, type FilterState } from "@/components/search-filters";
import { YarnTable } from "@/components/yarn-table";
import { YarnDialog } from "@/components/yarn-dialog";
import { DeleteDialog } from "@/components/delete-dialog";
import { useYarnList, useSeedYarns } from "@/hooks/use-yarns";
import type { Yarn, YarnWeight, YarnListParams } from "@/types";

const DEFAULT_FILTERS: FilterState = {
  search: "",
  weight: "",
  fibre: "",
  hasProject: "all",
  sortBy: "name",
  sortDir: "asc",
};

export function YarnsPage() {
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editYarn, setEditYarn] = useState<Yarn | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteYarn, setDeleteYarn] = useState<Yarn | null>(null);

  const queryParams: YarnListParams = {
    ...(filters.search ? { q: filters.search } : {}),
    ...(filters.weight ? { weight: filters.weight as YarnWeight } : {}),
    ...(filters.fibre ? { fibre: filters.fibre } : {}),
    ...(filters.hasProject !== "all"
      ? { has_project: filters.hasProject === "with" }
      : {}),
    sort_by: filters.sortBy,
    sort_dir: filters.sortDir,
  };

  const { data: yarns, isLoading } = useYarnList(queryParams);
  const seedMutation = useSeedYarns();

  const existingNames = yarns
    ? [...new Set(yarns.map((y) => y.name))].sort()
    : [];
  const existingFibres = yarns
    ? [...new Set(yarns.map((y) => y.fibre))].sort()
    : [];

  function handleEdit(yarn: Yarn) {
    setEditYarn(yarn);
    setEditDialogOpen(true);
  }

  function handleDelete(yarn: Yarn) {
    setDeleteYarn(yarn);
    setDeleteDialogOpen(true);
  }

  function handleSeed() {
    seedMutation.mutate(undefined, {
      onSuccess: (result) => {
        toast.success(`Seeded ${result.created} yarns (${result.skipped} skipped)`);
      },
      onError: (err) => {
        toast.error(`Failed to seed data: ${err.message}`);
      },
    });
  }

  const isEmpty = !isLoading && (!yarns || yarns.length === 0);
  const hasFiltersApplied =
    filters.search !== "" ||
    filters.weight !== "" ||
    filters.fibre !== "" ||
    filters.hasProject !== "all";

  return (
    <div>
      <Dashboard />

      <div className="flex items-center justify-between gap-2 mb-4">
        <h2 className="text-lg font-semibold text-stone-800">Your Stash</h2>
        <div className="flex gap-2">
          {isEmpty && !hasFiltersApplied && (
            <Button
              variant="outline"
              onClick={handleSeed}
              disabled={seedMutation.isPending}
            >
              <SproutIcon className="size-4 mr-1.5" />
              {seedMutation.isPending ? "Seeding..." : "Seed data"}
            </Button>
          )}
          <Button onClick={() => setAddDialogOpen(true)}>
            <PlusIcon className="size-4 mr-1.5" />
            Add Yarn
          </Button>
        </div>
      </div>

      <SearchFilters filters={filters} onChange={setFilters} />

      {isLoading ? (
        <div className="flex items-center justify-center py-16 text-stone-500">
          Loading...
        </div>
      ) : isEmpty ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3 text-stone-500">
          <p className="text-base">
            {hasFiltersApplied
              ? "No yarns match your filters."
              : "No yarns in your stash yet. Add one or seed with sample data."}
          </p>
          {hasFiltersApplied && (
            <Button variant="outline" size="sm" onClick={() => setFilters(DEFAULT_FILTERS)}>
              Clear filters
            </Button>
          )}
        </div>
      ) : (
        <YarnTable yarns={yarns!} onEdit={handleEdit} onDelete={handleDelete} />
      )}

      <YarnDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        existingNames={existingNames}
        existingFibres={existingFibres}
      />

      <YarnDialog
        open={editDialogOpen}
        onOpenChange={(open) => {
          setEditDialogOpen(open);
          if (!open) setEditYarn(null);
        }}
        yarn={editYarn ?? undefined}
        existingNames={existingNames}
        existingFibres={existingFibres}
      />

      <DeleteDialog
        open={deleteDialogOpen}
        onOpenChange={(open) => {
          setDeleteDialogOpen(open);
          if (!open) setDeleteYarn(null);
        }}
        yarn={deleteYarn}
      />
    </div>
  );
}
