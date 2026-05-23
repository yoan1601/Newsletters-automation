import { task, logger } from "@trigger.dev/sdk/v3";
import * as path from "path";
import * as fs from "fs";
import { runPython, tmpPath, PROJECT_ROOT } from "../utils/run-python";

export interface RenderOutput {
  htmlPath: string;
  dateStr: string;
}

export const renderTask = task({
  id: "newsletter-render",
  maxDuration: 120,
  retry: { maxAttempts: 2, minTimeoutInMs: 3000 },
  run: async (_payload: Record<string, never>): Promise<RenderOutput> => {
    const contentPath = tmpPath("newsletter_content.json");

    if (!fs.existsSync(contentPath)) {
      throw new Error(`newsletter_content.json not found at ${contentPath}. Run draft-content first.`);
    }

    const dateStr = new Date().toISOString().slice(0, 10);
    const outputPath = path.join(PROJECT_ROOT, ".tmp", `newsletter_${dateStr}.html`);

    runPython("tools/render_newsletter.py", [
      "--content", contentPath,
      "--output", outputPath,
    ]);

    if (!fs.existsSync(outputPath)) {
      throw new Error(`Rendered HTML not found at expected path: ${outputPath}`);
    }

    const sizeKb = fs.statSync(outputPath).size / 1024;
    logger.log(`Rendered newsletter`, { path: outputPath, sizeKb: sizeKb.toFixed(1) });

    return { htmlPath: outputPath, dateStr };
  },
});
