
// Client-side mirror of the backend SSRF guard's obvious rejects. This is a
// UX nicety only — the real, authoritative check resolves DNS server-side
// and blocks RFC1918 / loopback / link-local / metadata ranges on every
// outbound request and again after every redirect (backend/app/security/ssrf.py).

const BLOCKED_HOST_PATTERNS = [
  /^localhost$/i,
  /^127\./,
  /^0\.0\.0\.0$/,
  /^169\.254\./, // link-local / cloud metadata (169.254.169.254)
  /^10\./,
  /^192\.168\./,
  /^172\.(1[6-9]|2\d|3[01])\./,
  /^::1$/,
  /^\[?::1\]?$/,
  /\.local$/i,
  /^0x[0-9a-f]+$/i,
];

export function validateTarget(input: string): { ok: true; hostname: string } | { ok: false; reason: string } {
  const trimmed = input.trim().toLowerCase();
  if (!trimmed) return { ok: false, reason: "Enter a domain." };

  let hostname = trimmed;
  try {
    hostname = trimmed.includes("://") ? new URL(trimmed).hostname : new URL(`https://${trimmed}`).hostname;
  } catch {
    return { ok: false, reason: "That doesn't look like a valid domain." };
  }

  if (BLOCKED_HOST_PATTERNS.some((re) => re.test(hostname))) {
    return { ok: false, reason: "Private, loopback, and link-local targets are blocked — this scans public sites only." };
  }

  if (!hostname.includes(".") && hostname !== "localhost") {
    return { ok: false, reason: "Enter a full domain, e.g. yourcompany.com." };
  }

  return { ok: true, hostname };
}
