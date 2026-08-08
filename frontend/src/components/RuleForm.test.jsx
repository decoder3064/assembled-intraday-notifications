import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RuleForm from "./RuleForm";
import * as api from "../api";

vi.mock("../api");

describe("RuleForm", () => {
  beforeEach(() => {
    api.createRule.mockResolvedValue({});
    api.updateRule.mockResolvedValue({});
  });

  it("does not crash while typing agent IDs (regression test — this used to blank the whole page)", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "long_call");
    await user.type(screen.getByLabelText(/agent ids/i), "a_31 a_11");

    expect(screen.getByText(/a_31, a_11/)).toBeInTheDocument();
  });

  it("splits agent IDs on comma or whitespace into a real array on submit", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "long_call");
    await user.type(screen.getByLabelText(/agent ids/i), "a_31, a_11");
    await user.type(screen.getByLabelText(/minutes threshold/i), "45");
    await user.type(screen.getByLabelText(/recipient/i), "lead_maria");
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(api.createRule).toHaveBeenCalledWith(
      expect.objectContaining({ scope: { agent_ids: ["a_31", "a_11"] } })
    );
  });

  it("converts a typed whole-number percentage into a fraction on submit", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "sla_risk");
    await user.type(screen.getByLabelText(/queue/i), "billing");
    await user.type(screen.getByLabelText(/warn at/i), "80");
    await user.type(screen.getByLabelText(/recipient/i), "lead_maria");
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(api.createRule).toHaveBeenCalledWith(expect.objectContaining({ params: { pct_of_sla: 0.8 } }));
  });

  it("pre-fills a whole-number percentage when editing an existing fraction-based rule", () => {
    render(
      <RuleForm
        onCreated={vi.fn()}
        onCancel={vi.fn()}
        initialRule={{
          id: "r1",
          rule_type: "sla_risk",
          scope: { queue_id: "billing" },
          params: { pct_of_sla: 0.8 },
          recipient_id: "lead_maria",
          severity: 3,
        }}
      />
    );

    expect(screen.getByLabelText(/warn at/i)).toHaveValue(80);
  });

  it("locks the rule type dropdown while editing, since changing it would invalidate scope/params", () => {
    render(
      <RuleForm
        onCreated={vi.fn()}
        onCancel={vi.fn()}
        initialRule={{
          id: "r1",
          rule_type: "queue_backlog",
          scope: { queue_id: "billing" },
          params: { threshold: 20 },
          recipient_id: "lead_maria",
          severity: 4,
        }}
      />
    );

    expect(screen.getByLabelText(/rule type/i)).toBeDisabled();
  });
});
