import type { AppSettings } from '../../types/models';
import { deliverClone } from './client';
import { defaultSettings } from './seed';

type SettingsListener = (settings: AppSettings) => void;

let currentSettings: AppSettings = structuredClone(defaultSettings);
const listeners = new Set<SettingsListener>();

export async function getSettings(): Promise<AppSettings> {
  return deliverClone(currentSettings);
}

export async function updateSettings(partial: Partial<AppSettings>): Promise<AppSettings> {
  currentSettings = {
    ...currentSettings,
    ...partial,
  };

  listeners.forEach((listener) => {
    listener(structuredClone(currentSettings));
  });

  return deliverClone(currentSettings);
}

export function subscribeSettings(listener: SettingsListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function resetSettingsApi(): void {
  currentSettings = structuredClone(defaultSettings);
  listeners.clear();
}
