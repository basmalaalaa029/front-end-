import { useCallback, useEffect, useState } from "react";
import toast from "react-hot-toast";
import "@ui/ui_kits/interview-sim/sim.css";
import { getDraftAnalysisInputs } from "@/features/cv-analysis";
import { HubHeader, HubIcon } from "@/features/hub-shell";
import {
  useEvaluateInterview,
  useStartInterview,
  useSubmitInterviewAnswer,
} from "@/features/interview/hooks/use-interview";
import type { AnswerScore, InterviewQuestion } from "@/features/interview/types";

type TranscriptEntry = { who: "ai" | "me"; text: string };

function InterviewerCard({
  role,
  sub,
  time,
}: {
  role: string;
  sub: string;
  time: string;
}) {
  return (
    <div className="interviewer-card">
      <div className="interviewer-av">
        AI
        <span className="live" />
      </div>
      <div className="interviewer-meta">
        <div className="role">{role}</div>
        <div className="name">Interview Coach</div>
        <div className="sub">{sub}</div>
      </div>
      <div className="timer">
        <div className="t">{time}</div>
        <div className="l">Elapsed</div>
      </div>
    </div>
  );
}

function QuestionCard({
  num,
  total,
  question,
  tag,
}: {
  num: number;
  total: number;
  question: string;
  tag: string;
}) {
  return (
    <div className="question-card">
      <div className="question-num">
        Question {num} of {total}
      </div>
      <div className="question-text">{question}</div>
      <span className="question-tag">
        <HubIcon name="tag" size={11} stroke={2} />
        {tag}
      </span>
    </div>
  );
}

function Transcript({ entries }: { entries: TranscriptEntry[] }) {
  return (
    <div className="transcript">
      {entries.map((e, i) => (
        <div key={i} className={"bubble " + e.who}>
          <div className={"who " + e.who}>{e.who === "ai" ? "AI" : "You"}</div>
          <div className="text">{e.text}</div>
        </div>
      ))}
    </div>
  );
}

function FeedbackPanel({
  lastScore,
  answered,
  total,
  targetRole,
  evaluation,
}: {
  lastScore: AnswerScore | null;
  answered: number;
  total: number;
  targetRole: string;
  evaluation: { overall: number; strengths: string[]; improvements: string[] } | null;
}) {
  const metrics = lastScore
    ? [
        { label: "Clarity", pct: lastScore.clarity },
        { label: "Structure", pct: lastScore.structure },
        { label: "Relevance", pct: lastScore.relevance },
        { label: "Overall", pct: lastScore.overall },
      ]
    : [];

  return (
    <>
      <div className="feedback-section">
        <h4>Live feedback</h4>
        {metrics.length ? (
          metrics.map((m) => (
            <div key={m.label} className="metric-row">
              <span className="label">{m.label}</span>
              <span className="bar">
                <i style={{ width: `${m.pct}%` }} />
              </span>
              <span className="pct">{m.pct}</span>
            </div>
          ))
        ) : (
          <p style={{ fontSize: 13, color: "var(--fg-tertiary)" }}>Answer a question to see scores.</p>
        )}
      </div>
      {lastScore?.feedback ? (
        <div className="feedback-section">
          <h4>Coach</h4>
          <div className="coaching">
            <div className="label">
              <HubIcon name="sparkles" size={11} stroke={2} />
              Suggestion
            </div>
            <div className="body">{lastScore.feedback}</div>
          </div>
        </div>
      ) : null}
      <div className="feedback-section">
        <h4>Session</h4>
        <div className="metric-row">
          <span className="label">Questions answered</span>
          <span className="pct">
            {answered} / {total}
          </span>
        </div>
        {evaluation ? (
          <div className="metric-row">
            <span className="label">Final score</span>
            <span className="pct">{evaluation.overall}</span>
          </div>
        ) : null}
        <div className="metric-row">
          <span className="label">Role</span>
          <span className="pct">{targetRole}</span>
        </div>
      </div>
    </>
  );
}

export default function InterviewPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [answerText, setAnswerText] = useState("");
  const [lastScore, setLastScore] = useState<AnswerScore | null>(null);
  const [targetRole, setTargetRole] = useState("Software Engineer");
  const [evaluation, setEvaluation] = useState<{
    overall: number;
    strengths: string[];
    improvements: string[];
  } | null>(null);
  const [started, setStarted] = useState(false);

  const startMutation = useStartInterview();
  const answerMutation = useSubmitInterviewAnswer();
  const evaluateMutation = useEvaluateInterview();

  const startSession = useCallback(async () => {
    const draft = getDraftAnalysisInputs();
    if (!draft?.cvText) {
      toast.error("Add CV content in the editor first (at least 50 characters).");
      return;
    }
    try {
      const resp = await startMutation.mutateAsync({
        cvText: draft.cvText,
        targetRole: draft.targetRole,
      });
      setSessionId(resp.session_id);
      setQuestions(resp.questions);
      setTargetRole(draft.targetRole);
      setCurrentIdx(0);
      setTranscript([{ who: "ai", text: resp.questions[0]?.text ?? "Let's begin." }]);
      setStarted(true);
      setEvaluation(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not start interview");
    }
  }, [startMutation]);

  useEffect(() => {
    if (!started) void startSession();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const submitAnswer = async () => {
    if (!sessionId || !questions[currentIdx]) return;
    const text = answerText.trim();
    if (text.length < 10) {
      toast.error("Write at least 10 characters for your answer.");
      return;
    }

    const q = questions[currentIdx];
    setTranscript((t) => [...t, { who: "me", text }]);
    setAnswerText("");

    try {
      const resp = await answerMutation.mutateAsync({
        sessionId,
        req: { questionId: q.id, answer: text },
      });
      setLastScore(resp.score);

      if (resp.next_question) {
        const nextIdx = currentIdx + 1;
        setCurrentIdx(nextIdx);
        setTranscript((t) => [...t, { who: "ai", text: resp.next_question!.text }]);
      } else {
        const ev = await evaluateMutation.mutateAsync(sessionId);
        setEvaluation({
          overall: ev.overall_score,
          strengths: ev.strengths,
          improvements: ev.improvements,
        });
        toast.success(`Interview complete — score ${ev.overall_score}/100`);
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Submit failed");
    }
  };

  const currentQ = questions[currentIdx];
  const busy = startMutation.isPending || answerMutation.isPending || evaluateMutation.isPending;

  if (!started && startMutation.isPending) {
    return (
      <p style={{ padding: 32, color: "var(--fg-secondary)" }}>Starting interview session…</p>
    );
  }

  return (
    <>
      <HubHeader
        title="Interview Sim"
        sub={`${targetRole} · ${questions.length} questions`}
        right={
          <>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={busy}
              onClick={() => void startSession()}
            >
              <HubIcon name="refresh-ccw" size={14} stroke={2} />
              Restart
            </button>
            <button
              type="button"
              className="btn btn-primary"
              disabled={!sessionId || busy}
              onClick={() => sessionId && void evaluateMutation.mutateAsync(sessionId).then((ev) => {
                setEvaluation({
                  overall: ev.overall_score,
                  strengths: ev.strengths,
                  improvements: ev.improvements,
                });
                toast.success(`Score: ${ev.overall_score}/100`);
              })}
            >
              <HubIcon name="square" size={14} stroke={2} />
              End session
            </button>
          </>
        }
      />
      <div className="sim-layout">
        <div className="sim-stage">
          <InterviewerCard
            role="AI interviewer"
            sub="Role-based behavioral questions scored against your CV."
            time="—"
          />
          {currentQ ? (
            <QuestionCard
              num={currentIdx + 1}
              total={questions.length}
              question={currentQ.text}
              tag={currentQ.category}
            />
          ) : null}
          <Transcript entries={transcript} />
          <div className="mic-bar" style={{ flexWrap: "wrap", gap: 8 }}>
            <textarea
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Type your answer here…"
              rows={3}
              style={{
                flex: "1 1 100%",
                padding: 10,
                borderRadius: 8,
                border: "1px solid var(--border-subtle)",
                fontFamily: "inherit",
              }}
            />
            <button
              type="button"
              className="btn btn-ai"
              disabled={busy || !currentQ}
              onClick={() => void submitAnswer()}
            >
              <HubIcon name="send" size={14} stroke={2} />
              Submit answer
            </button>
          </div>
        </div>
        <div className="sim-side">
          <FeedbackPanel
            lastScore={lastScore}
            answered={currentIdx}
            total={questions.length}
            targetRole={targetRole}
            evaluation={evaluation}
          />
        </div>
      </div>
    </>
  );
}
