import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";
import { logger } from "@trigger.dev/sdk/v3";

// Fall back to cwd — true when `npx trigger.dev@latest dev` is run from the project root.
// Set PROJECT_ROOT in .env to override (e.g. for cloud deployments).
export const PROJECT_ROOT = process.env.PROJECT_ROOT ?? process.cwd();

export function runPython(
  scriptRelPath: string,
  args: string[],
  timeoutMs = 120_000
): string {
  const scriptAbs = path.join(PROJECT_ROOT, scriptRelPath);
  const argStr = args.map((a) => `"${a.replace(/"/g, '\\"')}"`).join(" ");
  const cmd = `python "${scriptAbs}" ${argStr}`;

  logger.log(`Running Python: ${scriptRelPath}`);

  try {
    const stdout = execSync(cmd, {
      cwd: PROJECT_ROOT,
      env: { ...process.env },
      timeout: timeoutMs,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "pipe"],
    }) as string;

    return stdout;
  } catch (err: any) {
    const stdout: string = err.stdout?.toString() ?? "";
    const stderr: string = err.stderr?.toString() ?? "";
    throw new Error(
      `Python script failed: ${scriptRelPath}\nSTDOUT: ${stdout}\nSTDERR: ${stderr}`
    );
  }
}

export function readTmpJson<T>(filename: string): T {
  const filepath = path.join(PROJECT_ROOT, ".tmp", filename);
  if (!fs.existsSync(filepath)) {
    throw new Error(`Expected output file not found: ${filepath}`);
  }
  return JSON.parse(fs.readFileSync(filepath, "utf-8")) as T;
}

export function writeTmpJson(filename: string, data: unknown): void {
  const dir = path.join(PROJECT_ROOT, ".tmp");
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, filename), JSON.stringify(data, null, 2), "utf-8");
}

export function tmpPath(filename: string): string {
  return path.join(PROJECT_ROOT, ".tmp", filename);
}
