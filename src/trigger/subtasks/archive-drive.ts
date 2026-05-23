import { task, logger } from "@trigger.dev/sdk/v3";
import { runPython } from "../utils/run-python";

export interface ArchiveDriveInput {
  htmlPath: string;
}

export interface ArchiveDriveOutput {
  driveLink: string;
}

export const archiveDriveTask = task({
  id: "newsletter-archive-drive",
  maxDuration: 120,
  retry: { maxAttempts: 3, minTimeoutInMs: 5000 },
  run: async (input: ArchiveDriveInput): Promise<ArchiveDriveOutput> => {
    const stdout = runPython("tools/upload_to_drive.py", ["--file", input.htmlPath]);

    const match = stdout.match(/View link:\s*(https:\/\/\S+)/);
    const driveLink = match ? match[1] : "unknown — check Drive folder directly";

    logger.log("Archived to Drive", { driveLink });

    return { driveLink };
  },
});
