"use client"

import React, { useState, useEffect } from 'react'
import { Newspaper, Globe, Anchor, ArrowUpRight, TrendingUp, AlertCircle } from 'lucide-react'

const MarketIntel = () => {
  const [news, setNews] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/external/news`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setNews(data.slice(0, 5))
        } else {
          setNews([])
        }
      })
      .catch(() => setNews([]))

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/external/institutional`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setAlerts(data)
        } else {
          setAlerts([])
        }
      })
      .catch(() => setAlerts([]))
  }, [])

  return (
    <div className="space-y-8">
      {/* On-chain Alerts */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
          <Anchor className="w-4 h-4" /> Institutional Intel
        </h3>
        <div className="space-y-3">
          {alerts.map((alert, i) => (
            <div key={i} className="p-4 bg-slate-900/50 rounded-2xl border border-slate-800/50 hover:border-blue-500/30 transition-all">
              <div className="flex justify-between items-start mb-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  alert.impact === 'BULLISH' ? 'bg-emerald-500/10 text-emerald-500' : 
                  alert.impact === 'BEARISH' ? 'bg-rose-500/10 text-rose-500' : 'bg-slate-800 text-slate-400'
                }`}>
                  {alert.impact}
                </span>
                <span className="text-[10px] text-slate-600 font-bold">{alert.time}</span>
              </div>
              <p className="text-xs text-slate-300 font-medium leading-relaxed">{alert.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Hot News */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
          <Newspaper className="w-4 h-4" /> Market Sentiment
        </h3>
        <div className="space-y-4">
          {news.map((item, i) => (
            <div key={i} className="group cursor-pointer">
              <div className="flex items-start gap-3">
                <div className="w-1 h-1 rounded-full bg-blue-500 mt-2 group-hover:scale-150 transition-transform"></div>
                <div className="space-y-1">
                   <h4 className="text-xs font-bold text-slate-200 group-hover:text-blue-400 transition-colors leading-tight">
                     {item.title || item.domain}
                   </h4>
                   <div className="flex items-center gap-2">
                     <span className="text-[10px] text-slate-600 font-bold uppercase">{item.source || 'CryptoPanic'}</span>
                     <span className={`text-[10px] font-bold ${
                       item.sentiment === 'Bullish' ? 'text-emerald-500' : 
                       item.sentiment === 'Bearish' ? 'text-rose-500' : 'text-slate-500'
                     }`}>
                       {item.sentiment}
                     </span>
                   </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Global Macro Placeholder */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-500/20">
         <div className="flex items-center gap-2 mb-4">
           <Globe className="w-4 h-4 text-blue-400" />
           <span className="text-xs font-bold text-white uppercase tracking-tight">Macro Watch</span>
         </div>
         <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">DXY Index</span>
            <div className="flex items-center gap-1 text-emerald-500 font-bold text-xs">
              <TrendingUp className="w-3 h-3" />
              104.2
            </div>
         </div>
      </div>
    </div>
  )
}

export default MarketIntel
