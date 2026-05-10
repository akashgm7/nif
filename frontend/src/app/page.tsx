"use client"

import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Clock, 
  ArrowUpRight, 
  Zap,
  CheckCircle2,
  AlertCircle
} from 'lucide-react'
import { useState, useEffect } from 'react'
import MarketIntel from '@/components/MarketIntel'
import SignalChart from '@/components/SignalChart'

export default function Dashboard() {
  const [signals, setSignals] = useState<any[]>([])
  const [engineStatus, setEngineStatus] = useState('Stable')

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://quant-2.onrender.com/api/v1';
    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'wss://quant-2.onrender.com/ws';

    // Fetch initial signals
    fetch(`${API_URL}/signals`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setSignals(data)
        } else {
          setSignals([])
        }
      })
      .catch(() => setSignals([]))

    // Connect to WebSocket
    let ws: WebSocket | null = null;
    
    const connectWS = () => {
        ws = new WebSocket(`${WS_URL}`)
        
        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            if (message.type === 'new_signal') {
              setSignals(prev => [message.data, ...prev])
            }
          } catch (e) {}
        }

        ws.onopen = () => setEngineStatus('Stable')
        ws.onclose = () => {
            setEngineStatus('Disconnected')
            // Attempt reconnect after 5s
            setTimeout(connectWS, 5000)
        }
        ws.onerror = () => ws?.close()
    }

    connectWS()

    return () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close()
        }
    }
  }, [])

  const stats = [
    { name: 'Active Signals', value: signals.length.toString(), change: '+2', icon: Activity, color: 'text-emerald-500' },
    { name: '24h Win Rate', value: '78.4%', change: '+5.2%', icon: TrendingUp, color: 'text-blue-500' },
    { name: 'Total Profit', value: '+12.4%', change: '+1.1%', icon: Zap, color: 'text-amber-500' },
    { name: 'Avg. Confidence', value: '84%', change: '-2%', icon: CheckCircle2, color: 'text-purple-500' },
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-8 pl-64">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Institutional Dashboard</h1>
          <p className="text-slate-400">Real-time market scanning and signal intelligence.</p>
        </div>
        <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 p-1.5 rounded-xl">
          <button className="px-4 py-2 bg-slate-800 text-white rounded-lg text-sm font-semibold">15m</button>
          <button className="px-4 py-2 text-slate-500 hover:text-slate-300 rounded-lg text-sm font-semibold">1H</button>
          <button className="px-4 py-2 text-slate-500 hover:text-slate-300 rounded-lg text-sm font-semibold">4H</button>
          <button className="px-4 py-2 text-slate-500 hover:text-slate-300 rounded-lg text-sm font-semibold">1D</button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="glass-card p-6 rounded-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <stat.icon className={`w-16 h-16 ${stat.color}`} />
            </div>
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-2 rounded-lg bg-slate-900 border border-slate-800 ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium text-slate-400">{stat.name}</span>
            </div>
            <div className="flex items-baseline gap-3">
              <h3 className="text-2xl font-bold text-white">{stat.value}</h3>
              <span className={`text-xs font-bold ${stat.change.startsWith('+') ? 'text-emerald-500' : 'text-rose-500'}`}>
                {stat.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Signals Feed */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-500" />
              Live Trading Signals
            </h2>
            <button className="text-sm text-emerald-500 hover:text-emerald-400 font-semibold flex items-center gap-1">
              View All <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4">
            {signals.map((signal, i) => (
              <div key={i} className="glass-card p-6 rounded-2xl border border-slate-800/50 hover:border-emerald-500/30 transition-all duration-300">
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center font-bold text-lg">
                      {signal.symbol?.[0]}
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-white">{signal.symbol}</h4>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                          signal.direction === 'LONG' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
                        }`}>
                          {signal.direction}
                        </span>
                        <span className="text-[10px] text-slate-500 flex items-center gap-1 uppercase font-bold tracking-wider">
                          <Clock className="w-3 h-3" /> {signal.timestamp ? new Date(signal.timestamp).toLocaleTimeString() : 'Just now'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">{signal.confidence}%</div>
                    <div className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-1">Confidence Score</div>
                  </div>
                </div>

                <div className="mb-6 bg-slate-900/30 rounded-2xl border border-slate-800/50 p-2">
                   <SignalChart 
                      symbol={signal.symbol} 
                      entry={signal.entry} 
                      sl={signal.stop_loss} 
                      tp={signal.take_profit_1} 
                   />
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Entry Price</p>
                    <p className="text-sm font-mono text-white">{signal.entry?.toLocaleString()}</p>
                  </div>
                  <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Stop Loss</p>
                    <p className="text-sm font-mono text-rose-500">{signal.stop_loss?.toLocaleString()}</p>
                  </div>
                  <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Take Profit</p>
                    <p className="text-sm font-mono text-emerald-500">{signal.take_profit_1?.toLocaleString()}</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {signal.reasons.map((reason: string, j: number) => (
                    <span key={j} className="text-[10px] font-bold text-slate-400 bg-slate-800/50 px-2.5 py-1 rounded-lg border border-slate-700/50 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                      {reason}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Side Info */}
        <div className="space-y-6">
          <MarketIntel />
        </div>
      </div>
    </div>
  )
}
