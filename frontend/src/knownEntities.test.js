import { describe, it, expect } from "vitest";
import { formatAgentName, formatAgentList, KNOWN_AGENTS } from "./knownEntities";

describe("formatAgentName", () => {
  it("turns an internal id into a readable label", () => {
    expect(formatAgentName("a_19")).toBe("Agent 19");
    expect(formatAgentName("a_05")).toBe("Agent 5");
  });
});

describe("formatAgentList", () => {
  it("names a single agent directly", () => {
    expect(formatAgentList(["a_19"])).toBe("Agent 19");
  });

  it("joins two agents with 'and'", () => {
    expect(formatAgentList(["a_19", "a_88"])).toBe("Agent 19 and Agent 88");
  });

  it("uses an Oxford comma for three or more", () => {
    expect(formatAgentList(["a_19", "a_88", "a_31"])).toBe("Agent 19, Agent 88, and Agent 31");
  });

  it("collapses the full known roster into 'your whole team' instead of listing everyone", () => {
    expect(formatAgentList(KNOWN_AGENTS)).toBe("your whole team");
  });
});
