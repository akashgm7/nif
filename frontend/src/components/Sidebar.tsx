"use client"

import React from 'react'
import { 
  LayoutDashboard, 
  Search, 
  History, 
  BarChart3, 
  Settings, 
  Bot,
  Zap,
  ShieldCheck
} from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const Sidebar = () => {
  const pathname = usePathname()

  const menuItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/' },
    { name: 'Market Scanner', icon: Search, path: '/scanner' },
    { name: 'Signal History', icon: History, path: '/history' },
    { name: 'Backtester', icon: Zap, path: '/backtest' },
    { name: 'Analytics', icon: BarChart3, path: '/analytics' },
    { name: 'AI Engine', icon: Bot, path: '/ai' },
    { name: 'Risk Settings', icon: ShieldCheck, path: '/risk' },
    { name: 'Integrations', icon: Zap, path: '/integrations' },
    { name: 'Settings', icon: Settings, path: '/settings' },
  ]

  return (
    <div className="w-64 h-screen bg-[#0a0e14] border-r border-[#1e293b] flex flex-col fixed left-0 top-0 z-50">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center">
            <Zap className="text-[#022c22] w-6 h-6 fill-current" />
          </div>
          <span className="text-xl font-bold tracking-tight gradient-text">NIFTY SNIPER</span>
        </div>

        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path
            return (
              <Link 
                key={item.name} 
                href={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                  isActive 
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-400' : 'group-hover:text-slate-200'}`} />
                <span className="font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="mt-auto p-6">
        <div className="p-4 bg-slate-900/50 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Engine Active</span>
          </div>
          <p className="text-xs text-slate-500">Scanning Indian Indices (NIFTY, BANKNIFTY) strictly 9:15-3:30 IST.</p>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
