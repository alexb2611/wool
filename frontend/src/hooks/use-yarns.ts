import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as yarnsApi from "../api/yarns";
import type { YarnCreate, YarnUpdate, YarnListParams } from "../types";

const YARNS_KEY = ["yarns"];
const STATS_KEY = ["yarns", "stats"];

export function useYarnList(params?: YarnListParams) {
  return useQuery({
    queryKey: [...YARNS_KEY, params],
    queryFn: () => yarnsApi.listYarns(params),
  });
}

export function useYarn(id: number) {
  return useQuery({
    queryKey: [...YARNS_KEY, id],
    queryFn: () => yarnsApi.getYarn(id),
  });
}

export function useYarnStats() {
  return useQuery({
    queryKey: STATS_KEY,
    queryFn: yarnsApi.getYarnStats,
  });
}

export function useCreateYarn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: YarnCreate) => yarnsApi.createYarn(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useUpdateYarn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: YarnUpdate }) => yarnsApi.updateYarn(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useDeleteYarn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => yarnsApi.deleteYarn(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useSeedYarns() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: yarnsApi.seedYarns,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: YARNS_KEY });
      queryClient.invalidateQueries({ queryKey: STATS_KEY });
    },
  });
}

export function useScrapeYarn() {
  return useMutation({
    mutationFn: (url: string) => yarnsApi.scrapeYarn(url),
  });
}
