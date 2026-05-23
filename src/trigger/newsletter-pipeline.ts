import { task, schedules, logger } from "@trigger.dev/sdk/v3";
import { researchTask } from "./subtasks/research";
import { draftContentTask } from "./subtasks/draft-content";
import { generateInfographicsTask } from "./subtasks/generate-infographics";
import { renderTask } from "./subtasks/render";
import { sendEmailTask } from "./subtasks/send-email";
import { archiveDriveTask } from "./subtasks/archive-drive";

export interface NewsletterPipelineInput {
  topic: string;
  days?: number;
  maxResults?: number;
  issueTitleOverride?: string;
  recipientOverride?: string;
  // false (default): pipeline stops after render and returns the HTML path for review.
  // true: pipeline sends and archives immediately without pausing.
  skipApprovalGate?: boolean;
}

export const newsletterPipeline = task({
  id: "newsletter-pipeline",
  maxDuration: 3600,
  run: async (input: NewsletterPipelineInput) => {
    const {
      topic,
      days = 30,
      maxResults = 10,
      issueTitleOverride,
      recipientOverride,
      skipApprovalGate = false,
    } = input;

    logger.log("Newsletter pipeline started", { topic, days, skipApprovalGate });

    // Step 1: Research
    const research = await researchTask.triggerAndWait({ topic, days, maxResults });
    if (!research.ok) throw new Error(`Research failed: ${research.error}`);
    logger.log("Research complete", { resultCount: research.output.results.length });

    // Step 2: Draft content with Claude API
    const draft = await draftContentTask.triggerAndWait({
      research: research.output,
      issueTitleOverride,
    });
    if (!draft.ok) throw new Error(`Content drafting failed: ${draft.error}`);
    logger.log("Content drafted", { sectionCount: draft.output.sections.length });

    // Step 3: Generate infographics (non-fatal — pipeline continues on partial failure)
    const withImages = await generateInfographicsTask.triggerAndWait(draft.output);
    const finalContent = withImages.ok ? withImages.output : draft.output;
    if (!withImages.ok) {
      logger.warn("Infographic generation failed entirely — proceeding without images");
    }

    // Step 4: Render HTML
    const rendered = await renderTask.triggerAndWait({});
    if (!rendered.ok) throw new Error(`Render failed: ${rendered.error}`);
    logger.log("Newsletter rendered", { htmlPath: rendered.output.htmlPath });

    // Step 5: Approval gate
    // When skipApprovalGate is false, the pipeline stops here.
    // Preview the HTML at the path shown above, then re-trigger with skipApprovalGate: true
    // (or trigger the pipeline-send-finalize task directly).
    if (!skipApprovalGate) {
      logger.log("Pipeline paused for approval. Preview the rendered HTML, then:", {
        action: 'Re-trigger newsletter-pipeline with { "skipApprovalGate": true } to send',
        htmlPath: rendered.output.htmlPath,
      });
      return {
        status: "pending_approval",
        htmlPath: rendered.output.htmlPath,
        title: finalContent.title,
      };
    }

    // Step 6: Derive subject line
    const now = new Date();
    const formatted = now.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
    const topicPart = finalContent.title.split("|")[0].trim();
    const subject = `${topicPart} | ${formatted}`;

    // Step 7: Send email
    const sent = await sendEmailTask.triggerAndWait({
      htmlPath: rendered.output.htmlPath,
      subject,
      to: recipientOverride,
    });
    if (!sent.ok) throw new Error(`Email send failed: ${sent.error}`);

    // Step 8: Archive to Drive
    const archived = await archiveDriveTask.triggerAndWait({
      htmlPath: rendered.output.htmlPath,
    });
    if (!archived.ok) {
      logger.warn("Drive archive failed", { error: archived.error });
    }

    const driveLink = archived.ok ? archived.output.driveLink : null;
    logger.log("Pipeline complete", { subject, driveLink });

    return {
      status: "sent",
      subject,
      driveLink,
      sectionCount: finalContent.sections.length,
    };
  },
});

// Weekly cron: every Monday at 9:00 AM UTC
export const weeklyNewsletter = schedules.task({
  id: "newsletter-weekly-cron",
  cron: "0 9 * * 1",
  run: async () => {
    const topic =
      process.env.NEWSLETTER_WEEKLY_TOPIC ?? "AI agents and automation 2026";

    logger.log("Weekly cron triggered", { topic });

    await newsletterPipeline.triggerAndWait({
      topic,
      days: 7,
      maxResults: 10,
      skipApprovalGate: true,
    });
  },
});
