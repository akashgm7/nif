"use client"
// v1.0.1

import React, { useState, useEffect } from 'react'
import { 
  Search, 
  TrendingUp, 
  TrendingDown, 
  Zap, 
  Activity,
  ArrowUpRight,
  Filter,
  RefreshCw
} from 'lucide-react'

export default function ScannerPage() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://quant-2.onrender.com/api/v1';
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'wss://quant-2.onrender.com/ws';

  useEffect(() => {
    // 1. Initial Fetch
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_URL}/scanner`)
        if (!res.ok) throw new Error(`HTTP Error: ${res.status}`)
        const json = await res.json()
        setData(json)
        setError(null)
      } catch (err: any) {
        console.error("Scanner Fetch Error:", err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    // 2. Live WebSocket Updates
    console.log("Connecting to WebSocket:", WS_URL)
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connect = () => {
      socket = new WebSocket(WS_URL)

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'scanner_update') {
            setData(message.data)
            setLoading(false)
          }
        } catch (err) {
          console.error("WS Parse Error:", err)
        }
      }

      socket.onerror = (err) => {
          console.error("WS Connection Error for URL:", WS_URL, err)
      }

      socket.onclose = () => {
          console.log("WS Connection Closed. Reconnecting in 5s...")
          reconnectTimeout = setTimeout(connect, 5000)
      }
    }

    connect()

    return () => {
      if (socket) socket.close()
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
    }
  }, [API_URL, WS_URL])

  return (
    <div className="max-w-7xl mx-auto space-y-8 pl-64">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Search className="w-8 h-8 text-emerald-500" />
            Market Scanner
          </h1>
          <p className="text-slate-400">Real-time technical bias across all monitored indices.</p>
        </div>
        <div className="flex items-center gap-3">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 px-4 py-2 rounded-xl flex items-center gap-2">
                <Activity className="w-4 h-4 text-rose-500" />
                <span className="text-xs font-bold text-rose-500 uppercase">Offline: {error}</span>
            </div>
          )}
          <div className="bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-xl flex items-center gap-2">
             <RefreshCw className="w-4 h-4 text-emerald-500 animate-spin" />
             <span className="text-xs font-bold text-emerald-500 uppercase">Live Updating</span>
          </div>
        </div>
      </div>

      <div className="glass-card rounded-2xl overflow-hidden border border-slate-800/50">
        <table className="w-full text-left">
          <thead className="bg-slate-900/80 border-b border-slate-800">
            <tr>
              <th className="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 tracking-widest">Index</th>
              <th className="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 tracking-widest">Current Price</th>
              <th className="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 tracking-widest">Market Bias</th>
              <th className="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 tracking-widest">Volatility</th>
              <th className="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 tracking-widest text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {data.length === 0 && loading ? (
              [1, 2, 3, 4, 5].map(i => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={5} className="px-6 py-4 bg-slate-900/20 h-16"></td>
                </tr>
              ))
            ) : (
              data.map((item) => (
                <tr key={item.symbol} className="hover:bg-slate-800/30 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center font-bold text-xs">
                        {item.symbol[0]}
                      </div>
                      <span className="font-bold text-white">{item.symbol}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono text-slate-300">
                        {item.price > 0 ? `₹${item.price.toLocaleString()}` : 'FETCHING...'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border uppercase tracking-wider ${
                      item.bias === 'BULLISH' 
                        ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' 
                        : item.bias === 'BEARISH'
                        ? 'bg-rose-500/10 text-rose-500 border-rose-500/20'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}>
                      {item.bias}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Activity className={`w-4 h-4 ${item.volatility === 'High' ? 'text-amber-500' : 'text-slate-500'}`} />
                      <span className="text-sm text-slate-300">{item.volatility}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="p-2 text-slate-500 hover:text-emerald-500 transition-colors">
                      <ArrowUpRight className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
