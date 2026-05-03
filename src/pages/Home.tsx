import React from 'react';
import { 
  Search, 
  Sparkles, 
  FileText, 
  Briefcase, 
  TrendingUp, 
  CheckCircle,
  ArrowRight,
  Globe,
  Zap,
  Star,
  Users,
  Award
} from 'lucide-react';
import { motion } from 'framer-motion';
import Footer from '../components/layout/Footer';

const HomePage = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  };

  const features = [
    {
      icon: <FileText size={32} />,
      title: "تحليل الـ CV الذكي",
      desc: "ارفع سيرتك الذاتية وسيقوم الـ AI بتحليلها ومطابقتها مع أفضل الوظائف",
      color: "from-blue-500 to-cyan-500",
      bgColor: "bg-blue-50"
    },
    {
      icon: <Zap size={32} />,
      title: "توصيات فورية",
      desc: "نظامنا يتعلم من اهتماماتك ليقدم لك قائمة وظائف مخصصة",
      color: "from-purple-500 to-pink-500",
      bgColor: "bg-purple-50"
    },
    {
      icon: <TrendingUp size={32} />,
      title: "متابعة الطلبات",
      desc: "لوحة تحكم ذكية تتيح لك تتبع حالة طلبات التوظيف",
      color: "from-emerald-500 to-green-500",
      bgColor: "bg-emerald-50"
    }
  ];

  const categories = [
    'التطوير والبرمجة',
    'التسويق الرقمي',
    'التصميم الإبداعي',
    'إدارة المشاريع',
    'البيانات والـ AI',
    'المبيعات',
    'الموارد البشرية',
    'الخدمة اللوجستية'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white text-right" dir="rtl">
      
      {/* Hero Section */}
      <motion.section 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="relative pt-20 pb-32 overflow-hidden"
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full -z-10">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="absolute top-10 left-10 w-72 h-72 bg-blue-100 rounded-full blur-3xl opacity-30"
          />
          <motion.div 
            animate={{ rotate: -360 }}
            transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            className="absolute bottom-10 right-10 w-96 h-96 bg-indigo-100 rounded-full blur-3xl opacity-30"
          />
        </div>

        <div className="container mx-auto px-6 text-center">
          <motion.div 
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 px-4 py-1.5 rounded-full text-sm font-bold mb-6 border border-blue-200"
          >
            <Sparkles size={16} className="animate-spin" /> مدعوم بأحدث تقنيات الذكاء الاصطناعي
          </motion.div>

          <motion.h1 
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            className="text-5xl md:text-7xl font-extrabold text-slate-900 mb-6 leading-tight"
          >
            ابنِ مسارك المهني <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-l from-blue-600 to-indigo-600">بذكاء واحترافية</span>
          </motion.h1>

          <motion.p 
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            className="text-xl text-slate-600 mb-10 max-w-3xl mx-auto leading-relaxed"
          >
            المنصة المتكاملة لإدارة وظائفك، تحليل سيرتك الذاتية، والحصول على اقتراحات ذكية تسرّع وصولك للوظيفة التي تستحقها.
          </motion.p>

          {/* Smart Search Bar */}
          <motion.div 
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            className="max-w-4xl mx-auto bg-white p-2 rounded-2xl shadow-2xl border border-gray-200 flex flex-col md:flex-row items-center gap-2"
          >
            <div className="flex items-center w-full px-4 border-l border-gray-200">
              <Search className="text-gray-400 ml-3" size={20} />
              <input 
                type="text" 
                placeholder="المسمى الوظيفي، مهارة..." 
                className="w-full py-4 outline-none bg-transparent text-right" 
              />
            </div>
            <div className="flex items-center w-full px-4 border-l border-gray-200">
              <Globe className="text-gray-400 ml-3" size={20} />
              <input 
                type="text" 
                placeholder="المدينة، أو عن بعد" 
                className="w-full py-4 outline-none bg-transparent text-right" 
              />
            </div>
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="w-full md:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-10 py-4 rounded-xl font-bold hover:shadow-lg transition-all"
            >
              بحث
            </motion.button>
          </motion.div>
        </div>
      </motion.section>

      {/* Features Section */}
      <motion.section 
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-24 bg-white"
      >
        <div className="container mx-auto px-6">
          <motion.div variants={itemVariants} className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">لماذا تختار منصتنا الذكية؟</h2>
            <p className="text-slate-600 text-lg">نحن ندمج التكنولوجيا مع إدارة المسيرة المهنية لتقديم تجربة فريدة</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <motion.div
                key={idx}
                variants={itemVariants}
                whileHover={{ y: -10 }}
                className="group bg-white p-8 rounded-2xl border border-gray-200 hover:shadow-2xl transition-all duration-300"
              >
                <motion.div 
                  className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mb-6 text-white`}
                  whileHover={{ rotate: 10, scale: 1.1 }}
                >
                  {feature.icon}
                </motion.div>
                <h3 className="text-xl font-bold mb-3 text-slate-900">{feature.title}</h3>
                <p className="text-slate-600 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Stats Section */}
      <motion.section 
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-24 bg-gradient-to-r from-blue-600 to-indigo-600 text-white"
      >
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            {[
              { icon: <Users size={32} />, num: "50K+", text: "مستخدم نشط" },
              { icon: <Briefcase size={32} />, num: "10K+", text: "وظيفة متاحة" },
              { icon: <Award size={32} />, num: "95%", text: "معدل النجاح" }
            ].map((stat, idx) => (
              <motion.div 
                key={idx}
                variants={itemVariants}
                className="flex flex-col items-center"
              >
                <motion.div 
                  whileHover={{ scale: 1.2, rotate: 10 }}
                  className="mb-4"
                >
                  {stat.icon}
                </motion.div>
                <div className="text-4xl font-bold mb-2">{stat.num}</div>
                <p className="text-blue-100">{stat.text}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Categories Section */}
      <motion.section 
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-24 bg-slate-50"
      >
        <div className="container mx-auto px-6">
          <div className="flex justify-between items-end mb-12">
            <div className="text-right">
              <h2 className="text-3xl font-bold text-slate-900 mb-2">استكشف بالمجالات</h2>
              <p className="text-slate-600">أكثر المجالات طلباً هذا الشهر</p>
            </div>
            <motion.button 
              whileHover={{ gap: "12px" }}
              className="text-blue-600 font-bold flex items-center gap-2 hover:text-blue-700"
            >
              عرض كل المجالات <ArrowRight size={20} className="rotate-180" />
            </motion.button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {categories.map((cat, i) => (
              <motion.div
                key={i}
                variants={itemVariants}
                whileHover={{ scale: 1.05, y: -5 }}
                className="p-6 border border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition text-center font-bold text-slate-700 bg-white"
              >
                {cat}
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section 
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="container mx-auto px-6 mb-24"
      >
        <div className="bg-gradient-to-r from-slate-900 to-blue-900 rounded-3xl p-12 text-white relative overflow-hidden flex flex-col md:flex-row items-center justify-between">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
            className="absolute -right-20 -top-20 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"
          />
          
          <div className="relative z-10 md:w-2/3 text-center md:text-right">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">جاهز لخطوتك القادمة في مسارك المهني؟</h2>
            <p className="text-blue-200 text-lg mb-8">سجل الآن مجاناً وابدأ في تجربة طريقة التوظيف الذكية.</p>
            <div className="flex flex-col md:flex-row gap-4 justify-center md:justify-start">
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="bg-blue-600 text-white px-8 py-4 rounded-xl font-bold hover:bg-blue-700 transition shadow-lg"
              >
                أنشئ حسابك الآن
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="bg-white/10 text-white border border-white/20 px-8 py-4 rounded-xl font-bold hover:bg-white/20 transition"
              >
                تحدث مع خبير مهني
              </motion.button>
            </div>
          </div>
        </div>
      </motion.section> 
    </div>
  );
};

export default HomePage;