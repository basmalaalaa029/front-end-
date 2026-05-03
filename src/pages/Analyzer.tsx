import { useState, useRef } from "react";
import api from "../lib/api";
import { 
  UploadCloud, FileText, Loader2, CheckCircle2, AlertCircle, 
  TrendingUp, Zap, Download, X, Copy, Share2, RefreshCw 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function Analyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);
  const [dragActive, setDragActive] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    if (selectedFile.type !== "application/pdf") {
      setError("يجب أن يكون الملف بصيغة PDF");
      return;
    }
    if (selectedFile.size > 5 * 1024 * 1024) {
      setError("حجم الملف يجب أن يكون أقل من 5MB");
      return;
    }
    setFile(selectedFile);
    setError("");
  };

  // Drag & Drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append("cv", file);

      // Upload
      const uploadRes = await api.post("/cv/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent: any) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
        },
      });

      setUploadProgress(100);

      // Analyze
      const cvId = uploadRes.data.data.cvId;
      const analyzeRes = await api.post("/cv/analyze", { cvId });
      setResult(analyzeRes.data.data);
    } catch (err: any) {
      setError(
        err.response?.data?.data?.message || "حدث خطأ أثناء التحليل."
      );
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const scoreColor = (s: number) =>
    s >= 80 ? "text-emerald-500" : s >= 60 ? "text-amber-500" : "text-red-500";

  const scoreGradient = (s: number) =>
    s >= 80
      ? "from-emerald-500 to-teal-500"
      : s >= 60
      ? "from-amber-500 to-orange-500"
      : "from-red-500 to-pink-500";

  const scoreLabel = (s: number) =>
    s >= 80
      ? "ممتاز جداً ✨"
      : s >= 60
      ? "جيد - يحتاج تحسين"
      : "يحتاج تحسين كبير";

  const handleCopyKeyword = (kw: string) => {
    navigator.clipboard.writeText(kw);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError("");
    setUploadProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="pb-16 min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50"
      dir="rtl"
    >
      <div className="max-w-[1200px] mx-auto p-6 md:p-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <div className="flex items-center justify-end gap-2 mb-3">
            <span className="text-xs text-violet-600 font-semibold uppercase tracking-widest bg-violet-100 px-3 py-1 rounded-full">
              أداة ذكية
            </span>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 4, repeat: Infinity }}
            >
              <Zap className="w-4 h-4 text-violet-600" />
            </motion.div>
          </div>
          <h1 className="text-5xl md:text-6xl font-black text-gray-900 mb-3">
            CV Analyzer
          </h1>
          <p className="text-gray-600 text-lg max-w-2xl">
            ارفع سيرتك الذاتية بصيغة PDF للحصول على تقييم ATS فوري، تحليل شامل، 
            وتوصيات مخصصة لتحسين فرصك في المقابلة.
          </p>
        </motion.div>

        {/* Main Container */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Upload Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="md:col-span-2"
          >
            <label className="block cursor-pointer h-full">
              <motion.div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                whileHover={{ borderColor: "rgb(99, 102, 241)" }}
                className={`flex flex-col items-center justify-center rounded-3xl border-2 border-dashed p-16 transition-all duration-300
                  ${
                    dragActive
                      ? "border-violet-500 bg-violet-100 scale-105"
                      : file
                      ? "border-violet-400 bg-violet-50"
                      : "border-gray-300 bg-gray-50 hover:bg-gray-100"
                  }`}
              >
                <motion.div
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 2.5, repeat: Infinity }}
                >
                  {file ? (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="text-violet-600 mb-4"
                    >
                      <FileText className="w-20 h-20" />
                    </motion.div>
                  ) : (
                    <motion.div
                      initial={{ y: 0 }}
                      animate={{ y: dragActive ? -10 : 0 }}
                    >
                      <UploadCloud className="w-20 h-20 text-gray-400 mb-4" />
                    </motion.div>
                  )}
                </motion.div>

                {file ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center"
                  >
                    <p className="font-bold text-gray-900 text-xl mb-2">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-600 mb-4">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                    <motion.span
                      animate={{ scale: [1, 1.05, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="inline-block text-sm text-violet-600 bg-violet-100 border border-violet-300 rounded-full px-4 py-2 font-medium"
                    >
                      ✓ جاهز للتحليل
                    </motion.span>
                  </motion.div>
                ) : (
                  <>
                    <p className="font-bold text-gray-900 text-xl mb-2">
                      اسحب الملف أو اضغط للاختيار
                    </p>
                    <p className="text-sm text-gray-600">
                      PDF فقط — الحد الأقصى 5MB
                    </p>
                  </>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </motion.div>
            </label>

            {/* Action Buttons */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: file ? 1 : 0.5 }}
              className="mt-6 flex gap-3"
            >
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleAnalyze}
                disabled={!file || loading}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl px-8 py-4 text-base font-bold text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-violet-600 to-indigo-600 hover:shadow-xl"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    جاري التحليل...
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-5 h-5" />
                    تشغيل التحليل
                  </>
                )}
              </motion.button>

              {file && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleReset}
                  className="px-4 py-4 rounded-xl border border-gray-300 bg-white hover:bg-gray-50 transition-all"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </motion.button>
              )}
            </motion.div>

            {/* Upload Progress */}
            <AnimatePresence>
              {loading && uploadProgress > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mt-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      جاري الرفع...
                    </span>
                    <span className="text-sm font-bold text-violet-600">
                      {uploadProgress}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      transition={{ ease: "easeOut" }}
                      className="h-full bg-gradient-to-r from-violet-600 to-indigo-600"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error Message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3"
                >
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">{error}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Score Card - Right Side */}
          <AnimatePresence>
            {result ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="rounded-3xl bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 p-8 flex flex-col items-center justify-center text-center h-full"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{
                    duration: 20,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                  className="absolute inset-0 rounded-3xl opacity-5 border-4 border-violet-500"
                />
                <p className="text-xs text-gray-600 uppercase tracking-widest font-bold mb-4 relative z-10">
                  درجة التطابق ATS
                </p>
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{
                    type: "spring",
                    stiffness: 100,
                    damping: 15,
                  }}
                  className="relative z-10"
                >
                  <div
                    className={`text-7xl font-black bg-gradient-to-r ${scoreGradient(
                      result.score
                    )} bg-clip-text text-transparent mb-4`}
                  >
                    {result.score}
                  </div>
                </motion.div>
                <motion.span
                  animate={{ y: [0, -5, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className={`text-lg font-bold ${scoreColor(
                    result.score
                  )} mb-8 relative z-10`}
                >
                  {scoreLabel(result.score)}
                </motion.span>
                <div className="w-full h-3 rounded-full bg-gray-300 overflow-hidden relative z-10">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${result.score}%` }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className={`h-full bg-gradient-to-r ${scoreGradient(
                      result.score
                    )}`}
                  />
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>

        {/* Results Section */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-10 space-y-6"
            >
              {/* Missing Keywords */}
              {result.missingKeywords?.length > 0 && (
                <motion.div
                  whileHover={{ y: -5 }}
                  className="rounded-2xl border border-red-200 bg-gradient-to-br from-red-50 to-orange-50 p-8"
                >
                  <div className="flex items-center gap-2 mb-6">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                    <h3 className="text-xl font-bold text-gray-900">
                      الكلمات المفقودة الرئيسية
                    </h3>
                  </div>
                  <motion.div
                    className="flex flex-wrap gap-3"
                    variants={{
                      container: { staggerChildren: 0.05 },
                    }}
                    initial="hidden"
                    animate="visible"
                  >
                    {result.missingKeywords.map((kw: string, i: number) => (
                      <motion.button
                        key={i}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.08, y: -2 }}
                        onClick={() => handleCopyKeyword(kw)}
                        className="rounded-lg border-2 border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 shadow-sm hover:border-red-500 hover:bg-red-50 transition-all group relative"
                      >
                        {kw}
                        <motion.div
                          initial={{ opacity: 0, scale: 0 }}
                          whileHover={{ opacity: 1, scale: 1 }}
                          className="absolute right-full mr-2 top-1/2 -translate-y-1/2"
                        >
                          <Copy className="w-4 h-4 text-red-600" />
                        </motion.div>
                      </motion.button>
                    ))}
                  </motion.div>
                </motion.div>
              )}

              {/* Suggestions */}
              {result.suggestions?.length > 0 && (
                <motion.div
                  whileHover={{ y: -5 }}
                  className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-teal-50 p-8"
                >
                  <div className="flex items-center gap-2 mb-6">
                    <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                    <h3 className="text-xl font-bold text-gray-900">
                      توصيات التحسين
                    </h3>
                  </div>
                  <ul className="space-y-4">
                    {result.suggestions?.map((sug: string, i: number) => (
                      <motion.li
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex gap-4 items-start justify-end group"
                      >
                        <span className="text-sm text-gray-700 leading-relaxed flex-1">
                          {sug}
                        </span>
                        <motion.span
                          whileHover={{
                            scale: 1.2,
                            rotate: 360,
                          }}
                          className="h-8 w-8 rounded-full border-2 border-emerald-500 bg-emerald-100 flex items-center justify-center flex-shrink-0 text-xs font-bold text-emerald-600"
                        >
                          {i + 1}
                        </motion.span>
                      </motion.li>
                    ))}
                  </ul>
                </motion.div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 flex items-center justify-center gap-2 rounded-xl px-6 py-4 bg-gradient-to-r from-violet-600 to-indigo-600 text-white font-bold hover:shadow-lg transition-all"
                >
                  <Download className="w-5 h-5" />
                  تحميل التقرير
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center justify-center gap-2 px-6 py-4 rounded-xl border border-gray-300 bg-white hover:bg-gray-50 font-bold text-gray-700 transition-all"
                >
                  <Share2 className="w-5 h-5" />
                  مشاركة
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleReset}
                  className="flex items-center justify-center gap-2 px-6 py-4 rounded-xl border border-gray-300 bg-white hover:bg-gray-50 font-bold text-gray-700 transition-all"
                >
                  <RefreshCw className="w-5 h-5" />
                  تحليل جديد
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}