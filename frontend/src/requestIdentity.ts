// Request identities provide deduplication, never authentication. LAN HTTP does
// not expose randomUUID/subtle, but still provides secure getRandomValues.
export function newRequestId(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = bytesToHex(bytes);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join(
    "",
  );
}

export async function requestFingerprint(payload: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  if (crypto.subtle)
    return bytesToHex(
      new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    );
  const { sha256 } = await import("@noble/hashes/sha2.js");
  return bytesToHex(sha256(bytes));
}
