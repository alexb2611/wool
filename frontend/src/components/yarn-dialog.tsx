import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { YarnForm } from "@/components/yarn-form";
import { useCreateYarn, useUpdateYarn } from "@/hooks/use-yarns";
import type { Yarn, YarnCreate, YarnUpdate } from "@/types";

interface YarnDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  yarn?: Yarn;
  existingNames: string[];
  existingFibres: string[];
}

export function YarnDialog({
  open,
  onOpenChange,
  yarn,
  existingNames,
  existingFibres,
}: YarnDialogProps) {
  const createMutation = useCreateYarn();
  const updateMutation = useUpdateYarn();

  const isEditMode = yarn != null;
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  function handleSubmit(data: YarnCreate | YarnUpdate) {
    if (isEditMode) {
      updateMutation.mutate(
        { id: yarn.id, data: data as YarnUpdate },
        {
          onSuccess: () => {
            toast.success(`"${yarn.name}" updated`);
            onOpenChange(false);
          },
          onError: (err) => {
            toast.error(`Failed to update yarn: ${err.message}`);
          },
        }
      );
    } else {
      createMutation.mutate(data as YarnCreate, {
        onSuccess: () => {
          toast.success("Yarn added to stash");
          onOpenChange(false);
        },
        onError: (err) => {
          toast.error(`Failed to add yarn: ${err.message}`);
        },
      });
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditMode ? "Edit Yarn" : "Add Yarn"}</DialogTitle>
        </DialogHeader>
        <YarnForm
          initialData={yarn}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          existingNames={existingNames}
          existingFibres={existingFibres}
        />
      </DialogContent>
    </Dialog>
  );
}
