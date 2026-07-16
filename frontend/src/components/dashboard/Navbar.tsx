import { Search, Bell, Settings } from "lucide-react"
import { motion } from "framer-motion"
import { useNavigate, useLocation } from "react-router-dom"

export function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()

  const tabs = [
    { name: "Overview", path: "/dashboard" },
    { name: "Cash Flow", path: "/transactions" },
    { name: "Intelligence", path: "/analytics" },
    { name: "Import", path: "/import" },
    { name: "Goals", path: "#" }
  ]

  // Find active tab based on current path
  const activeTab = tabs.find(t => location.pathname === t.path)?.name || "Overview"

  return (
    <nav className="fixed top-4 inset-x-0 z-50 flex justify-center pointer-events-none">
      <motion.div 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="glass-panel rounded-full px-2 py-1.5 flex items-center shadow-[0_8px_32px_-8px_rgba(0,0,0,0.8)] pointer-events-auto transition-all hover:bg-white/[0.02]"
      >
        
        {/* Logo */}
        <div className="flex items-center gap-2 pl-3 pr-5 border-r border-white/5 cursor-pointer" onClick={() => navigate("/dashboard")}>
          <div className="h-4 w-4 bg-gradient-to-tr from-emerald-400 to-cyan-400 rounded-full shadow-[0_0_15px_rgba(52,211,153,0.4)]" />
          <span className="typo-badge text-[10px] text-white">Auditor</span>
        </div>

        {/* Links */}
        <div className="hidden md:flex items-center px-3 gap-0.5">
          {tabs.map((tab) => (
            <button
              key={tab.name}
              onClick={() => {
                if (tab.path !== "#") {
                  navigate(tab.path)
                }
              }}
              className={`relative px-4 py-1.5 typo-badge text-[9px] transition-colors rounded-full ${
                activeTab === tab.name ? "text-white" : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {activeTab === tab.name && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-white/5 border border-white/10 rounded-full shadow-inner"
                  transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
                />
              )}
              <span className="relative z-10">{tab.name}</span>
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 pl-3 pr-1 border-l border-white/5">
          <button className="p-1.5 text-gray-500 hover:text-white hover:bg-white/5 rounded-full transition-all">
            <Search className="h-3.5 w-3.5" />
          </button>
          <button className="p-1.5 text-gray-500 hover:text-white hover:bg-white/5 rounded-full transition-all relative">
            <Bell className="h-3.5 w-3.5" />
            <span className="absolute top-1 right-1 flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500 shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
            </span>
          </button>
          <button className="p-1.5 text-gray-500 hover:text-white hover:bg-white/5 rounded-full transition-all" onClick={() => {
            // Quick logout via settings button or similar, or just leave as placeholder
            if (confirm("Are you sure you want to log out?")) {
              localStorage.removeItem("access_token");
              navigate("/login");
            }
          }}>
            <Settings className="h-3.5 w-3.5" />
          </button>
        </div>

      </motion.div>
    </nav>
  )
}

