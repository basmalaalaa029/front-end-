/** In-memory CV file shared across job matching and interview (survives navigation). */

let pipelineCvFile: File | null = null;

export function setPipelineCvFile(file: File): void {
  pipelineCvFile = file;
}

export function getPipelineCvFile(): File | null {
  return pipelineCvFile;
}

export function clearPipelineCvFile(): void {
  pipelineCvFile = null;
}

/** Return and clear the CV file used for the current job-match session. */
export function takePipelineCvFile(): File | null {
  const file = pipelineCvFile;
  pipelineCvFile = null;
  return file;
}
