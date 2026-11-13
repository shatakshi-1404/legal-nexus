import type { Finding } from "../../types";

export default function CitationCard({ f }: { f: Finding }) {
  return (
    <div className="mt-2 space-y-2 text-xs">
      <blockquote className="border-l-2 border-line pl-2 text-ink-soft">
        <span className="font-medium text-navy">Your document, page {f.document_page}:</span> {f.document_excerpt.slice(0, 300)}
      </blockquote>
      {f.legal_excerpt ? (
        <blockquote className="border-l-2 border-accent pl-2 text-ink-soft">
          <span className="font-medium text-navy">{f.legal_section}</span> {f.citation_verified ? "(checked against source)" : "(unchecked)"}: {f.legal_excerpt}
        </blockquote>
      ) : <p className="text-ink-soft">No legal source was cited for this finding.</p>}
    </div>
  );
}
