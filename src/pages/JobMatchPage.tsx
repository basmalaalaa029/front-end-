import { useState } from "react";
import api from "../lib/api";
import { 
  Briefcase, FileText, Send, Sparkles, Loader2, Copy, 
  CheckCircle2, AlertCircle, TrendingUp, Zap
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface MatchResult {
  matchScore: number;
  overlapTerms: string[];
  missingInCV: string[];
}

export default function JobMatchPage() {
  const [cvText, setCvText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MatchResult | null>(null);
  const [copied, setCopied] = useState(false);

  const handleMatch = async () => {
    if (!cvText || !jobDescription) return;
    setLoading(true);
    try {
      const res = await api.post("/cv/match", { cvText, jobDescription });
      setResult(res.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setCvText("");
    setJobDescription("");
    setResult(null);
  };

  const scoreColor = (score: number) =>
    score >= 75 ? "from-emerald-500 to-teal-500"
    : score >= 50 ? "from-amber-500 to-orange-500"
    : "from-red-500 to-pink-500";

  const scoreLabel = (score: number) =>
    score >= 75 ? "توافق ممتاز! 🎯"
    : score >= 50 ? "توافق جيد - يحتاج تحسين"
    : "توافق ضعيف - تحتاج تعديلات كبيرة";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="pb-16 min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50"
      dir="rtl"
    >
      <div className="max-w-[1400px] mx-auto p-6 md:p-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="text-xs text-emerald-600 font-semibold uppercase tracking-widest bg-emerald-100 px-3 py-1 rounded-full">
              مطابق ذكي
            </span>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 4, repeat: Infinity }}
            >
              <Zap className="w-4 h-4 text-emerald-600" />
            </motion.div>
          </div>
          <h1 className="text-5xl md:text-6xl font-black text-gray-900 mb-3">
            Job Matcher
          </h1>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            قارن سيرتك الذاتية مع أي وصف وظيفي واحصل على نسبة التطابق الدقيقة 
            والتوصيات المخصصة لتحسين فرصك.
          </p>
        </motion.div>

        {/* Main Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Input Side */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="md:col-span-2 space-y-6"
          >
            {/* CV Text Area */}
            <motion.div
              whileHover={{ y: -5 }}
              className="rounded-3xl border border-gray-200 bg-white overflow-hidden shadow-lg"
            >
              <div className="bg-gradient-to-r from-violet-50 to-indigo-50 px-6 py-4 border-b border-gray-200 flex items-center gap-3">
                <FileText className="w-5 h-5 text-violet-600" />
                <label className="text-sm font-bold text-gray-900">
                  نص السيرة الذاتية
                </label>
              </div>
              <textarea
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                placeholder="الصق نص سيرتك الذاتية هنا... (يمكنك نسخ النص من أي ملف CV)"
                className="w-full h-56 p-6 text-gray-700 outline-none resize-none focus:ring-2 focus:ring-violet-500/20 transition-all"
              />
            </motion.div>

            {/* Job Description Text Area */}
            <motion.div
              whileHover={{ y: -5 }}
              className="rounded-3xl border border-gray-200 bg-white overflow-hidden shadow-lg"
            >
              <div className="bg-gradient-to-r from-emerald-50 to-teal-50 px-6 py-4 border-b border-gray-200 flex items-center gap-3">
                <Briefcase className="w-5 h-5 text-emerald-600" />
                <label className="text-sm font-bold text-gray-900">
                  وصف الوظيفة (Job Description)
                </label>
              </div>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="الصق وصف الوظيفة المستهدفة هنا... (يمكنك نسخه من إعلان التوظيف)"
                className="w-full h-56 p-6 text-gray-700 outline-none resize-none focus:ring-2 focus:ring-emerald-500/20 transition-all"
              />
            </motion.div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleMatch}
                disabled={loading || !cvText || !jobDescription}
                className="flex-1 flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    جاري المطابقة...
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-5 h-5" />
                    تحليل المطابقة
                  </>
                )}
              </motion.button>

              {(cvText || jobDescription) && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleReset}
                  className="px-6 py-4 border border-gray-300 bg-white hover:bg-gray-50 rounded-xl font-bold text-gray-700 transition-all"
                >
                  إعادة تعيين
                </motion.button>
              )}
            </div>
          </motion.div>

          {/* Score Card - Right Side */}
          <AnimatePresence>
            {result ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="rounded-3xl bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 p-8 flex flex-col items-center justify-center text-center h-fit sticky top-10"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 rounded-3xl opacity-5 border-4 border-violet-500"
                />

                <p className="text-xs text-gray-600 uppercase tracking-widest font-bold mb-4 relative z-10">
                  نسبة التطابق
                </p>

                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", stiffness: 100 }}
                  className="relative z-10"
                >
                  <div className={`text-7xl font-black bg-gradient-to-r ${scoreColor(result.matchScore)} bg-clip-text text-transparent mb-4`}>
                    {result.matchScore}%
                  </div>
                </motion.div>

                <motion.span
                  animate={{ y: [0, -5, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-lg font-bold text-gray-700 mb-8 relative z-10"
                >
                  {scoreLabel(result.matchScore)}
                </motion.span>

                <div className="w-full h-3 rounded-full bg-gray-300 overflow-hidden relative z-10 mb-6">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${result.matchScore}%` }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className={`h-full bg-gradient-to-r ${scoreColor(result.matchScore)}`}
                  />
                </div>

                {result.matchScore >= 75 ? (
                  <motion.p className="text-sm text-emerald-600 font-medium relative z-10">
                    ✅ فرصتك قوية جداً في هذه الوظيفة!
                  </motion.p>
                ) : (
                  <motion.p className="text-sm text-amber-600 font-medium relative z-10">
                    ⚠️ نصيحة: أضف الكلمات المفقودة لتحسين الفرصة
                  </motion.p>
                )}
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>

        {/* Results Details Section */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-10 grid md:grid-cols-2 gap-6"
            >
              {/* Overlap Terms */}
              {result.overlapTerms?.length > 0 && (
                <motion.div
                  whileHover={{ y: -5 }}
                  className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-teal-50 p-8"
                >
                  <div className="flex items-center gap-2 mb-6">
                    <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                    <h3 className="text-xl font-bold text-gray-900">
                      الكلمات المتطابقة
                    </h3>
                  </div>

                  <motion.div
                    className="flex flex-wrap gap-3"
                    variants={{ container: { staggerChildren: 0.05 } }}
                    initial="hidden"
                    animate="visible"
                  >
                    {result.overlapTerms.map((term: string, i: number) => (
                      <motion.button
                        key={i}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.1, y: -2 }}
                        onClick={() => handleCopy(term)}
                        className="rounded-lg border-2 border-emerald-300 bg-white px-4 py-2 text-sm font-medium text-emerald-700 shadow-sm hover:border-emerald-500 hover:bg-emerald-50 transition-all group relative"
                      >
                        {term}
                        <motion.div
                          initial={{ opacity: 0, scale: 0 }}
                          whileHover={{ opacity: 1, scale: 1 }}
                          className="absolute left-full ml-2 top-1/2 -translate-y-1/2"
                        >
                          <Copy className="w-4 h-4 text-emerald-600" />
                        </motion.div>
                      </motion.button>
                    ))}
                  </motion.div>

                  <p className="text-xs text-emerald-600 mt-4 font-medium">
                    ✓ هذه الكلمات موجودة في سيرتك والوظيفة - ممتاز!
                  </p>
                </motion.div>
              )}

              {/* Missing Terms */}
              {result.missingInCV?.length > 0 && (
                <motion.div
                  whileHover={{ y: -5 }}
                  className="rounded-2xl border border-red-200 bg-gradient-to-br from-red-50 to-orange-50 p-8"
                >
                  <div className="flex items-center gap-2 mb-6">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                    <h3 className="text-xl font-bold text-gray-900">
                      الكلمات المفقودة
                    </h3>
                  </div>

                  <motion.div
                    className="flex flex-wrap gap-3"
                    variants={{ container: { staggerChildren: 0.05 } }}
                    initial="hidden"
                    animate="visible"
                  >
                    {result.missingInCV.map((term: string, i: number) => (
                      <motion.button
                        key={i}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.1, y: -2 }}
                        onClick={() => handleCopy(term)}
                        className="rounded-lg border-2 border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 shadow-sm hover:border-red-500 hover:bg-red-50 transition-all group relative"
                      >
                        {term}
                        <motion.div
                          initial={{ opacity: 0, scale: 0 }}
                          whileHover={{ opacity: 1, scale: 1 }}
                          className="absolute left-full ml-2 top-1/2 -translate-y-1/2"
                        >
                          <Copy className="w-4 h-4 text-red-600" />
                        </motion.div>
                      </motion.button>
                    ))}
                  </motion.div>

                  <p className="text-xs text-red-600 mt-4 font-medium">
                    ⚠️ أضف هذه الكلمات في سيرتك لتحسين فرصتك
                  </p>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 20 }}
            className="mt-12 text-center p-12 rounded-3xl border-2 border-dashed border-gray-300"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
              className="inline-flex items-center justify-center w-16 h-16 bg-violet-100 rounded-2xl mb-4"
            >
              <Sparkles className="w-8 h-8 text-violet-600" />
            </motion.div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              جاهز للمطابقة الذكية؟
            </h3>
            <p className="text-gray-600 max-w-md mx-auto">
              أدخل نص السيرة الذاتية ووصف الوظيفة لبدء المطابقة الفورية واكتشف نسبة التطابق الدقيقة.
            </p>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}