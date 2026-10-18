import { useState } from "react";
import { AppShell } from "./components/AppShell";
import { LandingScreen } from "./screens/LandingScreen";
import { Empty } from "./components/states/Empty";

export default function App() {
  const [started, setStarted] = useState(false);

  return (
    <AppShell>
      {started ? (
        <Empty message="Interview flow arrives in a later phase." />
      ) : (
        <LandingScreen onStart={() => setStarted(true)} />
      )}
    </AppShell>
  );
}
