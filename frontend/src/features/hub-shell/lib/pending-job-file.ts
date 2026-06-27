/** In-memory CV file handoff into job matching (same pattern as analysis pending upload). */

let pendingFile: File | null = null;

export function setPendingJobFile(file: File): void {
  pendingFile = file;
}

export function takePendingJobFile(): File | null {
  const file = pendingFile;
  pendingFile = null;
  return file;
}
