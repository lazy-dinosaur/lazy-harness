type WindowControlsProps = {
  onClose: () => void;
  useScrollBehavior: 'initialScrollSettleMs' | 'manual';
  initialScrollSettleMs: number;
};

export function WindowControls({ onClose, useScrollBehavior, initialScrollSettleMs }: WindowControlsProps) {
  return (
    <section data-scroll-behavior={useScrollBehavior} data-initial-scroll-settle-ms={initialScrollSettleMs}>
      <button type="button" onClick={onClose}>닫기</button>
    </section>
  );
}
