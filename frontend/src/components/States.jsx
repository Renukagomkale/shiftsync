import { errorMessages } from "../api";

export function Loading({ label = "Loading" }) {
  return <p className="py-16 text-center font-display text-lg">{label}...</p>;
}

export function ErrorBox({ error, onRetry }) {
  return (
    <div className="rounded-2xl border border-ink bg-paper p-5" role="alert">
      <p className="font-medium">{errorMessages(error)[0]}</p>
      {onRetry && (
        <button onClick={onRetry} className="pill mt-3">
          Try again
        </button>
      )}
    </div>
  );
}

export function ErrorList({ messages }) {
  if (!messages.length) return null;
  return (
    <ul className="rounded-xl border border-ink bg-butter/60 px-4 py-3 text-sm" role="alert">
      {messages.map((message) => (
        <li key={message}>{message}</li>
      ))}
    </ul>
  );
}
