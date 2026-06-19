/** Holds a resume file between gallery/upload click and Analysis page mount. */
let pendingFile: File | null = null;

export function setPendingAnalysisFile(file: File): void {
  pendingFile = file;
}

export function takePendingAnalysisFile(): File | null {
  const file = pendingFile;
  pendingFile = null;
  return file;
}
