import { Link } from "react-router-dom";
import { useAuthStore } from "../lib/store";
import {
  ArrowLeft,
  Sparkles,
  Activity,
  Bell,
  Lightbulb,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { motion } from "framer-motion";
import { useState, useRef, useEffect } from "react";

/* ─── Types ──────────────────────────────────────────────── */
interface ServiceCard {
  href: string;
  emoji: string;
  badge: string;
  title: string;
  titleAr: string;
  desc: string;
  cta: string;
  gradient: string;
  borderHover: string;
  shadowHover: string;
  accent: string;
}

/* ─── Data ───────────────────────────────────────────────── */
const SERVICES: ServiceCard[] = [
  {
    href: "/dashboard/analyzer",
    emoji: "🔍",
    badge: "ATS SCORE",
    title: "CV Analyzer",
    titleAr: "محلّل السيرة الذاتية",
    desc: "ارفع ملف PDF واحصل على درجة ATS مفصّلة، الكلمات المفقودة، وتوصيات فورية.",
    cta: "ابدأ التحليل",
    gradient: "from-violet-600 to-purple-700",
    borderHover: "group-hover:border-violet-500/60",
    shadowHover: "group-hover:shadow-[0_24px_48px_rgba(139,92,246,.28)]",
    accent: "text-violet-400",
  },
  {
    href: "/dashboard/jobs",
    emoji: "💼",
    badge: "SMART MATCH",
    title: "Job Matcher",
    titleAr: "مطابق الوظائف",
    desc: "قارن سيرتك بأي إعلان وظيفي واحصل على درجة تطابق مفصّلة مع تحليل الفجوات.",
    cta: "ابحث عن وظيفة",
    gradient: "from-cyan-500 to-sky-600",
    borderHover: "group-hover:border-cyan-500/60",
    shadowHover: "group-hover:shadow-[0_24px_48px_rgba(34,211,238,.22)]",
    accent: "text-cyan-400",
  },
  {
    href: "/dashboard/editor",
    emoji: "✏️",
    badge: "AI EDITOR",
    title: "CV Editor",
    titleAr: "محرّر السيرة الذاتية",
    desc: "عدّل وحسّن سيرتك الذاتية بمساعدة الذكاء الاصطناعي في الوقت الفعلي.",
    cta: "ابدأ التحرير",
    gradient: "from-emerald-500 to-teal-600",
    borderHover: "group-hover:border-emerald-500/60",
    shadowHover: "group-hover:shadow-[0_24px_48px_rgba(52,211,153,.22)]",
    accent: "text-emerald-400",
  },
  {
    href: "/dashboard/analysis",
    emoji: "📊",
    badge: "DEEP ANALYSIS",
    title: "Career Analysis",
    titleAr: "تحليل المسار المهني",
    desc: "تحليل شامل لمسارك مع خارطة طريق مخصصة لأهدافك المستقبلية.",
    cta: "اكتشف مسارك",
    gradient: "from-pink-500 to-rose-600",
    borderHover: "group-hover:border-pink-500/60",
    shadowHover: "group-hover:shadow-[0_24px_48px_rgba(244,114,182,.22)]",
    accent: "text-pink-400",
  },
  {
    href: "/dashboard/ats",
    emoji: "⚡",
    badge: "OPTIMIZER",
    title: "ATS Optimizer",
    titleAr: "محسّن نظام ATS",
    desc: "حسّن سيرتك لتجاوز أنظمة تتبع المتقدمين بنسبة 95%+ مع كلمات مفتاحية مستهدفة.",
    cta: "حسّن الآن",
    gradient: "from-amber-500 to-orange-500",
    borderHover: "group-hover:border-amber-500/60",
    shadowHover: "group-hover:shadow-[0_24px_48px_rgba(251,191,36,.22)]",
    accent: "text-amber-400",
  },
];

const STATS = [
  { emoji: "📄", val: "3",  label: "ملفات مرفوعة",  vc: "text-violet-400"  },
  { emoji: "📈", val: "87", label: "درجة ATS",        vc: "text-cyan-400"    },
  { emoji: "💼", val: "12", label: "وظائف متطابقة",  vc: "text-emerald-400" },
];

const PROGRESS = [
  { label: "رفع السيرة الذاتية", pct: 100, bar: "from-violet-500 to-purple-500" },
  { label: "تحليل ATS",          pct: 87,  bar: "from-cyan-500 to-sky-500"      },
  { label: "مطابقة وظيفة",       pct: 65,  bar: "from-emerald-500 to-teal-500"  },
  { label: "تحسين ATS",          pct: 40,  bar: "from-amber-500 to-orange-500"  },
];

/* ─── Animation Variants ─────────────────────────────────── */
const stagger = {
  hidden:  { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.04 } },
};
const fadeUp = {
  hidden:  { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

/* ─── Dashboard Component ────────────────────────────────── */
export default function Dashboard() {
  const { user } = useAuthStore();
  const firstName = user?.name?.split(" ")[0] ?? "مستخدم";

  /* slider state */
  const [current, setCurrent] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [cardW, setCardW] = useState(0);
  const [vis,   setVis]   = useState(2);
  const maxSlide = SERVICES.length - vis;
  const touchX   = useRef(0);

  useEffect(() => {
    const calc = () => {
      const v = window.innerWidth < 640 ? 1 : 2;
      setVis(v);
      if (wrapRef.current) {
        const gap = 16;
        setCardW((wrapRef.current.clientWidth - gap * (v - 1)) / v + gap);
      }
    };
    calc();
    window.addEventListener("resize", calc);
    return () => window.removeEventListener("resize", calc);
  }, []);

  const goTo = (i: number) => setCurrent(Math.max(0, Math.min(i, maxSlide)));

  return (
    /*
     * ─── FIX FOR WHITE GAP ───────────────────────────────────
     * Use w-full + min-h-screen so this component always fills
     * whatever space the parent layout (sidebar + main) gives it.
     * Remove any max-w constraint at the top level so the dark
     * background stretches edge-to-edge inside the content area.
     * The inner max-w-5xl wrapper keeps content readable on large screens.
     */
    <div
      dir="rtl"
      className="w-full min-h-screen bg-[#0b0f1a] text-white"
      style={{ fontFamily: "'Cairo', sans-serif" }}
    >
      {/* Ambient mesh — fixed behind everything */}
      <div
        aria-hidden
        className="fixed inset-0 pointer-events-none"
        style={{
          zIndex: 0,
          background: `
            radial-gradient(ellipse 55% 38% at 18% 8%,  rgba(99,102,241,.13) 0%, transparent 60%),
            radial-gradient(ellipse 45% 32% at 82% 78%, rgba(34,211,238,.08) 0%, transparent 60%),
            radial-gradient(ellipse 38% 28% at 55% 45%, rgba(167,139,250,.05) 0%, transparent 50%)
          `,
        }}
      />

      {/* Content */}
      <motion.div
        variants={stagger}
        initial="hidden"
        animate="visible"
        className="relative z-10 max-w-5xl mx-auto px-5 md:px-8 py-8 pb-16"
      >
        {/* ── Header ── */}
        <motion.div variants={fadeUp} className="flex items-start justify-between mb-9">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="w-3 h-3 text-violet-400" />
              </motion.div>
              <span className="text-[.62rem] text-gray-500 font-bold uppercase tracking-[.2em]">
                لوحة التحكم الشخصية
              </span>
            </div>

            <h1 className="text-3xl md:text-[2.15rem] font-black leading-tight tracking-tight">
              مرحباً،{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-l from-violet-400 to-cyan-400">
                {firstName}
              </span>{" "}
              👋
            </h1>
            <p className="text-gray-500 text-sm mt-1.5">
              اختر الأداة التي تناسب احتياجك اليوم
            </p>
          </div>

          <div className="flex items-center gap-2.5 mt-1">
            <button className="relative w-9 h-9 rounded-xl bg-white/[.05] border border-white/[.07] flex items-center justify-center hover:bg-white/[.09] transition-colors">
              <Bell className="w-4 h-4 text-gray-400" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-pink-500 rounded-full border border-[#0b0f1a]" />
            </button>
            <Link to="/dashboard/profile">
              <motion.div
                whileHover={{ scale: 1.06 }}
                className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center font-black text-sm border-2 border-violet-500/40 shadow-[0_0_20px_rgba(99,102,241,.35)] cursor-pointer select-none"
              >
                {firstName[0]}
              </motion.div>
            </Link>
          </div>
        </motion.div>

        {/* ── Stats ── */}
        <motion.div variants={fadeUp} className="grid grid-cols-3 gap-3 mb-8">
          {STATS.map((s, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -3 }}
              className="flex items-center gap-3 bg-white/[.04] border border-white/[.07] rounded-2xl px-4 py-3.5 hover:shadow-lg transition-shadow"
            >
              <span className="text-2xl leading-none">{s.emoji}</span>
              <div>
                <p className="text-[.68rem] text-gray-500 leading-none mb-1">{s.label}</p>
                <p className={`text-[1.6rem] font-black leading-none ${s.vc}`}>{s.val}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* ── Slider ── */}
        <motion.div variants={fadeUp} className="mb-8">
          {/* Section header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="block w-4 h-[2px] bg-violet-500 rounded" />
              <span className="text-[.62rem] font-bold uppercase tracking-[.2em] text-gray-500">
                الخدمات المتاحة
              </span>
            </div>
            <div className="flex gap-1.5">
              <button
                onClick={() => goTo(current - 1)}
                disabled={current === 0}
                className="w-8 h-8 rounded-xl bg-white/[.05] border border-white/[.07] flex items-center justify-center hover:bg-violet-600 hover:border-violet-600 disabled:opacity-25 disabled:pointer-events-none transition-all"
              >
                <ChevronLeft className="w-[14px] h-[14px]" />
              </button>
              <button
                onClick={() => goTo(current + 1)}
                disabled={current >= maxSlide}
                className="w-8 h-8 rounded-xl bg-white/[.05] border border-white/[.07] flex items-center justify-center hover:bg-violet-600 hover:border-violet-600 disabled:opacity-25 disabled:pointer-events-none transition-all"
              >
                <ChevronRight className="w-[14px] h-[14px]" />
              </button>
            </div>
          </div>

          {/* Track */}
          <div
            ref={wrapRef}
            className="overflow-hidden rounded-2xl"
            onTouchStart={(e) => { touchX.current = e.touches[0].clientX; }}
            onTouchEnd={(e) => {
              const diff = touchX.current - e.changedTouches[0].clientX;
              if (Math.abs(diff) > 48) goTo(current + (diff > 0 ? 1 : -1));
            }}
          >
            <div
              className="flex gap-4 transition-transform duration-[520ms] ease-[cubic-bezier(.25,.46,.45,.94)]"
              style={{ transform: `translateX(${current * cardW}px)` }}
            >
              {SERVICES.map((svc, i) => (
                <Link
                  key={i}
                  to={svc.href}
                  style={{
                    flex: `0 0 calc(${100 / vis}% - ${(16 * (vis - 1)) / vis}px)`,
                  }}
                  className={`group block bg-white/[.04] border border-white/[.07] rounded-2xl p-5 transition-all duration-300 ${svc.borderHover} ${svc.shadowHover} hover:-translate-y-1.5`}
                >
                  {/* Top */}
                  <div className="flex items-start justify-between mb-5">
                    <motion.div
                      whileHover={{ rotate: 10, scale: 1.07 }}
                      className={`w-12 h-12 rounded-xl bg-gradient-to-br ${svc.gradient} flex items-center justify-center text-xl shadow-lg`}
                    >
                      {svc.emoji}
                    </motion.div>
                    <span className="text-[.58rem] font-bold tracking-widest text-gray-600 bg-white/[.04] border border-white/[.07] px-2 py-0.5 rounded-full">
                      {svc.badge}
                    </span>
                  </div>

                  <p className="font-black text-[1.05rem] text-white mb-0.5">
                    {svc.title}
                  </p>
                  <p className={`text-xs font-semibold mb-3 ${svc.accent}`}>{svc.titleAr}</p>
                  <p className="text-gray-500 text-[.8rem] leading-relaxed mb-5">{svc.desc}</p>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-3.5 border-t border-white/[.06]">
                    <span className="text-sm text-gray-300 font-semibold">{svc.cta}</span>
                    <div
                      className={`w-7 h-7 rounded-lg bg-gradient-to-br ${svc.gradient} flex items-center justify-center transition-transform group-hover:-translate-x-1`}
                    >
                      <ArrowLeft className="w-3.5 h-3.5 text-white" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Dots */}
          <div className="flex justify-center gap-1.5 mt-4">
            {Array.from({ length: maxSlide + 1 }).map((_, i) => (
              <button
                key={i}
                onClick={() => goTo(i)}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === current ? "w-5 bg-violet-500" : "w-1.5 bg-white/[.12]"
                }`}
              />
            ))}
          </div>
        </motion.div>

        {/* ── Bottom Grid ── */}
        <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Progress */}
          <div className="bg-white/[.04] border border-white/[.07] rounded-2xl p-5">
            <div className="flex items-center justify-between mb-5">
              <p className="text-sm font-bold flex items-center gap-2">
                <Activity className="w-4 h-4 text-violet-400" />
                اكتمال ملفك الشخصي
              </p>
              <span className="text-[.62rem] text-gray-600">4 خطوات</span>
            </div>
            <div className="flex flex-col gap-[18px]">
              {PROGRESS.map((p, i) => (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-gray-400">{p.label}</span>
                    <span className="text-white font-bold">{p.pct}%</span>
                  </div>
                  <div className="h-[5px] rounded-full bg-white/[.06] overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${p.pct}%` }}
                      transition={{ duration: 1.4, delay: i * 0.14, ease: "easeOut" }}
                      className={`h-full rounded-full bg-gradient-to-r ${p.bar}`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tip */}
          <div className="bg-gradient-to-br from-amber-500/[.08] to-orange-500/[.04] border border-amber-500/20 rounded-2xl p-5 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-500/15 flex items-center justify-center">
                <Lightbulb className="w-4 h-4 text-amber-400" />
              </div>
              <p className="text-sm font-bold text-amber-400">نصيحة اليوم</p>
            </div>
            <p className="text-gray-400 text-[.82rem] leading-[1.75]">
              السير الذاتية التي تحتوي على كلمات مفتاحية من وصف الوظيفة تحصل على فرصة مقابلة
              أعلى بـ 3 أضعاف. خصّص سيرتك لكل وظيفة تتقدم إليها!
            </p>
            <Link
              to="/dashboard/jobs"
              className="self-start text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/25 rounded-xl px-4 py-2 hover:bg-amber-500/20 transition-colors"
            >
              جرّب Job Matcher ←
            </Link>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}