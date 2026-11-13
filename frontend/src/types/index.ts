export interface Doc {
  id: string; filename: string; file_type: string; status: string; error?: string | null;
  doc_type?: string | null; num_pages: number; created_at: string;
  latest_analysis_id?: string | null; latest_analysis_status?: string | null;
}
export interface AgentRun {
  id: string; agent: string; status: string; input: Record<string, unknown>;
  output: Record<string, unknown>; tools: string[]; error?: string | null; duration_ms?: number | null;
}
export interface Finding {
  finding_id: string; kind: "risk" | "compliance"; clause_ref: string; rationale: string;
  status: "verified" | "flagged" | "rejected"; document_page: number; document_excerpt: string;
  legal_section: string; legal_excerpt: string; citation_verified: boolean; explanation: string;
  questions: string[]; severity?: "low" | "medium" | "high"; category?: string;
  recommendation?: string; compliance_status?: string;
}
export interface Report {
  summary: string; severity_counts: Record<string, number>; findings: Finding[];
  stats: Record<string, number>; disclaimer: string;
  doc_info: { doc_type?: string; parties?: string[]; governing_law?: string | null };
}
export interface Analysis { id: string; document_id: string; status: string; error?: string | null; report?: Report | null }
export interface ChatSource { label: string; kind: string; text: string; meta: Record<string, string> }
export interface ChatReply { conversation_id: string; answer: string; sources: ChatSource[]; citations_verified: boolean }
