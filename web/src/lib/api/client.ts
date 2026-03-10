const requestLog: string[] = [];

function sleep(durationMs: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, durationMs);
  });
}

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function requestResource<T>(
  resourceKey: string,
  resolver: () => T | Promise<T>,
): Promise<T> {
  requestLog.push(resourceKey);
  await sleep(12);
  return resolver();
}

export async function deliverClone<T>(value: T): Promise<T> {
  return requestResource('deliverClone', () => structuredClone(value));
}

export function getRequestLog(): string[] {
  return [...requestLog];
}

export function resetRequestLog(): void {
  requestLog.length = 0;
}
