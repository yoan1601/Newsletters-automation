import { task, logger } from "@trigger.dev/sdk/v3";
import * as fs from "fs";
import * as path from "path";
import { runPython, writeTmpJson, PROJECT_ROOT } from "../utils/run-python";
import type { NewsletterContent } from "./draft-content";

const MAX_INFOGRAPHICS = 3;

export const generateInfographicsTask = task({
  id: "newsletter-generate-infographics",
  // kie.ai can take up to 5 min per image; 3 images in parallel = ~20 min max
  maxDuration: 1200,
  run: async (content: NewsletterContent): Promise<NewsletterContent> => {
    const candidates = content.sections
      .map((section, index) => ({ section, index }))
      .filter(({ section }) => !!section.infographic_alt)
      .slice(0, MAX_INFOGRAPHICS);

    if (candidates.length === 0) {
      logger.log("No sections with infographic_alt — skipping image generation");
      return content;
    }

    logger.log(`Generating ${candidates.length} infographic(s) in parallel`);

    const results = await Promise.allSettled(
      candidates.map(async ({ section, index }) => {
        // Sanitize name: no spaces, lowercase, max 30 chars
        const name = `section_${String(index + 1).padStart(2, "0")}`;
        const prompt = `${section.infographic_alt}. Context: ${section.title}.`;

        try {
          runPython(
            "tools/generate_infographic.py",
            ["--prompt", prompt, "--name", name],
            360_000 // 6-minute timeout per image
          );

          const outputPath = path.join(PROJECT_ROOT, ".tmp", `infographic_${name}.jpg`);
          if (fs.existsSync(outputPath)) {
            logger.log(`Infographic generated for section ${index + 1}`, { path: outputPath });
            return { index, imgPath: `.tmp/infographic_${name}.jpg` };
          }
          throw new Error(`Expected output not found: ${outputPath}`);
        } catch (err) {
          logger.warn(`Infographic failed for section ${index + 1} — skipping`, {
            error: String(err).slice(0, 200),
          });
          return null;
        }
      })
    );

    // Patch successfully generated images into the content object
    const updatedSections = [...content.sections];
    for (const result of results) {
      if (result.status === "fulfilled" && result.value !== null) {
        const { index, imgPath } = result.value;
        updatedSections[index] = { ...updatedSections[index], infographic_path: imgPath };
      }
    }

    const updatedContent: NewsletterContent = { ...content, sections: updatedSections };
    writeTmpJson("newsletter_content.json", updatedContent);

    const successCount = results.filter((r) => r.status === "fulfilled" && r.value !== null).length;
    logger.log(`Infographics complete: ${successCount}/${candidates.length} succeeded`);

    return updatedContent;
  },
});
