/**
 * pages/HomePage.tsx
 * Premium landing page for the Personal Finance Spend Auditor.
 *
 * Design tokens: uses the existing index.css utility classes
 *  (os-card, os-inner-panel, glass-panel, typo-*, mesh-blob, bg-noise,
 *   animate-float, animate-fade-up-*, text-gradient-blue)
 *
 * No backend dependency — renders entirely from static/mock data.
 * Auth routes (/login, /signup) and protected routes are untouched.
 */

import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  RefreshCw,
  EyeOff,
  BarChart2,
  Lightbulb,
  ShieldCheck,
  Lock,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  Zap,
  Upload,
  Search,
  Sparkles,
  ChevronRight,
} from 'lucide-react'
import {
  LineChart,
  Line,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'

// ---------------------------------------------------------------------------
// Static mock data for dashboard preview cards
// ---------------------------------------------------------------------------
const spendTrend = [
  { v: 38000 }, { v: 41000 }, { v: 39500 }, { v: 44000 },
  { v: 40000 }, { v: 43200 }, { v: 42680 },
]

const savingsTrend = [
  { v: 1200 }, { v: 1800 }, { v: 1500 }, { v: 2200 },
  { v: 2600 }, { v: 2900 }, { v: 3200 },
]

const recentTransactions = [
  { name: 'Netflix', category: 'Entertainment', amount: -649, date: 'Sep 1' },
  { name: 'Swiggy', category: 'Food & Dining', amount: -340, date: 'Sep 2' },
  { name: 'Spotify Premium', category: 'Subscriptions', amount: -119, date: 'Sep 3' },
]

// ---------------------------------------------------------------------------
// Small reusable helpers
// ---------------------------------------------------------------------------
function formatINR(n: number): string {
  const abs = Math.abs(n)
  if (abs >= 100000) return `₹${(abs / 100000).toFixed(1)}L`
  if (abs >= 1000) return `₹${(abs / 1000).toFixed(1)}k`
  return `₹${abs.toLocaleString('en-IN')}`
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Top floating nav — mirrors the authenticated Navbar style */
function LandingNav() {
  return (
    <nav
      className="fixed top-4 inset-x-0 z-50 flex justify-center pointer-events-none"
      aria-label="Main navigation"
    >
      <motion.div
        initial={{ y: -24, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', damping: 28, stiffness: 220, delay: 0.1 }}
        className="glass-panel rounded-full px-2 py-1.5 flex items-center gap-1 shadow-[0_8px_32px_-8px_rgba(0,0,0,0.8)] pointer-events-auto"
      >
        {/* Logo mark */}
        <div className="flex items-center gap-2 pl-3 pr-5 border-r border-white/5">
          <div className="h-4 w-4 rounded-full bg-gradient-to-tr from-blue-400 to-cyan-400 shadow-[0_0_14px_rgba(96,165,250,0.5)]" />
          <span className="typo-badge text-[10px] text-white">Auditor</span>
        </div>

        {/* Nav links */}
        <div className="hidden sm:flex items-center px-3 gap-0.5">
          {['Features', 'How it works', 'Security'].map((label) => (
            <a
              key={label}
              href={`#${label.toLowerCase().replace(/\s+/g, '-')}`}
              className="px-3 py-1.5 typo-badge text-[9px] text-gray-500 hover:text-gray-200 transition-colors rounded-full hover:bg-white/5"
            >
              {label}
            </a>
          ))}
        </div>

        {/* Auth actions */}
        <div className="flex items-center gap-1 pl-3 pr-1 border-l border-white/5">
          <Link
            to="/login"
            className="px-3 py-1.5 typo-badge text-[9px] text-gray-400 hover:text-white transition-colors rounded-full hover:bg-white/5"
          >
            Sign in
          </Link>
          <Link
            to="/signup"
            id="nav-cta"
            className="px-3 py-1.5 typo-badge text-[9px] text-white bg-blue-500/90 hover:bg-blue-500 rounded-full transition-all shadow-[0_0_16px_rgba(59,130,246,0.3)] hover:shadow-[0_0_20px_rgba(59,130,246,0.45)]"
          >
            Get Started
          </Link>
        </div>
      </motion.div>
    </nav>
  )
}

/** Abstract dashboard preview — bento grid of real-looking UI cards */
function DashboardPreview() {
  return (
    <div
      className="relative w-full max-w-2xl mx-auto animate-fade-up-5"
      aria-hidden="true"
    >
      {/* Outer glow */}
      <div className="absolute inset-0 rounded-[28px] bg-blue-500/5 blur-3xl scale-95 pointer-events-none" />

      <div
        className="relative rounded-[24px] border border-white/[0.06] bg-[#0b0d12] p-4 shadow-[0_32px_80px_-16px_rgba(0,0,0,0.9)]"
        style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 32px 80px -16px rgba(0,0,0,0.9)' }}
      >
        {/* Preview header bar */}
        <div className="flex items-center justify-between mb-4 px-1">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-gradient-to-tr from-blue-400 to-cyan-400 shadow-[0_0_8px_rgba(96,165,250,0.4)]" />
            <span className="typo-badge text-[9px] text-white/40">Finance Auditor — Overview</span>
          </div>
          <div className="flex gap-1.5">
            <div className="h-2 w-2 rounded-full bg-white/10" />
            <div className="h-2 w-2 rounded-full bg-white/10" />
            <div className="h-2 w-2 rounded-full bg-white/10" />
          </div>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-12 gap-3">

          {/* Monthly Spending — wide */}
          <div className="col-span-12 sm:col-span-7 os-inner-panel p-4 animate-float">
            <div className="flex items-center justify-between mb-3">
              <p className="typo-subheading">Monthly Spending</p>
              <span className="flex items-center gap-1 text-[9px] font-semibold text-red-400/80 bg-red-400/10 px-2 py-0.5 rounded-full">
                <ArrowUpRight className="h-2.5 w-2.5" />+4.2%
              </span>
            </div>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-[28px] font-semibold tracking-[-0.04em] text-white tabular-nums leading-none">
                  ₹42,680
                </p>
                <p className="typo-caption mt-1 text-gray-600">this month</p>
              </div>
              <div className="h-10 w-28 opacity-60">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={spendTrend}>
                    <defs>
                      <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="v"
                      stroke="#3b82f6"
                      strokeWidth={1.5}
                      fill="url(#spendGrad)"
                      dot={false}
                      isAnimationActive={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recurring Subscriptions */}
          <div className="col-span-12 sm:col-span-5 os-inner-panel p-4 animate-float-delayed">
            <div className="flex items-center gap-2 mb-3">
              <RefreshCw className="h-3 w-3 text-blue-400" />
              <p className="typo-subheading">Recurring</p>
            </div>
            <p className="text-[22px] font-semibold tracking-[-0.04em] text-white tabular-nums leading-none">
              ₹8,420
            </p>
            <p className="typo-caption mt-1 text-gray-600">/ month · 14 subscriptions</p>
            <div className="mt-3 flex gap-1 flex-wrap">
              {['Netflix', 'Spotify', 'AWS', '+11'].map((s) => (
                <span
                  key={s}
                  className="px-1.5 py-0.5 rounded-full text-[8px] font-semibold bg-blue-500/10 text-blue-400/80 border border-blue-500/15"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>

          {/* Invisible Spend */}
          <div className="col-span-6 sm:col-span-4 os-inner-panel p-4">
            <div className="flex items-center gap-1.5 mb-3">
              <EyeOff className="h-3 w-3 text-amber-400" />
              <p className="typo-subheading text-amber-500/60">Invisible</p>
            </div>
            <p className="text-[18px] font-semibold tracking-[-0.03em] text-white tabular-nums">
              ₹14,280
            </p>
            <p className="typo-caption mt-0.5 text-gray-600">/ year</p>
          </div>

          {/* Potential Savings */}
          <div className="col-span-6 sm:col-span-4 os-inner-panel p-4">
            <div className="flex items-center gap-1.5 mb-3">
              <TrendingUp className="h-3 w-3 text-emerald-400" />
              <p className="typo-subheading text-emerald-500/60">Savings</p>
            </div>
            <p className="text-[18px] font-semibold tracking-[-0.03em] text-emerald-400 tabular-nums">
              ₹9,840
            </p>
            <p className="typo-caption mt-0.5 text-gray-600">potential / year</p>
          </div>

          {/* Insight */}
          <div className="col-span-12 sm:col-span-4 os-inner-panel p-4 flex items-start gap-2">
            <div className="mt-0.5 h-5 w-5 shrink-0 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <Zap className="h-2.5 w-2.5 text-blue-400" />
            </div>
            <div>
              <p className="typo-heading text-[10px] text-white/80 leading-snug">
                You spent ₹1,240 on unused subscriptions last quarter.
              </p>
              <p className="typo-caption mt-1 text-blue-400/70">
                Tap to review →
              </p>
            </div>
          </div>

          {/* Recent transactions */}
          <div className="col-span-12 os-inner-panel p-4">
            <p className="typo-subheading mb-3">Recent Transactions</p>
            <div className="flex flex-col gap-2">
              {recentTransactions.map((tx) => (
                <div key={tx.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 rounded-full bg-white/5 border border-white/[0.06] flex items-center justify-center">
                      <span className="text-[8px] font-semibold text-gray-500">
                        {tx.name[0]}
                      </span>
                    </div>
                    <div>
                      <p className="typo-heading text-[10px] text-white/70">{tx.name}</p>
                      <p className="typo-caption text-[9px] text-gray-600">{tx.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] font-semibold tabular-nums text-red-400/80">
                      {formatINR(tx.amount)}
                    </p>
                    <p className="typo-caption text-[9px] text-gray-600">{tx.date}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Savings sparkline */}
          <div className="col-span-12 os-inner-panel p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="typo-subheading">Savings Trend</p>
              <span className="flex items-center gap-1 text-[9px] font-semibold text-emerald-400/80">
                <ArrowDownRight className="h-2.5 w-2.5 rotate-180" />
                +₹2,000 vs last month
              </span>
            </div>
            <div className="h-12">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={savingsTrend}>
                  <Line
                    type="monotone"
                    dataKey="v"
                    stroke="#34d399"
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Feature card
// ---------------------------------------------------------------------------
interface FeatureCardProps {
  icon: React.ElementType
  title: string
  description: string
  delay: string
}

function FeatureCard({ icon: Icon, title, description, delay }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1], delay: parseFloat(delay) }}
      className="os-inner-panel p-6 flex gap-4 items-start group hover:border-blue-500/20 border border-white/[0.02] transition-all duration-300 rounded-[16px]"
    >
      <div className="mt-0.5 h-8 w-8 shrink-0 rounded-xl bg-blue-500/8 border border-blue-500/15 flex items-center justify-center group-hover:bg-blue-500/12 transition-colors">
        <Icon className="h-4 w-4 text-blue-400" />
      </div>
      <div>
        <h3 className="typo-heading text-sm text-white/90 mb-1.5">{title}</h3>
        <p className="typo-body text-gray-500 leading-relaxed">{description}</p>
      </div>
    </motion.div>
  )
}

// ---------------------------------------------------------------------------
// Step
// ---------------------------------------------------------------------------
interface StepProps {
  number: string
  title: string
  description: string
  icon: React.ElementType
  isLast?: boolean
}

function Step({ number, title, description, icon: Icon, isLast = false }: StepProps) {
  return (
    <div className="flex flex-col items-center text-center relative">
      {/* Connector line */}
      {!isLast && (
        <div className="hidden md:block absolute top-6 left-1/2 w-full h-px bg-gradient-to-r from-white/5 via-white/8 to-white/5 translate-x-8" />
      )}
      <div className="relative z-10 h-12 w-12 rounded-2xl bg-[#0e1015] border border-white/[0.07] flex items-center justify-center shadow-[0_4px_16px_-4px_rgba(0,0,0,0.6)] mb-5 group-hover:border-blue-500/20 transition-colors">
        <Icon className="h-5 w-5 text-blue-400" />
      </div>
      <span className="typo-badge text-[9px] text-blue-500/60 mb-2 tracking-[0.12em]">{number}</span>
      <h3 className="typo-heading text-[13px] text-white/90 mb-2">{title}</h3>
      <p className="typo-body text-gray-500 max-w-[200px] leading-relaxed">{description}</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Trust badge
// ---------------------------------------------------------------------------
function TrustBadge({ icon: Icon, text }: { icon: React.ElementType; text: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 h-5 w-5 shrink-0 rounded-full bg-white/5 border border-white/8 flex items-center justify-center">
        <Icon className="h-2.5 w-2.5 text-gray-400" />
      </div>
      <p className="typo-body text-gray-500 text-[12px] leading-snug">{text}</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function HomePage() {
  const howItWorksRef = useRef<HTMLElement>(null)

  return (
    <div className="relative min-h-screen bg-[#060709] text-white overflow-x-hidden">

      {/* ── Ambient background ────────────────────────────────── */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden" aria-hidden="true">
        {/* Blue ambient blob */}
        <div
          className="absolute top-[-15%] right-[-5%] w-[55%] h-[55%] rounded-full mesh-blob"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)' }}
        />
        {/* Subtle teal blob */}
        <div
          className="absolute bottom-[10%] left-[-10%] w-[45%] h-[45%] rounded-full mesh-blob"
          style={{
            background: 'radial-gradient(circle, rgba(34,211,238,0.04) 0%, transparent 70%)',
            animationDelay: '-7s',
          }}
        />
        {/* Noise overlay */}
        <div className="absolute inset-0 bg-noise" />
      </div>

      <LandingNav />

      {/* ── HERO ──────────────────────────────────────────────── */}
      <section
        className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 pt-24 pb-16 text-center"
        aria-labelledby="hero-headline"
      >
        {/* Eyebrow */}
        <div className="animate-fade-up mb-6">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/20 bg-blue-500/5 typo-badge text-[9px] text-blue-400/80 tracking-[0.12em]">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse" />
            PERSONAL FINANCE INTELLIGENCE
          </span>
        </div>

        {/* Headline */}
        <h1
          id="hero-headline"
          className="animate-fade-up-1 text-gradient-blue font-semibold tracking-[-0.04em] leading-[1.05] max-w-3xl mx-auto"
          style={{ fontSize: 'clamp(2.5rem, 7vw, 5rem)' }}
        >
          Know where your money&nbsp;
          <br className="hidden sm:block" />
          actually goes.
        </h1>

        {/* Subtext */}
        <p className="animate-fade-up-2 mt-6 typo-body text-gray-400 text-[15px] max-w-xl mx-auto leading-relaxed">
          Upload your bank statement and uncover recurring charges, forgotten subscriptions,
          spending patterns, and invisible costs — all in one place.
        </p>

        {/* CTAs */}
        <div className="animate-fade-up-3 mt-10 flex flex-col sm:flex-row items-center gap-3">
          <Link
            to="/signup"
            id="hero-cta-primary"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-semibold text-white bg-blue-500 hover:bg-blue-600 transition-all shadow-[0_0_24px_rgba(59,130,246,0.35)] hover:shadow-[0_0_32px_rgba(59,130,246,0.5)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            aria-label="Start auditing your finances"
          >
            Start Auditing
            <ChevronRight className="h-4 w-4" />
          </Link>
          <a
            href="#how-it-works"
            id="hero-cta-secondary"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-medium text-gray-400 hover:text-white border border-white/10 hover:border-white/20 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
            aria-label="See how the auditor works"
          >
            See how it works
          </a>
        </div>

        {/* Trust indicator */}
        <div className="animate-fade-up-4 mt-6 flex items-center gap-2 text-gray-600">
          <Lock className="h-3 w-3" />
          <span className="text-[11px] font-medium tracking-[-0.01em]">
            Your financial data stays private.
          </span>
        </div>

        {/* Dashboard preview */}
        <div className="animate-fade-up-5 w-full max-w-2xl mx-auto mt-16">
          <DashboardPreview />
        </div>

        {/* Scroll fade at bottom */}
        <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#060709] to-transparent" aria-hidden="true" />
      </section>

      {/* ── WHAT YOU GET ──────────────────────────────────────── */}
      <section
        id="features"
        className="relative z-10 px-4 py-24"
        aria-labelledby="features-heading"
      >
        <div className="max-w-4xl mx-auto">
          {/* Section label */}
          <div className="text-center mb-14">
            <span className="typo-badge text-[9px] text-blue-500/60 tracking-[0.12em]">WHAT YOU GET</span>
            <h2
              id="features-heading"
              className="mt-3 text-[clamp(1.6rem,4vw,2.5rem)] font-semibold tracking-[-0.03em] text-white/90"
            >
              Built for clarity, not complexity.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FeatureCard
              icon={RefreshCw}
              title="Find recurring charges"
              description="Automatically identify subscriptions and repeated merchant payments across your transaction history."
              delay="0"
            />
            <FeatureCard
              icon={EyeOff}
              title="Detect invisible spending"
              description="See how small recurring expenses quietly compound into significant amounts over months and years."
              delay="0.08"
            />
            <FeatureCard
              icon={BarChart2}
              title="Understand your spending"
              description="Turn raw bank transactions into meaningful categories, patterns, and trends you can actually act on."
              delay="0.16"
            />
            <FeatureCard
              icon={Lightbulb}
              title="Make better decisions"
              description="Get actionable recommendations based on your real transaction data — not generic financial advice."
              delay="0.24"
            />
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ──────────────────────────────────────── */}
      <section
        id="how-it-works"
        ref={howItWorksRef}
        className="relative z-10 px-4 py-24 hairline-t hairline-b"
        aria-labelledby="how-it-works-heading"
      >
        {/* Subtle horizontal divider */}
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <span className="typo-badge text-[9px] text-blue-500/60 tracking-[0.12em]">THE PROCESS</span>
            <h2
              id="how-it-works-heading"
              className="mt-3 text-[clamp(1.6rem,4vw,2.5rem)] font-semibold tracking-[-0.03em] text-white/90"
            >
              Three steps to financial&nbsp;clarity.
            </h2>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6 }}
            className="relative grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-6"
          >
            <Step
              number="01"
              title="Upload"
              description="Upload your bank statement as a CSV file. No account linking required."
              icon={Upload}
            />
            <Step
              number="02"
              title="Analyze"
              description="The system categorizes and analyzes your transactions automatically."
              icon={Search}
            />
            <Step
              number="03"
              title="Discover"
              description="Find subscriptions, anomalies, recurring expenses, and potential savings."
              icon={Sparkles}
              isLast
            />
          </motion.div>
        </div>
      </section>

      {/* ── SECURITY ──────────────────────────────────────────── */}
      <section
        id="security"
        className="relative z-10 px-4 py-24"
        aria-labelledby="security-heading"
      >
        <div className="max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-40px' }}
            transition={{ duration: 0.6 }}
            className="os-card p-10 md:p-14 relative overflow-hidden"
          >
            {/* Subtle inner glow */}
            <div
              className="absolute -top-16 -right-16 w-48 h-48 rounded-full blur-3xl pointer-events-none opacity-40"
              style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)' }}
              aria-hidden="true"
            />

            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-6">
                <ShieldCheck className="h-5 w-5 text-blue-400" />
                <span className="typo-badge text-[9px] text-blue-500/60 tracking-[0.12em]">PRIVACY &amp; SECURITY</span>
              </div>
              <h2
                id="security-heading"
                className="text-[clamp(1.4rem,3vw,2rem)] font-semibold tracking-[-0.03em] text-white/90 mb-8"
              >
                Built for your financial privacy.
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <TrustBadge icon={Lock} text="Secure authentication with JWT tokens." />
                <TrustBadge icon={ShieldCheck} text="All API communication is protected." />
                <TrustBadge icon={EyeOff} text="We never sell or share your financial data." />
                <TrustBadge icon={BarChart2} text="Deterministic calculations — no AI-invented numbers." />
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── FINAL CTA ─────────────────────────────────────────── */}
      <section
        className="relative z-10 px-4 py-28 text-center"
        aria-labelledby="final-cta-heading"
      >
        {/* Ambient glow under CTA */}
        <div
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[40%] h-40 blur-3xl pointer-events-none opacity-30"
          style={{ background: 'radial-gradient(ellipse, rgba(59,130,246,0.2) 0%, transparent 70%)' }}
          aria-hidden="true"
        />
        <div className="relative z-10 max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          >
            <h2
              id="final-cta-heading"
              className="text-[clamp(2rem,5vw,3.5rem)] font-semibold tracking-[-0.04em] text-gradient-blue leading-[1.1]"
            >
              Your spending tells a story.
              <br />
              <span className="text-white/50">Let's make it useful.</span>
            </h2>
            <p className="mt-5 typo-body text-gray-500 text-[14px] max-w-md mx-auto">
              Join others who've already uncovered thousands in unnecessary charges.
            </p>
            <div className="mt-10">
              <Link
                to="/signup"
                id="final-cta-btn"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full text-sm font-semibold text-white bg-blue-500 hover:bg-blue-600 transition-all shadow-[0_0_32px_rgba(59,130,246,0.4)] hover:shadow-[0_0_40px_rgba(59,130,246,0.55)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                aria-label="Start auditing your finances now"
              >
                Start Auditing
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── FOOTER ────────────────────────────────────────────── */}
      <footer
        className="relative z-10 px-4 py-10 hairline-t"
        aria-label="Site footer"
      >
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
          {/* Brand */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 rounded-full bg-gradient-to-tr from-blue-400 to-cyan-400 shadow-[0_0_10px_rgba(96,165,250,0.4)]" />
              <span className="typo-badge text-[10px] text-white">Finance Auditor</span>
            </div>
            <p className="typo-caption text-gray-600 max-w-[220px]">
              Personal finance intelligence for the self-aware spender.
            </p>
          </div>

          {/* Links */}
          <nav aria-label="Footer navigation" className="flex flex-wrap gap-x-6 gap-y-3">
            {[
              { label: 'Privacy', href: '#security' },
              { label: 'Security', href: '#security' },
              { label: 'Sign in', href: '/login' },
              { label: 'Get Started', href: '/signup' },
            ].map(({ label, href }) => (
              href.startsWith('/') ? (
                <Link
                  key={label}
                  to={href}
                  className="typo-caption text-gray-600 hover:text-gray-300 transition-colors"
                >
                  {label}
                </Link>
              ) : (
                <a
                  key={label}
                  href={href}
                  className="typo-caption text-gray-600 hover:text-gray-300 transition-colors"
                >
                  {label}
                </a>
              )
            ))}
          </nav>

          {/* Copyright */}
          <p className="typo-caption text-gray-700 shrink-0">
            © {new Date().getFullYear()} Finance Auditor
          </p>
        </div>
      </footer>

    </div>
  )
}
