import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { HubLayout } from "@/features/hub-shell";
import { DashboardPage } from "@/features/dashboard";
import { AnalysisPage } from "@/features/cv-analysis";
import { CvEditorPage, CvTemplatePickerPage, CvWizardPage } from "@/features/cv-editor";
import { JobAgentPage } from "@/features/job-agent";
import { InterviewPage } from "@/features/interview";
import Home from "@/features/landing";
import { LoginPage, RegisterPage, ProtectedRoute } from "@/features/auth";
import { OAuthCallbackPage } from "@/features/auth/components/oauth-callback-page";
import { ProfilePage } from "@/features/profile";

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
        {/* Public routes */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth/callback" element={<OAuthCallbackPage />} />

        {/* Protected routes — redirect to /login if not authenticated */}
        <Route
          element={
            <ProtectedRoute>
              <HubLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/analyzer" element={<AnalysisPage />} />
          <Route path="/dashboard/jobs" element={<JobAgentPage />} />
          <Route path="/dashboard/editor" element={<CvTemplatePickerPage />} />
          <Route path="/dashboard/editor/create/:templateId" element={<CvWizardPage />} />
          <Route path="/dashboard/editor/build/:templateId" element={<CvEditorPage />} />
          <Route path="/dashboard/interview" element={<InterviewPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
