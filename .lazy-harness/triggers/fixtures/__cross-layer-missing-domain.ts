export function calculateInvoiceChecksum(invoiceNumber: string): number {
  return [...invoiceNumber].reduce((sum, char) => sum + char.charCodeAt(0), 0);
}
