import { useEffect, useRef, useState } from "react";
import { fetchAgents } from "./lib/api";
import { useChatSession } from "./hooks/useChatSession";
import HomePage from "./pages/HomePage";
import ChatScreen from "./pages/ChatScreen";

export default function App() {
  const architectureRef = useRef(null);
  const [screen, setScreen] = useState("home");
  const [agents, setAgents] = useState([]);
  const chat = useChatSession();

  useEffect(() => {
    fetchAgents()
      .then(setAgents)
      .catch(() => setAgents([]));
  }, []);

  if (screen === "home") {
    return (
      <HomePage onStartChat={() => setScreen("chat")} agents={agents} architectureRef={architectureRef} />
    );
  }

  return <ChatScreen {...chat} agents={agents} onBackHome={() => setScreen("home")} />;
}
