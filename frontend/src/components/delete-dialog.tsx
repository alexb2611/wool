import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useDeleteYarn } from "@/hooks/use-yarns";
import type { Yarn } from "@/types";

interface DeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  yarn: Yarn | null;
}

export function DeleteDialog({ open, onOpenChange, yarn }: DeleteDialogProps) {
  const deleteMutation = useDeleteYarn();

  function handleDelete() {
    if (!yarn) return;
    deleteMutation.mutate(yarn.id, {
      onSuccess: () => {
        toast.success(`"${yarn.name}" deleted`);
        onOpenChange(false);
      },
      onError: (err) => {
        toast.error(`Failed to delete yarn: ${err.message}`);
      },
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete yarn</DialogTitle>
          <DialogDescription>
            {yarn
              ? `Are you sure you want to delete ${yarn.name} (${yarn.colour})? This cannot be undone.`
              : "Are you sure you want to delete this yarn?"}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>
            Cancel
          </DialogClose>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
