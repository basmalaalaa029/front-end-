import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/features/auth/stores/auth-store";

/* ============================
   Icons
============================ */
const IconGrid = () => (
  <svg className="w-[15px] h-[15px]" viewBox="0 0 16 16" fill="none">
    <rect x="1" y="1" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.8" />
    <rect x="9" y="1" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.4" />
    <rect x="1" y="9" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.4" />
    <rect x="9" y="9" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.6" />
  </svg>
);

const IconBriefcase = () => (
  <svg className="w-[15px] h-[15px]" viewBox="0 0 16 16" fill="none">
    <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.3" />
    <path d="M5 7h6M5 10h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
  </svg>
);

const IconCV = () => (
  <svg className="w-[15px] h-[15px]" viewBox="0 0 16 16" fill="none">
    <path
      d="M3 2h10a1 1 0 011 1v10a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z"
      stroke="currentColor"
      strokeWidth="1.3"
    />
    <path d="M5 6h6M5 9h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
  </svg>
);

const IconMenu = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const IconClose = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const IconLogout = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
);

const IconLogin = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
);

/* ============================
   NAV ITEMS - تظهر دائماً
============================ */
const NAV_ITEMS = [
  { key: "home", label: "الرئيسية", path: "/", icon: <IconGrid /> },
  { key: "dashboard", label: "لوحة التحكم", path: "/dashboard", icon: <IconBriefcase /> },
  { key: "cv", label: "الـ CV", path: "/cv", icon: <IconCV /> },
];
/* ============================
   Navbar
============================ */
export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  
  // ✅ اقرأ كل الـ state من الـ store
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const logout = useAuthStore((state) => state.logout);

  // ✅ تحميل البيانات من localStorage عند بدء الـ component
 

  // ✅ Debug: اطبع الـ user في الـ console
  useEffect(() => {
    console.log("🔐 User state updated:", user);
    console.log("🔑 Token:", token ? "✅ Present" : "❌ Missing");
    console.log("🔥 NAVBAR USER:", user);
  }, [user, token]);

  // ✅ إغلاق الـ dropdowns عند تغيير الصفحة
  useEffect(() => {
    setProfileOpen(false);
    setMobileOpen(false);
  }, [location.pathname]);

  // ✅ Helper functions
  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    setMobileOpen(false);
    setProfileOpen(false);
  };

  const handleLogout = () => {
    logout();
    setProfileOpen(false);
    setMobileOpen(false);
    navigate("/");
  };

  // ✅ منع الـ click من إغلاق الـ dropdown
  const handleDropdownClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  // ✅ إغلاق الـ dropdown عند الـ click خارجه
  useEffect(() => {
    const handleClickOutside = () => {
      setProfileOpen(false);
    };

    if (profileOpen) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [profileOpen]);

  return (
    <nav
      dir="rtl"
      className="flex items-center gap-2 h-[60px] px-5 bg-white border border-black/10 rounded-2xl shadow-md font-sans relative z-40"
    >
      {/* Logo */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => handleNavigate("/")}
        className="flex items-center gap-2 ml-2 shrink-0 transition group"
      >
        <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center shadow-md group-hover:shadow-lg transition">
          <svg className="w-[18px] h-[18px]" viewBox="0 0 18 18" fill="none">
            <path
              d="M3 14l4-7 3 4 2-3 3 6"
              stroke="white"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="14" cy="4" r="2" fill="white" opacity="0.8" />
          </svg>
        </div>
        <span className="text-[20px] font-bold text-gray-900 tracking-tight hidden sm:inline">
          CV <span className="text-blue-600">CAREER</span>
        </span>
      </motion.button>

      {/* Divider */}
      <div className="w-px h-5 bg-black/10 mx-2 hidden sm:block" />

      {/* Desktop Nav - تظهر دائماً */}
      <div className="hidden sm:flex items-center gap-1 flex-1">
        {NAV_ITEMS.map((item) => (
          <motion.button
            key={item.key}
            whileHover={{ backgroundColor: "#f3f4f6" }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleNavigate(item.path)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition
              ${isActive(item.path)
                ? "text-blue-600 bg-blue-50 shadow-sm"
                : "text-gray-500 hover:text-gray-900"}
            `}
          >
            {item.icon}
            <span>{item.label}</span>
          </motion.button>
        ))}
      </div>

      {/* Spacer */}
      <div className="flex-1 hidden sm:block" />

      {/* Right Section */}
      <div className="flex items-center gap-3 ml-auto shrink-0 relative">
        {user ? (
          // ✅ لما يكون مسجل دخول
          <>
            {/* User Name - إظهار إضافي */}
            <div className="hidden md:block text-right border-r border-gray-200 pr-3">
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm font-semibold text-gray-900 truncate"
              >
                {user.name}
              </motion.p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>

            {/* Avatar Button */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
              onClick={(e) => {
                e.stopPropagation();
                setProfileOpen(!profileOpen);
              }}
              className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-sm font-bold border-2 border-black/10 transition hover:shadow-lg hover:border-black/20 relative"
              title={user.name}
            >
              <motion.div
                animate={{ scale: profileOpen ? 1.2 : 1 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                {user.name?.charAt(0).toUpperCase() || "U"}
              </motion.div>
            </motion.button>

            {/* Animated Dropdown */}
            <AnimatePresence>
              {profileOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.15, type: "spring", stiffness: 300 }}
                  onClick={handleDropdownClick}
                  className="absolute left-0 top-14 w-60 bg-white border border-black/10 rounded-xl shadow-xl overflow-hidden z-50 backdrop-blur-sm"
                >
                  {/* Header with user info */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-100"
                  >
                    <p className="text-sm font-bold text-gray-900">{user.name}</p>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </motion.div>

                  {/* Menu Items */}
                  <div className="p-2 space-y-1">
                    {[
                      {
                        icon: <IconBriefcase />,
                        label: "لوحة التحكم",
                        path: "/dashboard",
                      },
                      {
                        icon: <IconCV />,
                        label: "الـ CV",
                        path: "/cv",
                      },
                    ].map((item, idx) => (
                      <motion.button
                        key={idx}
                        whileHover={{ backgroundColor: "#f3f4f6", x: -4 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleNavigate(item.path)}
                        className="w-full text-right px-3 py-2 text-sm text-gray-700 hover:text-blue-600 transition rounded-lg flex items-center gap-3 justify-end"
                      >
                        {item.label}
                        {item.icon}
                      </motion.button>
                    ))}

                    <motion.div
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      className="h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent my-2 origin-right"
                    />

                    <motion.button
                      whileHover={{ backgroundColor: "#fef2f2", x: -4 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleLogout}
                      className="w-full text-right px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 transition rounded-lg flex items-center gap-3 justify-end font-medium"
                    >
                      تسجيل الخروج
                      <IconLogout />
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        ) : (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleNavigate("/login")}
            className="px-4 py-2 text-blue-600 border border-blue-600 rounded-lg text-sm font-semibold hover:bg-blue-50 transition flex items-center gap-2"
          >
            <span>تسجيل الدخول</span>
            <IconLogin />
          </motion.button>
        )}
      </div>

      {/* Mobile Menu Button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setMobileOpen(!mobileOpen)}
        className="sm:hidden text-gray-600 hover:text-gray-900 transition"
      >
        {mobileOpen ? <IconClose /> : <IconMenu />}
      </motion.button>

      {/* Mobile Menu - تظهر دائماً */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 bg-white border border-black/10 rounded-2xl mt-2 overflow-hidden sm:hidden shadow-lg z-40"
          >
            <div className="flex flex-col p-2 space-y-1">
              {/* User info في Mobile */}
              {user && (
                <>
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="px-3 py-2 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg"
                  >
                    <p className="text-sm font-bold text-gray-900">{user.name}</p>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </motion.div>
                  <div className="h-2" />
                </>
              )}

              {/* Nav Items */}
              {NAV_ITEMS.map((item, idx) => (
                <motion.button
                  key={item.key}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  whileHover={{ backgroundColor: "#f3f4f6", x: -4 }}
                  onClick={() => handleNavigate(item.path)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition text-right w-full
                    ${isActive(item.path)
                      ? "text-blue-600 bg-blue-50 shadow-sm"
                      : "text-gray-600 hover:text-gray-900"}
                  `}
                >
                  <span>{item.label}</span>
                  {item.icon}
                </motion.button>
              ))}

              {/* Logout/Login في Mobile */}
              {user ? (
                <>
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    className="h-px bg-gray-200 my-2 origin-right"
                  />
                  <motion.button
                    whileHover={{ backgroundColor: "#fef2f2", x: -4 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleLogout}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-red-500 w-full text-right hover:bg-red-50 transition"
                  >
                    <span>تسجيل الخروج</span>
                    <IconLogout />
                  </motion.button>
                </>
              ) : (
                <>
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    className="h-px bg-gray-200 my-2 origin-right"
                  />
                  <motion.button
                    whileHover={{ backgroundColor: "#eff6ff", x: -4 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleNavigate("/login")}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-blue-600 w-full text-right hover:bg-blue-50 transition"
                  >
                    <span>تسجيل الدخول</span>
                    <IconLogin />
                  </motion.button>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}