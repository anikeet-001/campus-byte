import React, { useState } from "react";
import { api } from "./api";

export default function Auth({ finish }) {
  const [signup, setSignup] = useState(false);
  const [role, setRole] = useState("customer");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.target));
    setBusy(true);
    setError("");
    try {
      finish(await api(signup ? "register" : "login", "POST", values));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="auth">
      <div className="poster">
        <span className="eyebrow">CAMPUS BYTE / FOOD DELIVERY</span>
        <h1>
          Campus food.
          <br />
          <em>On order.</em>
        </h1>
        <p>
          Order from a campus kitchen and follow your meal from the counter to
          your door.
        </p>
        <div className="plate" aria-hidden="true">
          🍜
        </div>
      </div>
      <form className="panel authform" onSubmit={submit}>
        <h2>{signup ? "Create an account" : "Welcome back"}</h2>
        {signup && (
          <>
            <label>
              Your name
              <input name="name" required maxLength="120" />
            </label>
            <label>
              Account type
              <select
                name="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="customer">Customer</option>
                <option value="owner">Restaurant owner</option>
                <option value="partner">Delivery partner</option>
              </select>
            </label>
            {role === "owner" && (
              <label>
                Restaurant name
                <input name="restaurant" required maxLength="120" />
              </label>
            )}
          </>
        )}
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete={signup ? "new-password" : "current-password"}
            minLength="8"
            maxLength="128"
            required
          />
        </label>
        {error && <p role="alert">{error}</p>}
        <button disabled={busy}>{signup ? "Create account" : "Sign in"}</button>
        <button
          className="link"
          type="button"
          onClick={() => {
            setSignup(!signup);
            setError("");
          }}
        >
          {signup
            ? "Already registered? Sign in"
            : "New here? Create an account"}
        </button>
      </form>
    </section>
  );
}
