import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";
import MainLayout from "./MainLayout";

// Pages
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import ATSAnalyzePage from "./pages/ATSAnalyzePage";
import JobMatchPage from "./pages/JobMatchPage";
import CVEditorPage from "./pages/CVEditorPage";
import Profile from "../src/components/profile";
function App() {
  return (
    <Router>
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: "#13141f",
            color: "#fff",
            border: "1px solid rgba(255,255,255,0.1)",
          },
        }}
      />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
        <Route path="/profile" element={<Profile />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/analyzer" element={<ATSAnalyzePage />} />
          <Route path="/dashboard/jobs" element={<JobMatchPage />} />
          <Route path="/dashboard/editor" element={<CVEditorPage />} />
        </Route>
        {/* إعادة توجيه أي مسار غير معروف */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
