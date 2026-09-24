import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { CreateResearch } from "./pages/CreateResearch";
import { Dashboard } from "./pages/Dashboard";
import { History } from "./pages/History";
import { Login } from "./pages/Login";
import { PersonaChat } from "./pages/PersonaChat";
import { Register } from "./pages/Register";
import { ResearchDetail } from "./pages/ResearchDetail";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/research/new" element={<CreateResearch />} />
          <Route path="/research/:id" element={<ResearchDetail />} />
          <Route path="/research/:id/personas/:personaId/chat" element={<PersonaChat />} />
          <Route path="/history" element={<History />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
