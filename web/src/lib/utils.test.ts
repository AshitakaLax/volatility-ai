/**
 * runUrl() is the whole mechanism behind "selecting a simulation opens
 * a new tab": every place that offers to open a run builds its href
 * from this one function. A bug here is not a display glitch -- it is
 * either a link nobody can open, or a link that opens the wrong run.
 *
 * `base` is passed explicitly rather than relying on `window.location`
 * (its real default) -- this project's vitest setup runs in a plain
 * Node environment with no DOM library installed, and the function
 * accepting a base is what keeps this testable without adding one.
 */
import { describe, expect, it } from "vitest";

import { runUrl } from "./utils";

describe("runUrl", () => {
  it("carries a run id as the only query parameter", () => {
    const url = new URL(runUrl("abc123", "http://localhost:8000/"));
    expect(url.searchParams.get("run")).toBe("abc123");
    expect([...url.searchParams.keys()]).toEqual(["run"]);
  });

  it("keeps the given origin and path", () => {
    const url = new URL(runUrl("abc123", "http://172.16.0.137:8000/some/path"));
    expect(url.origin).toBe("http://172.16.0.137:8000");
    expect(url.pathname).toBe("/some/path");
  });

  it("drops whatever query params were already present", () => {
    const url = new URL(runUrl("abc123", "http://localhost:8000/?tab=live&debug=1"));
    expect([...url.searchParams.keys()]).toEqual(["run"]);
  });

  it("url-encodes a run id that needs it", () => {
    const url = new URL(runUrl("has space/slash", "http://localhost:8000/"));
    expect(url.searchParams.get("run")).toBe("has space/slash");
  });
});
