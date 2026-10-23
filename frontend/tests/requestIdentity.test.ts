import { createHash, webcrypto } from "node:crypto";
import { afterEach, describe, expect, it, vi } from "vitest";
import { newRequestId, requestFingerprint } from "../src/requestIdentity";

afterEach(() => vi.unstubAllGlobals());

describe("HTTP LAN request identities", () => {
  it("uses secure random bytes when the secure-context UUID API is absent", () => {
    const getRandomValues = vi.fn((bytes: Uint8Array) =>
      webcrypto.getRandomValues(bytes),
    );
    vi.stubGlobal("crypto", { getRandomValues });
    const ids = Array.from({ length: 32 }, () => newRequestId());
    expect(
      ids.every((id) =>
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
          id,
        ),
      ),
    ).toBe(true);
    expect(new Set(ids).size).toBe(ids.length);
    expect(getRandomValues).toHaveBeenCalledTimes(ids.length);
  });

  it.each([null, "", { task: "局域网：x² + π", files: ["a", "b"] }])(
    "matches SHA-256 exactly with and without Web Crypto for %j",
    async (payload) => {
      const expected = createHash("sha256")
        .update(JSON.stringify(payload))
        .digest("hex");
      vi.stubGlobal("crypto", webcrypto);
      expect(await requestFingerprint(payload)).toBe(expected);
      vi.stubGlobal("crypto", {});
      expect(await requestFingerprint(payload)).toBe(expected);
    },
  );
});
