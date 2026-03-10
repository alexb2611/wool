import { request } from "./client";
import type { Yarn, YarnCreate, YarnUpdate, YarnStats, YarnListParams, SeedResult } from "../types";

export function listYarns(params?: YarnListParams): Promise<Yarn[]> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        searchParams.set(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return request<Yarn[]>(`/yarns/${query ? `?${query}` : ""}`);
}

export function getYarn(id: number): Promise<Yarn> {
  return request<Yarn>(`/yarns/${id}`);
}

export function createYarn(data: YarnCreate): Promise<Yarn> {
  return request<Yarn>("/yarns/", { method: "POST", body: JSON.stringify(data) });
}

export function updateYarn(id: number, data: YarnUpdate): Promise<Yarn> {
  return request<Yarn>(`/yarns/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteYarn(id: number): Promise<void> {
  return request<void>(`/yarns/${id}`, { method: "DELETE" });
}

export function getYarnStats(): Promise<YarnStats> {
  return request<YarnStats>("/yarns/stats");
}

export function seedYarns(): Promise<SeedResult> {
  return request<SeedResult>("/yarns/seed", { method: "POST" });
}
