import { useCvDraftStore } from "@/features/cv-editor/stores/cv-draft-store";

/** Reload persisted CV draft for the current signed-in user. */
export function rehydrateUserScopedStores(): void {
  void useCvDraftStore.persist.rehydrate();
}
