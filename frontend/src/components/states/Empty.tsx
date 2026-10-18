export function Empty({
  message = "Nothing here yet.",
}: {
  message?: string;
}) {
  return (
    <div className="state state--empty">
      <p>{message}</p>
    </div>
  );
}
