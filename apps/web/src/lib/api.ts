export type ReviewAction = "APPROVE" | "EDIT" | "REJECT";

export type WorkflowResult = {
  run_id: string;
  conversation_id?: string;
  workflow_status: "COMPLETED" | "INTERRUPTED";
  intent: string;
  response: string;
  draft_response: string;
  evidence_status: string;
  escalation_required: boolean;
  escalation_reason?: string;
  risk_flags: string[];
  sources: { source_name: string; title: string; chunk_index: number; distance: number }[];
  tool_results: Record<string, unknown>[];
  graph_path: string[];
  human_review_payload?: {
    customer_message: string;
    proposed_response: string;
    escalation_reason: string;
    risk_flags: string[];
    allowed_actions: ReviewAction[];
  };
};

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request(path: string, body: Record<string, unknown>): Promise<WorkflowResult> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail ?? "The support workflow could not be completed.");
  return payload as WorkflowResult;
}

export const startChat = (message: string, conversationId: string) =>
  request("/api/chat", { message, conversation_id: conversationId });

export const resumeChat = (conversationId: string, action: ReviewAction, editedResponse?: string) =>
  request(`/api/chat/${encodeURIComponent(conversationId)}/resume`, {
    action,
    ...(editedResponse ? { edited_response: editedResponse } : {}),
  });
