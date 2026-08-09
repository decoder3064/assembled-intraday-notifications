import { describe, it, expect } from "vitest";
import { tierFor } from "./SeverityBadge";

describe("tierFor", () => {
  it("classifies low severities", () => {
    expect(tierFor(1)).toBe("low");
    expect(tierFor(2)).toBe("low");
  });

  it("classifies mid severities", () => {
    expect(tierFor(3)).toBe("mid");
    expect(tierFor(5)).toBe("mid");
  });

  it("classifies high severities", () => {
    expect(tierFor(6)).toBe("high");
    expect(tierFor(10)).toBe("high");
  });
});
