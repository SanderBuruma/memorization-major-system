/** Escape HTML special characters to prevent XSS when inserting into innerHTML. */
export function escapeHTML(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
