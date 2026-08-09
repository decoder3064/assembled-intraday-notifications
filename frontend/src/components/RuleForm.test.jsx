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

  it("converts a typed whole-number percentage into a fraction on submit", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "sla_risk");
    await user.selectOptions(screen.getByLabelText(/queue/i), "billing");
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

describe("RuleForm — entity selection", () => {
  beforeEach(() => {
    api.createRule.mockResolvedValue({});
    api.updateRule.mockResolvedValue({});
  });

  it("shows a queue dropdown, not a free-text field, for queue-based rules", () => {
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);
    const queueField = screen.getByLabelText(/queue/i);
    expect(queueField.tagName).toBe("SELECT");
    expect(screen.getByRole("option", { name: "billing" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "tier_2" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "vip" })).toBeInTheDocument();
  });

  it("shows agent checkboxes, not a free-text field, for multi-agent rules", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "long_call");

    expect(screen.queryByRole("textbox", { name: /agent/i })).not.toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "a_31" })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "a_11" })).toBeInTheDocument();
  });

  it("checking two agents submits a real array, not a parsed string", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "long_call");
    await user.click(screen.getByRole("checkbox", { name: "a_31" }));
    await user.click(screen.getByRole("checkbox", { name: "a_11" }));
    await user.type(screen.getByLabelText(/minutes threshold/i), "45");
    await user.type(screen.getByLabelText(/recipient/i), "lead_maria");
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(api.createRule).toHaveBeenCalledWith(
      expect.objectContaining({ scope: { agent_ids: ["a_31", "a_11"] } })
    );
  });

  it("unchecking a previously-checked agent removes them from the array", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "long_call");
    await user.click(screen.getByRole("checkbox", { name: "a_31" }));
    await user.click(screen.getByRole("checkbox", { name: "a_11" }));
    await user.click(screen.getByRole("checkbox", { name: "a_31" })); // uncheck
    await user.type(screen.getByLabelText(/minutes threshold/i), "45");
    await user.type(screen.getByLabelText(/recipient/i), "lead_maria");
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(api.createRule).toHaveBeenCalledWith(expect.objectContaining({ scope: { agent_ids: ["a_11"] } }));
  });

  it("pre-checks the correct agents when editing an existing rule", () => {
    render(
      <RuleForm
        onCreated={vi.fn()}
        onCancel={vi.fn()}
        initialRule={{
          id: "r1",
          rule_type: "long_call",
          scope: { agent_ids: ["a_31", "a_11"] },
          params: { duration_min: 45 },
          recipient_id: "lead_maria",
          severity: 6,
        }}
      />
    );

    expect(screen.getByRole("checkbox", { name: "a_31" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "a_11" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "a_19" })).not.toBeChecked();
  });

  it("shows a single-agent dropdown for adherence_self, not checkboxes or free text", async () => {
    const user = userEvent.setup();
    render(<RuleForm onCreated={vi.fn()} onCancel={vi.fn()} />);

    await user.selectOptions(screen.getByLabelText(/rule type/i), "adherence_self");

    const agentField = screen.getByLabelText(/your agent id/i);
    expect(agentField.tagName).toBe("SELECT");
  });
});
