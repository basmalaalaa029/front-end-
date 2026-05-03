import { useState, useRef } from "react";
import {
  Plus, Trash2, Download, Save, Eye, ChevronDown, Loader2,
  FileText, Briefcase, BookOpen, Zap, Globe, Copy, Check
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useReactToPrint } from "react-to-print";
import { toast } from "react-hot-toast";
import api from "../lib/api";
import type { CVData } from "../types";
import { CVPreview } from "../components/CVPreview";

export default function CVEditorPage() {
  const [activeTab, setActiveTab] = useState<"personal" | "experience" | "education" | "skills" | "languages">("personal");
  const [loadingSave, setLoadingSave] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const [cvData, setCvData] = useState<CVData>({
    personalInfo: {
      name: "",
      email: "",
      phone: "",
      summary: "",
      address: "",
      linkedin: "",
      github: "",
    },
    experiences: [{ company: "", role: "", duration: "", description: "" }],
    education: [{ institution: "", degree: "", year: "" }],
    skills: [{ name: "", level: "Intermediate" }],
    languages: [{ name: "", proficiency: "Fluent" }],
  });

  const previewRef = useRef<HTMLDivElement>(null);
  const handlePrint = useReactToPrint({
    contentRef: previewRef,
    documentTitle: `${cvData.personalInfo.name || "CV"}_Resume`,
  });

  const handleSave = async () => {
    setLoadingSave(true);
    try {
      await api.post("/cv/save", cvData);
      toast.success("✅ تم حفظ السيرة الذاتية بنجاح!");
    } catch (error) {
      toast.error("❌ حدث خطأ أثناء الحفظ");
    } finally {
      setLoadingSave(false);
    }
  };

  const updatePersonalInfo = (field: string, value: string) => {
    setCvData((prev) => ({
      ...prev,
      personalInfo: { ...prev.personalInfo, [field]: value },
    }));
  };

  const updateArrayItem = (section: keyof CVData, index: number, field: string, value: string) => {
    setCvData((prev) => {
      const arr = [...(prev[section] as any[])];
      arr[index] = { ...arr[index], [field]: value };
      return { ...prev, [section]: arr };
    });
  };

  const addArrayItem = (section: keyof CVData, emptyItem: any) => {
    setCvData((prev) => ({
      ...prev,
      [section]: [...(prev[section] as any[]), emptyItem],
    }));
  };

  const removeArrayItem = (section: keyof CVData, index: number) => {
    setCvData((prev) => ({
      ...prev,
      [section]: (prev[section] as any[]).filter((_, i) => i !== index),
    }));
  };

  const TabButton = ({ id, label, icon }: { id: any; label: string; icon: React.ReactNode }) => (
    <motion.button
      onClick={() => setActiveTab(id)}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`px-4 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2 ${
        activeTab === id
          ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/30"
          : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/10"
      }`}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </motion.button>
  );

  const FormGroup = ({
    label,
    value,
    onChange,
    type = "text",
    placeholder,
  }: {
    label: string;
    value: string;
    onChange: (value: string) => void;
    type?: string;
    placeholder?: string;
  }) => (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1.5">{label}</label>
      {type === "textarea" ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-[#0d0e18] border border-white/10 rounded-xl p-3 text-white outline-none focus:border-violet-500 transition-all resize-none focus:ring-2 focus:ring-violet-500/20"
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-[#0d0e18] border border-white/10 rounded-xl p-3 text-white outline-none focus:border-violet-500 transition-all focus:ring-2 focus:ring-violet-500/20"
        />
      )}
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="pb-16 min-h-screen bg-gradient-to-br from-[#07080f] via-[#0a0b15] to-[#07080f]"
      dir="rtl"
    >
      <div className="max-w-[1600px] mx-auto p-6 md:p-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row items-center justify-between gap-6 mb-10"
        >
          <div>
            <h1 className="text-4xl md:text-5xl font-black text-white mb-2">محرّر السيرة الذاتية</h1>
            <p className="text-gray-400">
              أنشئ سيرة ذاتية احترافية محسّنة للـ ATS بسهولة
            </p>
          </div>

          <div className="flex gap-3 flex-wrap md:flex-nowrap">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSave}
              disabled={loadingSave}
              className="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white transition-all disabled:opacity-50"
            >
              {loadingSave ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Save className="w-5 h-5" />
              )}
              <span>حفظ</span>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handlePrint()}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 rounded-xl text-white font-bold transition-all shadow-lg shadow-violet-500/25"
            >
              <Download className="w-5 h-5" />
              <span>تحميل PDF</span>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowPreview(!showPreview)}
              className="md:hidden flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white transition-all"
            >
              <Eye className="w-5 h-5" />
              <span>عرض</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Main Grid */}
        <div className="grid lg:grid-cols-[1fr_600px] xl:grid-cols-[1fr_900px] gap-8">
          {/* Editor Side */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="space-y-6 flex flex-col"
          >
            {/* Tabs */}
            <div className="flex gap-2 p-1.5 bg-white/5 rounded-2xl overflow-x-auto hide-scrollbar border border-white/10">
              <TabButton
                id="personal"
                label="المعلومات"
                icon={<FileText className="w-4 h-4" />}
              />
              <TabButton
                id="experience"
                label="الخبرات"
                icon={<Briefcase className="w-4 h-4" />}
              />
              <TabButton
                id="education"
                label="التعليم"
                icon={<BookOpen className="w-4 h-4" />}
              />
              <TabButton
                id="skills"
                label="المهارات"
                icon={<Zap className="w-4 h-4" />}
              />
              <TabButton
                id="languages"
                label="اللغات"
                icon={<Globe className="w-4 h-4" />}
              />
            </div>

            {/* Form Area */}
            <div className="flex-1 glass-card p-8 rounded-3xl border border-white/10">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-6"
                >
                  {/* Personal Info */}
                  {activeTab === "personal" && (
                    <motion.div variants={{ container: { staggerChildren: 0.05 } }} initial="hidden" animate="visible" className="space-y-5">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <motion.div variants={{ item: { opacity: 0, y: 10 } }} initial="hidden" animate="visible">
                          <FormGroup
                            label="الاسم الكامل"
                            value={cvData.personalInfo.name}
                            onChange={(val) => updatePersonalInfo("name", val)}
                            placeholder="محمد أحمد"
                          />
                        </motion.div>
                        <motion.div variants={{ item: { opacity: 0, y: 10 } }} initial="hidden" animate="visible">
                          <FormGroup
                            label="المهنة / التخصص"
                            value={cvData.personalInfo.name}
                            onChange={(val) => updatePersonalInfo("name", val)}
                            placeholder="Senior Software Engineer"
                          />
                        </motion.div>
                        <motion.div variants={{ item: { opacity: 0, y: 10 } }} initial="hidden" animate="visible">
                          <FormGroup
                            label="البريد الإلكتروني"
                            type="email"
                            value={cvData.personalInfo.email}
                            onChange={(val) => updatePersonalInfo("email", val)}
                            placeholder="your@email.com"
                          />
                        </motion.div>
                        <motion.div variants={{ item: { opacity: 0, y: 10 } }} initial="hidden" animate="visible">
                          <FormGroup
                            label="رقم الهاتف"
                            type="tel"
                            value={cvData.personalInfo.phone}
                            onChange={(val) => updatePersonalInfo("phone", val)}
                            placeholder="+966 50 0000000"
                          />
                        </motion.div>
                        <motion.div variants={{ item: { opacity: 0, y: 10 } }} initial="hidden" animate="visible">
                          <FormGroup
                            label="العنوان"
                            value={cvData.personalInfo.address}
                            onChange={(val) => updatePersonalInfo("address", val)}
                            placeholder="الرياض، المملكة العربية السعودية"
                          />
                        </motion.div>
                        <motion.div variants={{ item: { opacity: 0, y: 10 } }} initial="hidden" animate="visible">
                          <FormGroup
                            label="رابط LinkedIn"
                            type="url"
                            value={cvData.personalInfo.linkedin}
                            onChange={(val) => updatePersonalInfo("linkedin", val)}
                            placeholder="linkedin.com/in/yourprofile"
                          />
                        </motion.div>
                      </div>
                      <motion.div variants={{ item: { opacity: 0, y: 10 } }} initial="hidden" animate="visible">
                        <FormGroup
                          label="نبذة تعريفية (Summary)"
                          type="textarea"
                          value={cvData.personalInfo.summary}
                          onChange={(val) => updatePersonalInfo("summary", val)}
                          placeholder="اكتب نبذة مختصرة عن نفسك وخبراتك..."
                        />
                      </motion.div>
                    </motion.div>
                  )}

                  {/* Experience */}
                  {activeTab === "experience" && (
                    <div className="space-y-6">
                      {cvData.experiences.map((exp, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-4 relative group hover:border-violet-500/50 transition-all"
                        >
                          <motion.button
                            whileHover={{ scale: 1.2, rotate: 90 }}
                            onClick={() => removeArrayItem("experiences", idx)}
                            className="absolute left-6 top-6 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all bg-white/5 p-2 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4" />
                          </motion.button>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormGroup
                              label="المسمى الوظيفي"
                              value={exp.role}
                              onChange={(val) => updateArrayItem("experiences", idx, "role", val)}
                              placeholder="Senior Developer"
                            />
                            <FormGroup
                              label="الشركة"
                              value={exp.company}
                              onChange={(val) => updateArrayItem("experiences", idx, "company", val)}
                              placeholder="اسم الشركة"
                            />
                            <div className="md:col-span-2">
                              <FormGroup
                                label="الفترة الزمنية"
                                value={exp.duration}
                                onChange={(val) => updateArrayItem("experiences", idx, "duration", val)}
                                placeholder="Jan 2020 - Present"
                              />
                            </div>
                            <div className="md:col-span-2">
                              <FormGroup
                                label="الوصف والإنجازات"
                                type="textarea"
                                value={exp.description}
                                onChange={(val) => updateArrayItem("experiences", idx, "description", val)}
                                placeholder="اكتب عن مسؤولياتك والإنجازات التي حققتها..."
                              />
                            </div>
                          </div>
                        </motion.div>
                      ))}

                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() =>
                          addArrayItem("experiences", {
                            company: "",
                            role: "",
                            duration: "",
                            description: "",
                          })
                        }
                        className="w-full py-4 border-2 border-dashed border-white/20 hover:border-violet-500 hover:bg-violet-500/10 rounded-2xl text-violet-400 font-bold transition-all flex justify-center items-center gap-2"
                      >
                        <Plus className="w-5 h-5" /> إضافة خبرة جديدة
                      </motion.button>
                    </div>
                  )}

                  {/* Education */}
                  {activeTab === "education" && (
                    <div className="space-y-6">
                      {cvData.education.map((edu, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-4 relative group hover:border-violet-500/50 transition-all"
                        >
                          <motion.button
                            whileHover={{ scale: 1.2, rotate: 90 }}
                            onClick={() => removeArrayItem("education", idx)}
                            className="absolute left-6 top-6 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all bg-white/5 p-2 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4" />
                          </motion.button>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormGroup
                              label="الدرجة العلمية"
                              value={edu.degree}
                              onChange={(val) => updateArrayItem("education", idx, "degree", val)}
                              placeholder="Bachelor of Computer Science"
                            />
                            <FormGroup
                              label="المؤسسة التعليمية"
                              value={edu.institution}
                              onChange={(val) => updateArrayItem("education", idx, "institution", val)}
                              placeholder="اسم الجامعة"
                            />
                            <div className="md:col-span-2">
                              <FormGroup
                                label="سنة التخرج"
                                value={edu.year}
                                onChange={(val) => updateArrayItem("education", idx, "year", val)}
                                placeholder="2023"
                              />
                            </div>
                          </div>
                        </motion.div>
                      ))}

                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => addArrayItem("education", { institution: "", degree: "", year: "" })}
                        className="w-full py-4 border-2 border-dashed border-white/20 hover:border-violet-500 hover:bg-violet-500/10 rounded-2xl text-violet-400 font-bold transition-all flex justify-center items-center gap-2"
                      >
                        <Plus className="w-5 h-5" /> إضافة تعليم جديد
                      </motion.button>
                    </div>
                  )}

                  {/* Skills */}
                  {activeTab === "skills" && (
                    <div className="space-y-4">
                      {cvData.skills.map((skill, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="flex gap-3"
                        >
                          <input
                            type="text"
                            value={skill.name}
                            onChange={(e) => updateArrayItem("skills", idx, "name", e.target.value)}
                            placeholder="المهارة (React, Node.js, ...)"
                            className="flex-1 bg-[#0d0e18] border border-white/10 rounded-xl p-3 text-white focus:border-violet-500 outline-none transition-all"
                          />
                          <select
                            value={skill.level}
                            onChange={(e) => updateArrayItem("skills", idx, "level", e.target.value)}
                            className="w-32 bg-[#0d0e18] border border-white/10 rounded-xl p-3 text-gray-300 focus:border-violet-500 outline-none transition-all"
                          >
                            <option>Beginner</option>
                            <option>Intermediate</option>
                            <option>Advanced</option>
                            <option>Expert</option>
                          </select>
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            onClick={() => removeArrayItem("skills", idx)}
                            className="p-3 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-xl transition-all"
                          >
                            <Trash2 className="w-4 h-4" />
                          </motion.button>
                        </motion.div>
                      ))}

                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => addArrayItem("skills", { name: "", level: "Intermediate" })}
                        className="w-full py-4 border-2 border-dashed border-white/20 hover:border-violet-500 hover:bg-violet-500/10 rounded-2xl text-violet-400 font-bold transition-all flex justify-center items-center gap-2"
                      >
                        <Plus className="w-5 h-5" /> إضافة مهارة
                      </motion.button>
                    </div>
                  )}

                  {/* Languages */}
                  {activeTab === "languages" && (
                    <div className="space-y-4">
                      {cvData.languages.map((lang, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="flex gap-3"
                        >
                          <input
                            type="text"
                            value={lang.name}
                            onChange={(e) => updateArrayItem("languages", idx, "name", e.target.value)}
                            placeholder="اللغة"
                            className="flex-1 bg-[#0d0e18] border border-white/10 rounded-xl p-3 text-white focus:border-violet-500 outline-none transition-all"
                          />
                          <select
                            value={lang.proficiency}
                            onChange={(e) => updateArrayItem("languages", idx, "proficiency", e.target.value)}
                            className="w-32 bg-[#0d0e18] border border-white/10 rounded-xl p-3 text-gray-300 focus:border-violet-500 outline-none transition-all"
                          >
                            <option>Basic</option>
                            <option>Conversational</option>
                            <option>Fluent</option>
                            <option>Native</option>
                          </select>
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            onClick={() => removeArrayItem("languages", idx)}
                            className="p-3 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-xl transition-all"
                          >
                            <Trash2 className="w-4 h-4" />
                          </motion.button>
                        </motion.div>
                      ))}

                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => addArrayItem("languages", { name: "", proficiency: "Fluent" })}
                        className="w-full py-4 border-2 border-dashed border-white/20 hover:border-violet-500 hover:bg-violet-500/10 rounded-2xl text-violet-400 font-bold transition-all flex justify-center items-center gap-2"
                      >
                        <Plus className="w-5 h-5" /> إضافة لغة
                      </motion.button>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Preview Side */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className={`hidden lg:flex flex-col h-[calc(100vh-180px)] sticky top-20 ${
              showPreview ? "block" : ""
            }`}
          >
            <div className="absolute top-0 inset-x-0 h-4 bg-gradient-to-b from-[#07080f] to-transparent z-10" />
            <div className="absolute bottom-0 inset-x-0 h-4 bg-gradient-to-t from-[#07080f] to-transparent z-10" />

            <div className="flex-1 overflow-y-auto hide-scrollbar rounded-3xl border border-white/10 shadow-2xl bg-white relative">
              <div className="scale-[0.75] xl:scale-[0.9] origin-top">
                <CVPreview data={cvData} ref={previewRef} />
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}