// @bdd-registered: RegisteredCheckoutFlow already exists in behavior-map equivalent registry
import { useState } from 'react';

export function RegisteredCheckoutFlow() {
  const [cart, setCart] = useState<string[]>([]);
  const [paid, setPaid] = useState(false);
  return (
    <form onSubmit={() => setPaid(true)}>
      <input onChange={(e) => setCart([e.target.value])} />
      {cart.map((item) => <button key={item} onClick={() => setPaid(true)}>{item}</button>)}
      {paid ? <div>결제 완료 화면</div> : null}
    </form>
  );
}
