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
