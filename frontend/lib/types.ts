// Mirrors the backend Pydantic schemas (backend/app/schemas). Keep in sync
// with the generated contract once the FastAPI OpenAPI -> zod pipeline exists.

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type Grade = "A" | "B" | "C" | "D" | "F";

export type ScanStatus = "queued" | "collecting" | "judging" | "explaining" | "complete" | "failed";

export type ScanTier = "public" | "verified";

export type VerificationStatus = "unverified" | "pending" | "verified";

export interface User {
  id: string;
  email: string;
  createdAt: string;
}

export interface Domain {
  id: string;
  hostname: string;
  verificationStatus: VerificationStatus;
  verificationToken: string;
  addedAt: string;
  lastScan?: ScanSummary;
}

export interface ScanSummary {
  id: string;
  domainId: string;
  hostname: string;
  status: ScanStatus;
  tier: ScanTier;
  grade?: Grade;
  score?: number;
  startedAt: string;
  completedAt?: string;
}

export interface ScanStage {
  key: "collect" | "judge" | "explain" | "present";
  label: string;
  status: "pending" | "active" | "done" | "error";
  detail?: string;
}

export interface Finding {
  id: string;
  scanId: string;
  ruleId: string;
  title: string;
  category: string;
  severity: Severity;
  cvssVector: string;
  cvssScore: number;
  owaspCategory: string;
  evidence: Record<string, unknown>;
  simpleExplanation: string;
  technicalExplanation: string;
  remediation: string[];
  fromCache: boolean;
}

export interface ScanReport {
  scan: ScanSummary;
  stages: ScanStage[];
  summary: string;
  findings: Finding[];
  severityBreakdown: Record<Severity, number>;
}

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  info: "Informational",
};

// Status palette slot each severity maps to (dataviz status set: good / warning / serious / critical)
export const SEVERITY_STATUS_SLOT: Record<Severity, "good" | "warning" | "serious" | "critical"> = {
  critical: "critical",
  high: "serious",
  medium: "warning",
  low: "good",
  info: "good",
};

export const GRADE_COPY: Record<Grade, string> = {
  A: "Strong posture",
  B: "Good, with gaps",
  C: "Needs attention",
  D: "At real risk",
  F: "Wide open",
};
