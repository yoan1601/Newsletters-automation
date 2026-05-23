import { task, logger } from "@trigger.dev/sdk/v3";
import { runPython } from "../utils/run-python";

export interface SendEmailInput {
  htmlPath: string;
  subject: string;
  to?: string;
}

export const sendEmailTask = task({
  id: "newsletter-send-email",
  maxDuration: 60,
  retry: { maxAttempts: 2, minTimeoutInMs: 10_000 },
  run: async (input: SendEmailInput): Promise<{ messageSent: boolean }> => {
    const { htmlPath, subject, to } = input;

    const args = ["--subject", subject, "--html-file", htmlPath];
    if (to) args.push("--to", to);

    runPython("tools/send_email_gmail.py", args);
    logger.log("Email sent", { subject, to: to ?? "default recipient" });

    return { messageSent: true };
  },
});
